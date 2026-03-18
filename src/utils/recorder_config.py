# src/utils/recorder_config.py
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RecorderConfig:
    url: Optional[str] = None
    user: Optional[str] = None          # str eller list[str] i multi-user-läge
    room_id: Optional[str] = None
    mode: Any = None                     # Mode enum från utils.enums
    automatic_interval: int = 5
    cookies: Dict[str, Any] = None
    proxy: Optional[str] = None
    output: Optional[str] = None
    duration: Optional[int] = None
    use_telegram: bool = False
    bitrate: Optional[str] = None        # t.ex. "1000k" eller "1M"

    def __post_init__(self):
        if self.cookies is None:
            self.cookies = {}