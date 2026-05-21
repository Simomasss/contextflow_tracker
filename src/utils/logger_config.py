import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.utils.paths import get_app_data_dir

def setup_logging():
    app_data_dir = get_app_data_dir()
    os.makedirs(app_data_dir, exist_ok=True)
    
    log_path = os.path.join(app_data_dir, "contextflow.log")

    # Formát logu: Čas - Úroveň - Zpráva
    log_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 1. Handler pro zápis do souboru (max 5 MB, necháváme 1 zálohu)
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=1, encoding='utf-8')
    file_handler.setFormatter(log_format)

    # 2. Handler pro výstup do konzole
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)

    # Nastavení kořenového loggeru
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("--- Logování inicializováno ---")
    logging.info(f"Log soubor: {log_path}")