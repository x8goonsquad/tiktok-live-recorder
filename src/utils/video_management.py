# src/utils/video_management.py
# (Fullständig ny fil – TS → MP4 merge KORREKT + helt tyst ffmpeg)

import os
import time
from pathlib import Path

import ffmpeg

from utils.logger_manager import logger


class VideoManagement:
    @staticmethod
    def wait_for_file_release(file, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with open(file, "ab"):
                    return True
            except PermissionError:
                time.sleep(0.5)
        return False

    @staticmethod
    def merge_ts_to_mp4(segments_dir: Path, final_mp4: Path):
        """TS-segment → korrekt MP4-merge (concat + c copy, ingen re-encoding) + HELT TYST ffmpeg"""
        logger.info(f"Merging TS segments to MP4: {final_mp4.name}")

        segment_list = sorted(segments_dir.glob("*.ts"))
        if not segment_list:
            logger.error("Inga TS-segment hittades!")
            return

        concat_file = segments_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for ts in segment_list:
                f.write(f"file '{ts.absolute()}'\n")

        try:
            (
                ffmpeg
                .input(str(concat_file), format="concat", safe=0)
                .output(str(final_mp4), c="copy", y="-y")
                .run(quiet=True, overwrite_output=True)   # Tyst + ingen output alls
            )
            logger.info(f"MP4 klar: {final_mp4.resolve()}")
        except ffmpeg.Error as e:
            logger.error(f"ffmpeg merge misslyckades: {e}")
            return

        # Städa upp
        for ts in segment_list:
            ts.unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)
        if segments_dir.exists() and not any(segments_dir.iterdir()):
            segments_dir.rmdir()