import logging
import os
import sys
import winreg
import subprocess
import shutil
from datetime import datetime

from src.utils.paths import get_app_data_dir

def run_contextflow_uninstaller():
    """Provede odinstalaci aplikace a zálohuje data."""
    exe_path = ""
    is_exe = False
    
    # 1. Odstranění z registrů (Startup)
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "ContextFlow")
        winreg.CloseKey(key)
        logging.info("✓ Registr vyčištěn.")
    except (FileNotFoundError, OSError):
        pass 

    # 2. Určení cest
    if getattr(sys, 'frozen', False):
        # Režim EXE
        exe_path = sys.executable
        is_exe = True

    app_data_dir = get_app_data_dir()
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    backup_folder_name = f"ContextFlow_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = os.path.join(downloads_folder, backup_folder_name)

    # 3. Záloha DB a Logů
    try:
        os.makedirs(backup_path, exist_ok=True)
        
        db_file = os.path.join(app_data_dir, "contextflow.db")
        log_file = os.path.join(app_data_dir, "contextflow.log")
        
        if os.path.exists(db_file):
            shutil.copy2(db_file, backup_path)
            logging.info("✓ Databáze zálohována do Stažených souborů.")
            
        if os.path.exists(log_file):
            shutil.copy2(log_file, backup_path)
            logging.info("✓ Logy zálohovány do Stažených souborů.")
            
    except Exception as e:
        logging.info(f"Nepodařilo se vytvořit zálohu: {e}")

    logging.info("Odinstalace dokončena. Spouštím self-destruct sekvenci a aplikaci ukončuji.")

    # Uzavřeme logování, abychom uvolnili soubor contextflow.log a mohli smazat složku
    logging.shutdown()

    # 4. Smazání AppData složky a samotného EXE (v CMD na pozadí, abychom to mohli smazat po ukončení)
    if os.path.exists(app_data_dir):
        # rmdir /s /q smaže složku včetně všech souborů (i EXE, pokud tam je a už nebeží)
        cmd_parts = ["timeout /t 3 > nul", f'rmdir /s /q "{app_data_dir}"']
        
        if is_exe and exe_path and not os.path.normcase(exe_path).startswith(os.path.normcase(app_data_dir)):
            cmd_parts.append(f'del /f /q "{exe_path}"')
            
        cmd = " && ".join(cmd_parts)
        
        # Pokud by CMD běželo z AppData, Windows by smazal obsah, ale nepovolil by smazat samotnou složku ContextFlow.
        safe_cwd = os.path.expanduser("~")
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW, cwd=safe_cwd)

    os._exit(0)