from src.utils.platform_handler import get_platform_handler

def run_contextflow_uninstaller():
    """Provede odinstalaci aplikace delegováním na platformní handler."""
    handler = get_platform_handler()
    handler.uninstall(backup_diagnostics=True)
