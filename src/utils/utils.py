# src/utils/utils.py
# (Fullständig fil – ny banner exakt som du ville)

import json
import os

from utils.enums import Info


def banner() -> None:
    """
    Prints the EXACT new startup UI you requested (New and improved - TikTok Lives Sweden).
    """
    print("""
  _____ _ _   _____    _     _    _           ___                   _
 |_   _(_) |_|_   _|__| |__ | |  (_)_ _____  | _ \___ __ ___ _ _ __| |___ _ _
   | | | | / / | |/ _ \ / / | |__| \ V / -_) |   / -_) _/ _ \ '_/ _` / -_) '_|
   |_| |_|_\_\ |_|\___/_\_\ |____|_|\_/\___| |_|_\___\__\___/_| \__,_\___|_|
   New and improved - TikTok Lives Sweden""", flush=True)


def read_cookies():
    """
    Loads the config file and returns it.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "cookies.json")
    with open(config_path, "r") as f:
        return json.load(f)


def read_telegram_config():
    """
    Loads the telegram config file and returns it.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "telegram.json")
    with open(config_path, "r") as f:
        return json.load(f)


def is_termux() -> bool:
    """
    Checks if the script is running in Termux.

    Returns:
        bool: True if running in Termux, False otherwise.
    """
    import distro
    import platform

    return platform.system().lower() == "linux" and distro.like() == ""


def is_windows() -> bool:
    """
    Checks if the script is running on Windows.

    Returns:
        bool: True if running on Windows, False otherwise.
    """
    import platform

    return platform.system().lower() == "windows"


def is_linux() -> bool:
    """
    Checks if the script is running on Linux.

    Returns:
        bool: True if running on Linux, False otherwise.
    """
    import platform

    return platform.system().lower() == "linux"