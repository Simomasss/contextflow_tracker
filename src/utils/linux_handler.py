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
        Instalace se na Linuxu neprovádí automaticky.
        """
        logging.info("Linux detekován - automatická instalace/přesun přeskočen.")
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
Exec="{app_path}"
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
