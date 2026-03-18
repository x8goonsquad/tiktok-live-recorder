# src/utils/custom_exceptions.py

class TikTokRecorderError(Exception):
    """Basexception för alla fel i recordern."""
    pass


class ArgsParseError(TikTokRecorderError):
    """Fel vid parsning av kommandoradsargument."""
    pass


class LiveNotFound(TikTokRecorderError):
    """Live-ström kunde inte hittas eller room_id ogiltig."""
    pass


class UserLiveError(TikTokRecorderError):
    """Användaren är inte live när vi förväntade oss det."""
    pass