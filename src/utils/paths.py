import os
import sys

def get_app_data_dir(app_name="ContextFlow") -> str:
    """Returns the platform-specific directory for application data."""
    if not getattr(sys, 'frozen', False):
        # Running as a script (development mode)
        # Assuming this file is in src/utils, project root is two levels up
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, "..", ".."))

    # Running as a frozen executable (production mode)
    if sys.platform == "win32":
        base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base_dir, app_name)
    elif sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
    else:
        # Linux and others
        base_dir = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        return os.path.join(base_dir, app_name)
