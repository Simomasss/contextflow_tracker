import os
import sys
import shutil
import tempfile
import subprocess
import logging
from datetime import datetime
from src.utils.paths import get_app_data_dir
from src.utils.platform_handler import BasePlatformHandler

class MacPlatformHandler(BasePlatformHandler):
    def handle_installation(self) -> bool:
        """
        Instalace se na Macu neprovádí automaticky (používá se spuštění přímo z .app bundle).
        """
        logging.info("macOS detekován - automatická instalace/přesun přeskočen.")
        return True

    def _get_plist_path(self) -> str:
        return os.path.expanduser("~/Library/LaunchAgents/com.contextflow.tracker.plist")

    def setup_autostart(self) -> bool:
        """Přidá aktuální binárku do LaunchAgents pro start po zapnutí Macu."""
        if getattr(sys, 'frozen', False):
            import html
            app_path = sys.executable
            escaped_app_path = html.escape(app_path)
            plist_path = self._get_plist_path()
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.contextflow.tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>{escaped_app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            try:
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                with open(plist_path, "w", encoding="utf-8") as f:
                    f.write(plist_content)
                logging.info("✓ Aplikace přidána do po spuštění (LaunchAgent).")
                return True
            except Exception as e:
                logging.error(f"Nepodařilo se vytvořit autostart plist: {e}")
                return False
        return True

    def remove_autostart(self) -> bool:
        plist_path = self._get_plist_path()
        try:
            if os.path.exists(plist_path):
                os.remove(plist_path)
            logging.info("✓ Autostart (LaunchAgent) odstraněn.")
            return True
        except Exception as e:
            logging.error(f"Chyba při mazání autostartu: {e}")
            return False

    def uninstall(self, backup_diagnostics: bool = True) -> bool:
        """Provede odinstalaci aplikace a zálohuje data (macOS verze)."""
        self.remove_autostart()
        
        exe_path = ""
        is_exe = False
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            is_exe = True

        app_data_dir = get_app_data_dir()
        
        if backup_diagnostics:
            downloads_folder = os.path.expanduser("~/Downloads")
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
                    logging.info("✓ Logy zálohovány do Stažených soubufů.")
                    
            except Exception as e:
                logging.error(f"Nepodařilo se vytvořit zálohu: {e}")

        logging.info("Odinstalace dokončena. Spouštím self-destruct sekvenci a aplikaci ukončuji.")
        logging.shutdown()

        if os.path.exists(app_data_dir):
            # Pro Mac použijeme bash příkazy, start_new_session zajistí, že běží i po ukončení aplikace
            cmd_parts = ["sleep 3", f'rm -rf "{app_data_dir}"']
            if is_exe and exe_path and not os.path.normcase(exe_path).startswith(os.path.normcase(app_data_dir)):
                if ".app/Contents/MacOS" in exe_path:
                    bundle_path = exe_path.split(".app/Contents/MacOS")[0] + ".app"
                    cmd_parts.append(f'rm -rf "{bundle_path}"')
                else:
                    cmd_parts.append(f'rm -f "{exe_path}"')
                
            cmd = " ; ".join(cmd_parts)
            subprocess.Popen(['sh', '-c', cmd], start_new_session=True)

        os._exit(0)
        return True
