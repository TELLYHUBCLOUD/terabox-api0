import sys
from loguru import logger
from app.core.config import settings


def setup_logger():
    logger.remove()  # default handler hata do

    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # File handler
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="INFO",
        format="{time} | {level} | {name}:{line} | {message}",
    )

    return logger


log = setup_logger()
