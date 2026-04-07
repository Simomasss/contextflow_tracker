import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

class EditLogDialog(ctk.CTkToplevel):
    def __init__(self, master, log, db, on_save_callback):
        super().__init__(master)
        self.title("Upravit záznam")
        self.geometry("400x350")
        
        self.log = log
        self.db = db
        self.on_save = on_save_callback

        # Aby okno zůstalo v popředí a blokovalo interakci s hlavním oknem (volitelné)
        self.attributes("-topmost", True)
        self.grab_set() 

        ctk.CTkLabel(self, text=f"Upravit čas\n{log.project.client.name} / {log.project.name}", font=("Arial", 16, "bold")).pack(pady=20)

        # START TIME
        ctk.CTkLabel(self, text="Začátek (HH:MM:SS):").pack()
        self.start_entry = ctk.CTkEntry(self)
        self.start_entry.insert(0, log.start_time.strftime("%H:%M:%S"))
        self.start_entry.pack(pady=5)

        # END TIME
        ctk.CTkLabel(self, text="Konec (HH:MM:SS):").pack()
        self.end_entry = ctk.CTkEntry(self)
        self.end_entry.insert(0, log.end_time.strftime("%H:%M:%S"))
        self.end_entry.pack(pady=5)

        # Tlačítka
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(btn_frame, text="Smazat záznam", fg_color="#8d1f1f", width=100, command=self.delete_action).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Uložit změny", fg_color="#1f8d4e", width=100, command=self.save_action).pack(side="left", padx=10)

    def save_action(self):
        try:
            # Převedeme text zpět na časové objekty (předpokládáme stejný den)
            base_date = self.log.start_time.date()
            new_start = datetime.combine(base_date, datetime.strptime(self.start_entry.get(), "%H:%M:%S").time())
            new_end = datetime.combine(base_date, datetime.strptime(self.end_entry.get(), "%H:%M:%S").time())

            if new_start >= new_end:
                messagebox.showerror("Chyba", "Konec musí být až po začátku!")
                return

            # Voláme DB Handler
            if self.db.update_activity_log(self.log.id, new_start, new_end):
                self.on_save() # Zavolá refresh_data v HomeFrame
                self.destroy()
        except Exception as e:
            messagebox.showerror("Chyba", "Neplatný formát času (použij HH:MM:SS)")

    def delete_action(self):
        if messagebox.askyesno("Smazat", "Opravdu smazat tento log?"):
            if self.db.delete_activity_log(self.log.id):
                self.on_save()
                self.destroy()