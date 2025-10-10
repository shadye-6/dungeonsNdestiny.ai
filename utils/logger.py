import logging
from utils.config import LOG_LEVEL

def setup_logger(name="AI_DungeonMaster"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, LOG_LEVEL))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

