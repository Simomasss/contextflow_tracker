import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Určení složky (stejně jako u settings.json)
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    log_path = os.path.join(base_dir, "contextflow.log")

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