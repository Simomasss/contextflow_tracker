# run_gui.py
from src.gui.app import ContextFlowGUI
import customtkinter as ctk

# Nastavení vzhledu (volitelné, ale vypadá to líp)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    app = ContextFlowGUI()
    app.mainloop()