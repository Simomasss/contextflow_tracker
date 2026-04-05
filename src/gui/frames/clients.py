import customtkinter as ctk
from datetime import date

from sqlalchemy import select
from ...billing.invoice_generator import InvoiceGenerator

class ClientsFrame(ctk.CTkFrame):
    def __init__(self, master, aggregator, **kwargs):
        super().__init__(master, **kwargs)
        self.aggregator = aggregator
        self.selected_client = None

        self.grid_columnconfigure(0, weight=1) # Seznam
        self.grid_columnconfigure(1, weight=2) # Detail
        self.grid_rowconfigure(0, weight=1)

        # --- LEVÝ PANEL: SEZNAM ---
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Seznam klientů")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)

        # --- PRAVÝ PANEL: DETAIL ---
        self.detail_frame = ctk.CTkFrame(self)
        self.detail_frame.grid(row=0, column=1, sticky="nsew", pady=10, padx=10)
        
        self.render_list()

    def render_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        clients = self.aggregator.get_all_clients_summary()
        for c in clients:
            btn = ctk.CTkButton(
                self.list_frame, 
                text=f"{c['name']}\n({c['total_hours']:.1f} h)",
                command=lambda client=c: self.show_detail(client),
                fg_color="transparent", border_width=1
            )
            btn.pack(fill="x", pady=5, padx=5)

    def show_detail(self, client):
        self.selected_client = client
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.detail_frame, text=f"Detail klienta: {client['name']}", font=("Arial", 18, "bold")).pack(pady=10)

        # Jednoduchý formulář (ukázka IČO)
        ctk.CTkLabel(self.detail_frame, text="IČO:").pack(anchor="w", padx=20)
        ico_entry = ctk.CTkEntry(self.detail_frame)
        ico_entry.insert(0, client['ico'])
        ico_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Tlačítko pro fakturaci
        ctk.CTkLabel(self.detail_frame, text="Fakturace", font=("Arial", 14, "bold")).pack(pady=(20, 10))
        
        # Pro bakalářku uděláme fixní rozmezí (tento měsíc) pro ukázku
        btn_invoice = ctk.CTkButton(
            self.detail_frame, 
            text="Generovat fakturu (Březen 2026)", 
            fg_color="green",
            command=lambda: self.generate_pdf(client)
        )
        btn_invoice.pack(pady=10)

    def generate_pdf(self, client):
        # Získáme data z aggregatoru (pro první projekt klienta jako příklad)
        # V reálu by si uživatel vybral projekt ze seznamu
        with self.aggregator.db.Session() as session:
            from ...database.models import Project
            proj = session.execute(select(Project).where(Project.client_id == client['id'])).scalar()
            
            if proj:
                data = self.aggregator.get_invoice_data(proj.id, date(2026, 3, 1), date(2026, 3, 31))
                gen = InvoiceGenerator(data)
                gen.generate(f"Faktura_{client['name']}.pdf")
                print("Faktura vygenerována!")