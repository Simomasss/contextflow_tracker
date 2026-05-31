import os
import sys
import shutil
import tempfile
import subprocess
import logging
import winreg
from datetime import datetime
from src.utils.paths import get_app_data_dir
from src.utils.platform_handler import BasePlatformHandler

class WindowsPlatformHandler(BasePlatformHandler):
    def handle_installation(self) -> bool:
        """
        Pokud je aplikace spuštěna jako EXE z náhodného místa,
        přesune se automaticky do LocalAppData a na původním místě zanechá zástupce.
        """
        if not getattr(sys, 'frozen', False):
            return True

        current_exe = os.path.abspath(sys.executable)
        appdata_dir = get_app_data_dir()
        target_exe = os.path.join(appdata_dir, "ContextFlow.exe")

        if os.path.normcase(current_exe) == os.path.normcase(target_exe):
            return True

        os.makedirs(appdata_dir, exist_ok=True)

        try:
            logging.info(f"Probíhá instalace EXE do: {target_exe}")
            shutil.copy2(current_exe, target_exe)

            original_dir = os.path.dirname(current_exe)
            original_name = os.path.splitext(os.path.basename(current_exe))[0]
            shortcut_path = os.path.join(original_dir, f"{original_name}.lnk")

            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            Set oLink = oWS.CreateShortcut("{shortcut_path}")
            oLink.TargetPath = "{target_exe}"
            oLink.WorkingDirectory = "{appdata_dir}"
            oLink.IconLocation = "{target_exe}"
            oLink.Save
            """
            vbs_path = os.path.join(tempfile.gettempdir(), "create_shortcut.vbs")
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_script)
            
            subprocess.run(["cscript.exe", "//Nologo", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
            
            try:
                os.remove(vbs_path)
            except Exception:
                pass

            bat_path = os.path.join(tempfile.gettempdir(), "cf_migrate.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("timeout /t 2 /nobreak > NUL\n")
                f.write(f'del "{current_exe}"\n')
                f.write(f'start "" "{target_exe}"\n')
                f.write('del "%~f0"\n')

            subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            logging.info("Aplikace byla úspěšně přesunuta. Restartuji...")
            os._exit(0)

        except Exception as e:
            logging.error(f"Nepodařilo se přesunout aplikaci do AppData: {e}")
            return False
            
        return True

    def setup_autostart(self) -> bool:
        """Přidá aktuální EXE do registru pro start po zapnutí PC."""
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                try:
                    current_val, _ = winreg.QueryValueEx(key, "ContextFlow")
                    if current_val != app_path:
                        winreg.SetValueEx(key, "ContextFlow", 0, winreg.REG_SZ, app_path)
                        logging.info("✓ Cesta v registru aktualizována.")
                except FileNotFoundError:
                    winreg.SetValueEx(key, "ContextFlow", 0, winreg.REG_SZ, app_path)
                    logging.info("✓ Aplikace přidána do po spuštění.")
                finally:
                    winreg.CloseKey(key)
                return True
            except Exception as e:
                logging.error(f"Nepodařilo se zapsat/číst do registru: {e}")
                return False
        return True

    def remove_autostart(self) -> bool:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "ContextFlow")
            winreg.CloseKey(key)
            logging.info("✓ Registr vyčištěn.")
            return True
        except (FileNotFoundError, OSError):
            return True
        except Exception as e:
            logging.error(f"Chyba při mazání registru: {e}")
            return False

    def uninstall(self, backup_diagnostics: bool = True) -> bool:
        """Provede odinstalaci aplikace a zálohuje data."""
        self.remove_autostart()
        
        exe_path = ""
        is_exe = False
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            is_exe = True

        app_data_dir = get_app_data_dir()
        
        if backup_diagnostics:
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
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
            cmd_parts = ["timeout /t 3 > nul", f'rmdir /s /q "{app_data_dir}"']
            if is_exe and exe_path and not os.path.normcase(exe_path).startswith(os.path.normcase(app_data_dir)):
                cmd_parts.append(f'del /f /q "{exe_path}"')
                
            cmd = " && ".join(cmd_parts)
            safe_cwd = os.path.expanduser("~")
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW, cwd=safe_cwd)

        os._exit(0)
        return True
