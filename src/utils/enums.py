from enum import Enum, IntEnum


class Regex(Enum):
    def __str__(self):
        return str(self.value)

    IS_TIKTOK_LIVE = r".*www\.tiktok\.com.*|.*vm\.tiktok\.com.*"


class TimeOut(IntEnum):
    """
    Enumeration that defines timeout values.
    """
    def __mul__(self, operator):
        return self.value * operator

    ONE_MINUTE = 60
    AUTOMATIC_MODE = 5
    CONNECTION_CLOSED = 2


class StatusCode(IntEnum):
    OK = 200
    REDIRECT = 302
    MOVED = 301


class Mode(IntEnum):
    """
    Enumeration that represents the recording modes.
    """
    MANUAL = 0
    AUTOMATIC = 1
    FOLLOWERS = 2


class Error(Enum):
    """
    Enumeration that contains possible errors while using TikTok-Live-Recorder.
    """
    def __str__(self):
        return str(self.value)

    CONNECTION_CLOSED = "Connection broken by the server."
    CONNECTION_CLOSED_AUTOMATIC = f"{CONNECTION_CLOSED}. Try again after delay of {TimeOut.CONNECTION_CLOSED} minutes"


class TikTokError(Enum):
    """
    Enumeration that contains possible errors of TikTok
    """
    def __str__(self):
        return str(self.value)

    COUNTRY_BLACKLISTED = (
        "Captcha required or country blocked. "
        "Use a VPN, room_id, or authenticate with cookies.\n"
        "How to set cookies: https://github.com/Michele0303/tiktok-live-recorder/blob/main/docs/GUIDE.md#how-to-set-cookies\n"
        "How to get room_id: https://github.com/Michele0303/TikTok-Live-Recorder/blob/main/docs/GUIDE.md#how-to-get-room_id\n"
    )
    COUNTRY_BLACKLISTED_AUTO_MODE = (
        "Automatic mode is available only in unblocked countries. "
        "Use a VPN or authenticate with cookies.\n"
        "How to set cookies: https://github.com/Michele0303/tiktok-live-recorder/blob/main/docs/GUIDE.md#how-to-set-cookies\n"
    )
    COUNTRY_BLACKLISTED_FOLLOWERS_MODE = (
        "Followers mode is available only in unblocked countries. "
        "Use a VPN or authenticate with cookies.\n"
        "How to set cookies: https://github.com/Michele0303/tiktok-live-recorder/blob/main/docs/GUIDE.md#how-to-set-cookies\n"
    )
    ACCOUNT_PRIVATE = (
        "Account is private, login required. "
        "Please add your cookies to cookies.json "
        "https://github.com/Michele0303/tiktok-live-recorder/blob/main/docs/GUIDE.md#how-to-set-cookies"
    )
    ACCOUNT_PRIVATE_FOLLOW = (
        "This account is private. Follow the creator to access their LIVE."
    )
    LIVE_RESTRICTION = (
        "Live is private, login required. "
        "Please add your cookies to cookies.json"
        "https://github.com/Michele0303/tiktok-live-recorder/blob/main/docs/GUIDE.md#how-to-set-cookies"
    )
    USERNAME_ERROR = "Username / RoomID not found or the user has never been in live."
    ROOM_ID_ERROR = "Error extracting RoomID"
    USER_NEVER_BEEN_LIVE = "The user has never hosted a live stream on TikTok."
    USER_NOT_CURRENTLY_LIVE = "The user is not hosting a live stream at the moment."
    RETRIEVE_LIVE_URL = "Unable to retrieve live streaming url. Please try again later."
    INVALID_TIKTOK_LIVE_URL = "The provided URL is not a valid TikTok live stream."
    WAF_BLOCKED = "Your IP is blocked by TikTok WAF. Please change your IP address."
    # Nya tillägg 2025–2026 (vanliga från issues)
    CAPTCHA_CHALLENGE = "TikTok presented a captcha challenge. Use better cookies, proxy or VPN."
    RATE_LIMITED = "Rate limited by TikTok API. Wait a few minutes or use proxy."
    STREAM_ENDED_UNEXPECTEDLY = "Live stream ended unexpectedly during recording."


class Info(Enum):
    """
    Enumeration that defines the version number and the banner message.
    """
    def __str__(self):
        return str(self.value)

    def __iter__(self):
        return iter(self.value)

    NEW_FEATURES = [
        "Replaced pyrogram to telethon library.",
        "Fixed termux dependencies error.",
        "Minor.",
        "Added automatic TS-segmentation on bitrate/resolution change",
        "Silent ffmpeg operations and correct TS → MP4 merge with concat demuxer",
        "Automatic mode as default (-mode no longer required)",
        "Skipped update check by default",
        "Custom 'New and improved - TikTok Lives Sweden' banner",
    ]

    VERSION = "7.6"  # ← str – undviker float-problemet helt

    BANNER = rf"""
  _____ _ _ _____ _ _ _ ___ _
 |_ _(_) |_|_ _|__| |__ | | (_)_ _____ | _ \___ __ ___ _ _ __| |___ _ _
   | | | | / / | |/ _ \ / / | |__| \ V / -_) | / -_) _/ _ \ '_/ _` / -_) '_|
   |_| |_|_\_\ |_|\___/_\_\ |____|_|\_/\___| |_|_\___\__\___/_| \__,_\___|_|
   New and improved - TikTok Lives Sweden
   V{VERSION}
"""


# ────────────────────────────────────────────────
# NYA ENUMS TILLAGDA FÖR DINA MODIFIERINGAR
# ────────────────────────────────────────────────

class QualityChange(Enum):
    """
    Typer av förändringar som triggar ny TS-segment.
    Används i loggning och monitor-tråden.
    """
    RESOLUTION = "upplösning"
    BITRATE = "bitrate"
    BOTH = "upplösning och bitrate"

    def __str__(self):
        return self.value


class RecordingSegment(Enum):
    """
    Status för varje TS-segment (kan användas i framtida utökningar).
    """
    STARTING = "startar"
    ACTIVE = "aktiv"
    ENDED = "avslutad"
    MERGING = "mergas till MP4"
    FAILED = "misslyckades"


class FFmpegOption(str, Enum):
    """
    Vanliga ffmpeg-flaggor som strängar (gör koden renare och lättare att ändra).
    """
    RECONNECT = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    COPY_CODECS = "-c copy"
    SEGMENT_FORMAT = "-f segment -segment_format mpegts"
    QUIET = "-loglevel quiet -nostats -nostdin"
    OVERWRITE = "-y"
    HLS = "-f hls"  # om du någonsin byter till HLS istället för TS