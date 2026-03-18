# utils/logger_manager.py

import logging

logger = logging.getLogger("TikTokLiveRecorder")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - [%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)