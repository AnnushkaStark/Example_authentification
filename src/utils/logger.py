import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",  # noqa
    level="INFO",
    enqueue=True,
)

logger.add(
    "logs/app.log", rotation="500 MB", retention="10 days", compression="zip"
)
