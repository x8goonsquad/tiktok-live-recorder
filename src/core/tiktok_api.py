# src/core/tiktok_api.py
import json
import re
import time
import requests
from urllib.parse import urlparse, parse_qs

from utils.logger_manager import logger
from utils.custom_exceptions import TikTokRecorderError, LiveNotFound, UserLiveError
from utils.enums import TikTokError   # <-- lägg till detta i din enums.py om det saknas (se nedan)


class TikTokAPI:
    def __init__(self, proxy=None, cookies=None):
        self.session = requests.Session()
        self.proxy = proxy
        self.cookies = cookies or {}

        if self.proxy:
            proxies = {"http": self.proxy, "https": self.proxy}
            self.session.proxies.update(proxies)

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.tiktok.com/",
            "sec-ch-ua": '"Chromium";v="136", "Not;A=Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        })

        if self.cookies:
            self.session.cookies.update(self.cookies)

    def _make_request(self, url, params=None, timeout=15):
        for attempt in range(3):
            try:
                r = self.session.get(url, params=params, timeout=timeout)
                r.raise_for_status()
                return r.json() if "application/json" in r.headers.get("content-type", "") else r.text
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)

    # ====================== EXAKT samma live-detection som originalet ======================
    def is_room_alive(self, room_id: str) -> bool:
        """Original check_alive-endpoint (detta är anledningen till att det nu funkar)"""
        if not room_id:
            raise UserLiveError(TikTokError.USER_NOT_CURRENTLY_LIVE)

        data = self._make_request(
            "https://webcast.tiktok.com/webcast/room/check_alive/",
            params={
                "aid": "1988",
                "region": "CH",
                "room_ids": room_id,
                "user_is_login": "true"
            }
        )

        if "data" not in data or len(data["data"]) == 0:
            return False
        return data["data"][0].get("alive", False)

    def get_room_id_from_user(self, user: str) -> str | None:
        """Original tikrec.com signed URL (bypassar WAF och ger rätt room_id när användaren är live)"""
        user = user.lstrip("@")
        try:
            # Hämta signed URL
            sign_resp = self.session.get(f"https://tikrec.com/tiktok/room/api/sign", params={"unique_id": user})
            signed_path = sign_resp.json().get("signed_path")
            if not signed_path:
                raise UserLiveError(TikTokError.WAF_BLOCKED)

            signed_url = f"https://www.tiktok.com{signed_path}"
            resp = self.session.get(signed_url)
            data = resp.json()

            room_id = (data.get("data") or {}).get("user", {}).get("roomId")
            if not room_id:
                raise UserLiveError(TikTokError.USER_NOT_CURRENTLY_LIVE)
            return room_id
        except Exception as e:
            logger.debug(f"Room ID error for @{user}: {e}")
            raise UserLiveError(TikTokError.USER_NOT_CURRENTLY_LIVE)

    def get_live_url(self, room_id: str) -> str:
        """Original get_live_url (nya SDK + FLV fallback)"""
        data = self._make_request(
            "https://webcast.tiktok.com/webcast/room/info/",
            params={"aid": "1988", "room_id": room_id}
        )

        stream_url = data.get("data", {}).get("stream_url", {})

        # Ny SDK-struktur (2025–2026)
        sdk_data_str = stream_url.get("live_core_sdk_data", {}).get("pull_data", {}).get("stream_data")
        if sdk_data_str:
            sdk_data = json.loads(sdk_data_str).get("data", {})
            qualities = stream_url.get("live_core_sdk_data", {}).get("pull_data", {}).get("options", {}).get("qualities", [])
            level_map = {q["sdk_key"]: q["level"] for q in qualities}

            best_flv = None
            best_level = -1
            for sdk_key, entry in sdk_data.items():
                level = level_map.get(sdk_key, -1)
                flv = entry.get("main", {}).get("flv")
                if level > best_level and flv:
                    best_level = level
                    best_flv = flv
            if best_flv:
                return best_flv

        # Legacy fallback
        flv_urls = stream_url.get("flv_pull_url", {})
        for quality in ["FULL_HD1", "HD1", "SD2", "SD1"]:
            if flv_urls.get(quality):
                return flv_urls[quality]

        raise LiveNotFound(TikTokError.RETRIEVE_LIVE_URL)

    # Resten av metoderna (get_user_from_room_id, get_room_and_user_from_url, etc.) kan du behålla från min tidigare version eller lägga till vid behov
    # (de används inte i automatic mode för en enskild user)

    def is_country_blacklisted(self):
        return False  # kan utökas vid behov