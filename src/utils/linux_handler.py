import os
import sys
import shutil
import tempfile
import subprocess
import logging
from datetime import datetime
from src.utils.paths import get_app_data_dir
from src.utils.platform_handler import BasePlatformHandler

class LinuxPlatformHandler(BasePlatformHandler):
    def handle_installation(self) -> bool:
        """
        Pokud je aplikace spuštěna jako binárka z náhodného místa,
        přesune se automaticky do AppData (~/.local/share/ContextFlow) a na původním místě zanechá symlink.
        """
        if not getattr(sys, 'frozen', False):
            return True

        current_exe = os.path.abspath(sys.executable)
        appdata_dir = get_app_data_dir()
        target_exe = os.path.join(appdata_dir, "ContextFlow")

        if os.path.normcase(current_exe) == os.path.normcase(target_exe):
            return True

        os.makedirs(appdata_dir, exist_ok=True)

        try:
            logging.info(f"Probíhá instalace binárky do: {target_exe}")
            shutil.copy2(current_exe, target_exe)
            
            # Ujistíme se, že má nová binárka správná práva pro spuštění (chmod +x)
            os.chmod(target_exe, 0o755)

            original_dir = os.path.dirname(current_exe)
            original_name = os.path.basename(current_exe)
            shortcut_path = os.path.join(original_dir, f"{original_name}_shortcut")

            # Vytvoření symbolického linku (standard na Linuxu)
            if not os.path.exists(shortcut_path):
                try:
                    os.symlink(target_exe, shortcut_path)
                except Exception as e:
                    logging.warning(f"Nelze vytvořit symlink: {e}")

            # Shell skript pro smazání staré binárky a spuštění nové
            bash_path = os.path.join(tempfile.gettempdir(), "cf_migrate.sh")
            with open(bash_path, "w", encoding="utf-8") as f:
                f.write("#!/bin/bash\n")
                f.write("sleep 2\n") # Počkat na ukončení starého procesu
                f.write(f'rm -f "{current_exe}"\n')
                # Spuštění cílové aplikace odděleně od bash skriptu pomocí nohup
                f.write(f'nohup "{target_exe}" > /dev/null 2>&1 &\n')
                f.write(f'rm -f "$0"\n') # Smazat sám sebe

            os.chmod(bash_path, 0o755)
            # Spustit bash skript na pozadí v nové relaci
            subprocess.Popen([bash_path], start_new_session=True)
            
            logging.info("Aplikace byla úspěšně přesunuta. Restartuji...")
            os._exit(0)

        except Exception as e:
            logging.error(f"Nepodařilo se přesunout aplikaci do AppData: {e}")
            return False
            
        return True

    def _get_autostart_path(self) -> str:
        # Standard XDG autostart pro Linux (funguje pro GNOME, KDE, XFCE, atd.)
        return os.path.expanduser("~/.config/autostart/contextflow_tracker.desktop")

    def setup_autostart(self) -> bool:
        """Přidá aktuální binárku do ~/.config/autostart pro start po zapnutí PC."""
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            desktop_path = self._get_autostart_path()
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[en_US]=ContextFlow Tracker
Name=ContextFlow Tracker
Comment=ContextFlow Background Tracker
Terminal=false
"""
            try:
                os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
                with open(desktop_path, "w", encoding="utf-8") as f:
                    f.write(desktop_content)
                # Nastavíme práva, některé desktopové prostředí to vyžadují
                os.chmod(desktop_path, 0o755)
                
                logging.info("✓ Aplikace přidána do po spuštění (XDG Autostart).")
                return True
            except Exception as e:
                logging.error(f"Nepodařilo se vytvořit autostart .desktop soubor: {e}")
                return False
        return True

    def remove_autostart(self) -> bool:
        desktop_path = self._get_autostart_path()
        try:
            if os.path.exists(desktop_path):
                os.remove(desktop_path)
            logging.info("✓ Autostart (.desktop) odstraněn.")
            return True
        except Exception as e:
            logging.error(f"Chyba při mazání autostartu: {e}")
            return False

    def uninstall(self, backup_diagnostics: bool = True) -> bool:
        """Provede odinstalaci aplikace a zálohuje data (Linux verze)."""
        self.remove_autostart()
        
        exe_path = ""
        is_exe = False
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            is_exe = True

        app_data_dir = get_app_data_dir()
        
        if backup_diagnostics:
            # Na linuxu často existuje složka ~/Downloads, alternativně standardní xdg-user-dir
            downloads_folder = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads_folder):
                downloads_folder = os.path.expanduser("~") # fallback
                
            backup_folder_name = f"ContextFlow_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(downloads_folder, backup_folder_name)

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
                logging.error(f"Nepodařilo se vytvořit zálohu: {e}")

        logging.info("Odinstalace dokončena. Spouštím self-destruct sekvenci a aplikaci ukončuji.")
        logging.shutdown()

        if os.path.exists(app_data_dir):
            # Pro Linux spustíme shell příkazy odděleně od Python procesu
            cmd_parts = ["sleep 3", f'rm -rf "{app_data_dir}"']
            if is_exe and exe_path and not os.path.normcase(exe_path).startswith(os.path.normcase(app_data_dir)):
                cmd_parts.append(f'rm -f "{exe_path}"')
                
            cmd = " ; ".join(cmd_parts)
            subprocess.Popen(['sh', '-c', cmd], start_new_session=True)

        os._exit(0)
        return True
