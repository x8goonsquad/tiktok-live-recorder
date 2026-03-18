# src/core/tiktok_recorder.py
import time
import subprocess
import threading
import json
from http.client import HTTPException
from pathlib import Path
import sys
import signal

from requests import RequestException

from core.tiktok_api import TikTokAPI
from utils.logger_manager import logger
from utils.recorder_config import RecorderConfig
from utils.video_management import VideoManagement
from utils.custom_exceptions import LiveNotFound, UserLiveError, TikTokRecorderError
from utils.enums import Mode, Error, TimeOut, TikTokError


class TikTokRecorder:
    def __init__(self, config: RecorderConfig):
        self.tiktok = TikTokAPI(proxy=config.proxy, cookies=config.cookies)

        self.url = config.url
        self.user = config.user
        self.room_id = config.room_id
        self.mode = config.mode
        self.automatic_interval = config.automatic_interval
        self.cookies = config.cookies
        self.proxy = config.proxy
        self.output = config.output
        self.duration = config.duration
        self.use_telegram = config.use_telegram
        self.bitrate = config.bitrate

        self._should_exit = threading.Event()

    def _setup(self):
        self.check_country_blacklisted()

        if self.mode == Mode.FOLLOWERS:
            self.sec_uid = self.tiktok.get_sec_uid()
            if self.sec_uid is None:
                raise TikTokRecorderError("Failed to retrieve sec_uid.")
            logger.info("Followers mode activated\n")
        else:
            if self.url:
                self.user, self.room_id = self.tiktok.get_room_and_user_from_url(self.url)

            if not self.user:
                self.user = self.tiktok.get_user_from_room_id(self.room_id)

            if not self.room_id:
                self.room_id = self.tiktok.get_room_id_from_user(self.user)

            logger.info(f"USERNAME: {self.user}" + ("\n" if not self.room_id else ""))
            if self.room_id:
                logger.info(
                    f"ROOM_ID:  {self.room_id}"
                    + ("\n" if not self.tiktok.is_room_alive(self.room_id) else "")
                )

        if self.proxy:
            self.tiktok = TikTokAPI(proxy=None, cookies=self.cookies)

    def run(self):
        self._setup()

        def _handle_shutdown(sig, frame):
            logger.info("\nCtrl+C mottagen – avslutar inspelning, merger och stänger programmet...")
            self._should_exit.set()
            time.sleep(1.5)
            sys.exit(0)

        signal.signal(signal.SIGINT, _handle_shutdown)
        signal.signal(signal.SIGTERM, _handle_shutdown)

        if self.mode == Mode.MANUAL:
            self.manual_mode()
        elif self.mode == Mode.AUTOMATIC:
            self.automatic_mode()
        elif self.mode == Mode.FOLLOWERS:
            self.followers_mode()

    def manual_mode(self):
        if not self.tiktok.is_room_alive(self.room_id):
            raise UserLiveError(f"@{self.user}: {TikTokError.USER_NOT_CURRENTLY_LIVE}")

        self.start_recording(self.user, self.room_id)

    def automatic_mode(self):
        while not self._should_exit.is_set():
            try:
                if self._should_exit.is_set():
                    break
                self.room_id = self.tiktok.get_room_id_from_user(self.user)
                self.manual_mode()
            except (UserLiveError, LiveNotFound) as ex:
                logger.info(ex)
                if self._should_exit.is_set():
                    break
                logger.info(f"Waiting {self.automatic_interval} minutes before recheck\n")
                slept = 0
                while slept < self.automatic_interval * 60 and not self._should_exit.is_set():
                    time.sleep(1)
                    slept += 1
            except ConnectionError:
                logger.error(Error.CONNECTION_CLOSED_AUTOMATIC)
                if self._should_exit.is_set():
                    break
                time.sleep(TimeOut.CONNECTION_CLOSED * TimeOut.ONE_MINUTE)
            except Exception as e:
                logger.error(f"Unexpected error in automatic loop: {e}", exc_info=True)
                if self._should_exit.is_set():
                    break
                time.sleep(10)

        logger.info("Automatic mode avslutad – ingen mer inspelning startas.")

    def followers_mode(self):
        logger.warning("Followers mode aktiverat – Ctrl+C hanteras delvis")
        while not self._should_exit.is_set():
            time.sleep(30)

    def _build_output_path(self, user: str):
        base_dir = Path("recordings") / user
        base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output folder: {user}")

        timestamp = time.strftime('%Y.%m.%d_%H-%M-%S', time.localtime())
        final_mp4 = base_dir / f"{user}_{timestamp}.mp4"

        segments_dir = base_dir / f"temp_{timestamp}"
        segments_dir.mkdir(exist_ok=True)

        return segments_dir, final_mp4

    def _monitor_quality(self, live_url: str, stop_event: threading.Event, restart_event: threading.Event):
        """NY SEGMENTERING: Kollar resolution + aspect_ratio + pix_fmt + color_space + color_transfer + color_primaries
           (bitrate och FPS har tagits bort helt)"""
        last_quality = None

        while not stop_event.is_set() and not self._should_exit.is_set():
            try:
                probe = subprocess.run(
                    [
                        "ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_format", "-show_streams", live_url
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                data = json.loads(probe.stdout)
                stream = data.get("streams", [{}])[0]

                # NYA FÄLT – exakt som du begärde
                current_quality = (
                    f"{stream.get('width')}x{stream.get('height')}",                    # resolution
                    stream.get("display_aspect_ratio") or "unknown",                    # aspect_ratio
                    stream.get("pix_fmt"),                                              # pix_fmt
                    stream.get("color_space"),                                          # color_space
                    stream.get("color_transfer"),                                       # color_transfer
                    stream.get("color_primaries"),                                      # color_primaries
                )

                if last_quality is None:
                    last_quality = current_quality
                elif current_quality != last_quality:
                    logger.info(
                        f"Quality changed (resolution/aspect/pix_fmt/color) → startar ny segment!"
                    )
                    restart_event.set()
                    last_quality = current_quality

            except Exception:
                pass  # tyst fel – fortsätt monitorera

            time.sleep(30)

    def start_recording(self, user, room_id):
        live_url = self.tiktok.get_live_url(room_id)
        if not live_url:
            raise LiveNotFound(TikTokError.RETRIEVE_LIVE_URL)

        segments_dir, final_mp4 = self._build_output_path(user)

        logger.info("Started recording...")
        logger.info("[PRESS CTRL + C ONCE TO STOP – programmet avslutas efter merge]")

        stop_event = threading.Event()
        restart_event = threading.Event()

        monitor_thread = threading.Thread(
            target=self._monitor_quality,
            args=(live_url, stop_event, restart_event),
            daemon=True
        )
        monitor_thread.start()

        segment_index = 0

        try:
            while not stop_event.is_set() and not self._should_exit.is_set():
                if not self.tiktok.is_room_alive(room_id):
                    logger.info("User is no longer live. Stopping this recording.")
                    break

                current_segment = segments_dir / f"segment_{segment_index:03d}.ts"

                cmd = [
                    "ffmpeg",
                    "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
                    "-i", live_url,
                    "-c", "copy",
                    "-f", "mpegts",
                    "-y",
                    str(current_segment)
                ]

                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                while proc.poll() is None and not stop_event.is_set() and not self._should_exit.is_set():
                    if restart_event.is_set():
                        proc.terminate()
                        proc.wait(timeout=5)
                        restart_event.clear()
                        segment_index += 1
                        break
                    time.sleep(0.5)

                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)

        except KeyboardInterrupt:
            logger.info("Ctrl+C i inspelningsloopen – avslutar denna inspelning...")
            stop_event.set()
        finally:
            stop_event.set()
            logger.info("Inspelning stoppad – merger TS-segment till MP4...")
            VideoManagement.merge_ts_to_mp4(segments_dir, final_mp4)
            logger.info(f"Recording finished and merged: {final_mp4.resolve()}\n")

            if self._should_exit.is_set():
                logger.info("Global exit-flagg satt – ingen ny inspelning startas.")

    def check_country_blacklisted(self):
        is_blacklisted = self.tiktok.is_country_blacklisted()
        if not is_blacklisted:
            return False

        if self.room_id is None:
            raise TikTokRecorderError(TikTokError.COUNTRY_BLACKLISTED)

        if self.mode == Mode.AUTOMATIC:
            raise TikTokRecorderError(TikTokError.COUNTRY_BLACKLISTED_AUTO_MODE)
        elif self.mode == Mode.FOLLOWERS:
            raise TikTokRecorderError(TikTokError.COUNTRY_BLACKLISTED_FOLLOWERS_MODE)

        return is_blacklisted