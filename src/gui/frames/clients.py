import customtkinter as ctk
from datetime import date, datetime, timedelta
from tkinter import messagebox
from sqlalchemy import select

from ...database.models import Project, Client, BillingProfile
from ...billing.invoice_generator import InvoiceGenerator

class ClientsFrame(ctk.CTkFrame):
    def __init__(self, master, aggregator, **kwargs):
        super().__init__(master, **kwargs)
        self.aggregator = aggregator
        self.selected_client_id = None

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=0, minsize=200) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEVÝ PANEL: SEZNAM ---
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Klienti", width=200)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # --- PRAVÝ PANEL: DETAIL ---
        self.detail_container = ctk.CTkScrollableFrame(self, label_text="Nastavení fakturace")
        self.detail_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        self.render_list()

    def render_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        clients = self.aggregator.get_all_clients_summary()
        for c in clients:
            btn = ctk.CTkButton(
                self.list_frame, 
                text=f"{c['name']}\n{c['total_hours']:.1f} h",
                command=lambda cid=c['id']: self.show_detail(cid),
                fg_color="transparent", border_width=1,
                anchor="w"
            )
            btn.pack(fill="x", pady=2, padx=5)

    def show_detail(self, client_id):
        self.selected_client_id = client_id
        
        # Vyčistit kontejner
        for widget in self.detail_container.winfo_children():
            widget.destroy()

        # Načíst data z DB
        with self.aggregator.db.Session() as session:
            client = session.get(Client, client_id)
            profile = session.execute(select(BillingProfile)).scalar_one_or_none()
            projects = session.execute(select(Project).where(Project.client_id == client_id)).scalars().all()

        if not client: return

        # --- SEKCE 1: ODESÍLATEL ---
        self._add_section_label("ODESÍLATEL (Můj profil)")
        self.sender_entries = self._create_form(self.detail_container, {
            "name": ("Jméno/Firma:", profile.name if profile else ""),
            "address": ("Adresa:", profile.address if profile else ""),
            "ico": ("IČO:", profile.ico if profile else ""),
            "dic": ("DIČ:", profile.dic if profile else ""),
            "bank": ("Bankovní účet:", profile.bank_account if profile else "")
        })

        # --- SEKCE 2: PŘÍJEMCE ---
        self._add_section_label(f"PŘÍJEMCE (Klient: {client.name})")
        self.client_entries = self._create_form(self.detail_container, {
            "name": ("Název klienta:", client.name),
            "address": ("Adresa:", client.address or ""),
            "ico": ("IČO:", client.ico or ""),
            "dic": ("DIČ:", client.dic or ""),
            "email": ("Email:", client.email or "")
        })

        # --- SEKCE 3: OBDOBÍ A PROJEKT ---
        self._add_section_label("PARAMETRY FAKTURY")
        
        # Výpočet dat
        today = date.today()
        first_this_month = today.replace(day=1)
        last_last_month = first_this_month - timedelta(days=1)
        first_last_month = last_last_month.replace(day=1)

        date_frame = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=10)

        # OD:
        ctk.CTkLabel(date_frame, text="Od:").grid(row=0, column=0, padx=5)
        self.date_from = ctk.CTkEntry(date_frame, width=120)
        self.date_from.insert(0, first_last_month.strftime("%d.%m.%Y"))
        self.date_from.grid(row=0, column=1, padx=5)
        # BINDING: Při Enteru nebo kliknutí vedle se spustí update
        self.date_from.bind("<Return>", self.update_project_hours)
        self.date_from.bind("<FocusOut>", self.update_project_hours)

        # DO:
        ctk.CTkLabel(date_frame, text="Do:").grid(row=0, column=2, padx=5)
        self.date_to = ctk.CTkEntry(date_frame, width=120)
        self.date_to.insert(0, last_last_month.strftime("%d.%m.%Y"))
        self.date_to.grid(row=0, column=3, padx=5)
        # BINDING:
        self.date_to.bind("<Return>", self.update_project_hours)
        self.date_to.bind("<FocusOut>", self.update_project_hours)

        # --- SEZNAM PROJEKTŮ ---
        self._add_section_label("PROJEKTY K ZAHRNUTÍ")
        
        # Rámeček pro seznam
        self.proj_list_container = ctk.CTkFrame(self.detail_container, border_width=1, border_color="gray")
        self.proj_list_container.pack(fill="x", padx=20, pady=10)

        self.project_vars = {}
        self.project_hour_labels = {} # TADY si uložíme ty štítky pro pozdější update

        for p in projects:
            row = ctk.CTkFrame(self.proj_list_container, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)
            
            var = ctk.BooleanVar(value=False) 
            self.project_vars[p.id] = var
            
            cb = ctk.CTkCheckBox(row, text=f"{p.name}", variable=var, font=("Arial", 12))
            cb.pack(side="left", padx=10, pady=5)
            
            # Vytvoříme label a uložíme si ho do slovníku pod ID projektu
            hrs_label = ctk.CTkLabel(row, text="-- h", text_color="gray")
            hrs_label.pack(side="right", padx=10)
            self.project_hour_labels[p.id] = hrs_label

        # Na konci show_detail jednou zavoláme update, aby se tam hned objevily časy pro výchozí měsíc
        self.update_project_hours()

        # --- AKČNÍ TLAČÍTKA ---
        btn_frame = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(btn_frame, text="Uložit změny profilů", command=self.save_profiles, fg_color="gray").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Generovat PDF Fakturu", command=self.generate_invoice, fg_color="green").pack(side="left", padx=5)

    def _add_section_label(self, text):
        lbl = ctk.CTkLabel(self.detail_container, text=text, font=("Arial", 14, "bold"), text_color="#1f538d")
        lbl.pack(anchor="w", padx=10, pady=(15, 5))

    def _create_form(self, master, fields):
        entries = {}
        for key, (label, value) in fields.items():
            row = ctk.CTkFrame(master, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row)
            entry.insert(0, value)
            entry.pack(side="right", fill="x", expand=True)
            entries[key] = entry
        return entries

    def save_profiles(self):
        try:
            with self.aggregator.db.Session() as session:
                profile = session.execute(select(BillingProfile)).scalar_one_or_none()
                if not profile:
                    profile = BillingProfile()
                    session.add(profile)
                
                profile.name = self.sender_entries["name"].get()
                profile.address = self.sender_entries["address"].get()
                profile.ico = self.sender_entries["ico"].get()
                profile.dic = self.sender_entries["dic"].get()
                profile.bank_account = self.sender_entries["bank"].get()

                client = session.get(Client, self.selected_client_id)
                client.name = self.client_entries["name"].get()
                client.address = self.client_entries["address"].get()
                client.ico = self.client_entries["ico"].get()
                client.dic = self.client_entries["dic"].get()
                client.email = self.client_entries["email"].get()

                session.commit()
            messagebox.showinfo("Hotovo", "Údaje byly uloženy.")
            self.render_list()
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se uložit: {e}")

    def _select_all_projects(self):
        for var in self.project_vars.values():
            var.set(True)

    def _deselect_all_projects(self):
        for var in self.project_vars.values():
            var.set(False)

    def update_project_hours(self, event=None):
        """Aktualizuje pouze texty s hodinami bez překreslení celého okna."""
        try:
            # 1. Zkusíme přečíst data z políček
            d_from_str = self.date_from.get()
            d_to_str = self.date_to.get()
            
            d_from = datetime.strptime(d_from_str, "%d.%m.%Y").date()
            d_to = datetime.strptime(d_to_str, "%d.%m.%Y").date()

            # 2. Projdeme všechny uložené labely a aktualizujeme je
            for pid, label in self.project_hour_labels.items():
                hrs = self.aggregator.get_project_hours(pid, d_from, d_to)
                label.configure(text=f"{hrs:.1f} h")
                
        except ValueError:
            # Pokud uživatel zrovna píše nesmysly, nic neděláme a nepadáme
            pass

    def generate_invoice(self):
        try:
            selected_ids = [pid for pid, var in self.project_vars.items() if var.get()]
            if not selected_ids:
                messagebox.showwarning("Varování", "Vyberte alespoň jeden projekt!")
                return

            d_from = datetime.strptime(self.date_from.get(), "%d.%m.%Y").date()
            d_to = datetime.strptime(self.date_to.get(), "%d.%m.%Y").date()

            data = self.aggregator.get_invoice_data(selected_ids, d_from, d_to)
            gen = InvoiceGenerator(data)
            filename = f"Faktura_{data['recipient']['name']}_{date.today().strftime('%Y%m%d')}.pdf"
            gen.generate(filename)
            
            messagebox.showinfo("Úspěch", f"Faktura s {len(data['jobs'])} projekty vytvořena.")
        except ValueError:
            messagebox.showerror("Chyba", "Špatný formát data. Použijte DD.MM.RRRR")
        except Exception as e:
            messagebox.showerror("Chyba", f"Generování selhalo: {e}")