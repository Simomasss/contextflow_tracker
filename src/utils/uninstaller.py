import logging
import os
import sys
import winreg
import subprocess

def run_contextflow_uninstaller():
    """Provede odinstalaci aplikace (mimo databáze)."""
    
    # Inicializujeme proměnné na začátku, aby linter neprskal
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
        base_dir = os.path.dirname(sys.executable)
        exe_path = sys.executable
        is_exe = True
    else:
        # Režim vývoje (skript) - base_dir je root projektu
        # Jdeme o 2 úrovně výš z src/utils
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        is_exe = False

    json_path = os.path.join(base_dir, "settings.json")

    # 3. Smazání nastavení (JSON)
    if os.path.exists(json_path):
        try:
            os.remove(json_path)
            logging.info("✓ Soubor settings.json smazán.")
        except Exception as e:
            logging.info(f"Nepodařilo se smazat JSON: {e}")

    # 4. Smazání samotného EXE (jen pokud existuje cesta a jsme v EXE)
    if is_exe and exe_path:
        logging.info("! Spouštím self-destruct sekvenci pro EXE...")
        # Příkaz pro CMD: počká 2s a pak smaže soubor na dané cestě
        cmd = f'timeout /t 2 > nul && del /f /q "{exe_path}"'
        subprocess.Popen(cmd, shell=True)
    
    logging.info("Odinstalace dokončena. Aplikace se nyní ukončí.")
    os._exit(0)