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

        self.attributes("-topmost", True)
        self.grab_set() 

        ctk.CTkLabel(self, text=f"Upravit čas\n{log.project.client.name} / {log.project.name}", font=("Arial", 16, "bold")).pack(pady=20)

        # START DATETIME
        start_frame = ctk.CTkFrame(self, fg_color="transparent")
        start_frame.pack(pady=5)
        
        ctk.CTkLabel(start_frame, text="Začátek (DD.MM.RRRR a HH:MM:SS):").grid(row=0, column=0, columnspan=2, sticky="w")
        
        self.start_date_entry = ctk.CTkEntry(start_frame, width=120)
        self.start_date_entry.insert(0, log.start_time.strftime("%d.%m.%Y"))
        self.start_date_entry.grid(row=1, column=0, padx=5)
        
        self.start_time_entry = ctk.CTkEntry(start_frame, width=100)
        self.start_time_entry.insert(0, log.start_time.strftime("%H:%M:%S"))
        self.start_time_entry.grid(row=1, column=1, padx=5)

        # END DATETIME
        end_frame = ctk.CTkFrame(self, fg_color="transparent")
        end_frame.pack(pady=5)
        
        ctk.CTkLabel(end_frame, text="Konec (DD.MM.RRRR a HH:MM:SS):").grid(row=0, column=0, columnspan=2, sticky="w")
        
        self.end_date_entry = ctk.CTkEntry(end_frame, width=120)
        self.end_date_entry.insert(0, log.end_time.strftime("%d.%m.%Y"))
        self.end_date_entry.grid(row=1, column=0, padx=5)
        
        self.end_time_entry = ctk.CTkEntry(end_frame, width=100)
        self.end_time_entry.insert(0, log.end_time.strftime("%H:%M:%S"))
        self.end_time_entry.grid(row=1, column=1, padx=5)

        # Tlačítka
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(btn_frame, text="Smazat záznam", fg_color="#8d1f1f", width=100, command=self.delete_action).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Uložit změny", fg_color="#1f8d4e", width=100, command=self.save_action).pack(side="left", padx=10)

    def save_action(self):
        try:
            start_str = f"{self.start_date_entry.get().strip()} {self.start_time_entry.get().strip()}"
            end_str = f"{self.end_date_entry.get().strip()} {self.end_time_entry.get().strip()}"
            
            new_start = datetime.strptime(start_str, "%d.%m.%Y %H:%M:%S")
            new_end = datetime.strptime(end_str, "%d.%m.%Y %H:%M:%S")

            if new_start >= new_end:
                self.attributes("-topmost", False)
                messagebox.showerror("Chyba", "Konec musí být až po začátku!")
                self.attributes("-topmost", True)
                return

            if self.db.update_activity_log(self.log.id, new_start, new_end):
                self.on_save()
                self.destroy()
        except Exception as e:
            self.attributes("-topmost", False)
            messagebox.showerror("Chyba", "Neplatný formát data nebo času (použij DD.MM.RRRR a HH:MM:SS)")
            self.attributes("-topmost", True)

    def delete_action(self):
        self.attributes("-topmost", False)
        confirm = messagebox.askyesno("Smazat", "Opravdu smazat tento log?")
        self.attributes("-topmost", True)
        if confirm:
            if self.db.delete_activity_log(self.log.id):
                self.on_save()
                self.destroy()