import os
import logging
import logging.config
import configparser

def setup_logging_from_config(path: str = 'logging_config.ini') -> logging.Logger:
    config = configparser.ConfigParser()
    config.read(path)

    enabled: bool = config.getboolean('log_control', 'enabled', fallback=True)
    if enabled:
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
        logging.config.fileConfig(path)
    else:
        logging.disable(logging.CRITICAL)

    return logging.getLogger(__name__)

logger: logging.Logger = setup_logging_from_config()
