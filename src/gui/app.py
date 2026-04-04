import customtkinter as ctk

class ContextFlowGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ContextFlow v1.0")
        self.geometry("1100x700")

        # Konfigurace gridu (vlevo sloupec pro menu, vpravo zbytek)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="ContextFlow", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=20)

        self.home_btn = ctk.CTkButton(self.sidebar, text="Home", command=self.show_home)
        self.home_btn.pack(pady=10, padx=20)

        self.clients_btn = ctk.CTkButton(self.sidebar, text="Clients", command=self.show_clients)
        self.clients_btn.pack(pady=10, padx=20)

        # 2. MAIN CONTENT AREA
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Inicializace první stránky
        self.show_home()

    def show_home(self):
        # Vymazat main_view
        for widget in self.main_view.winfo_children():
            widget.destroy()
        
        # Tady se vykreslí Dashboard (Timeline, Logs, Stats)
        label = ctk.CTkLabel(self.main_view, text="Dashboard / Timeline", font=ctk.CTkFont(size=24))
        label.pack()

    def show_clients(self):
        # Vymazat main_view
        for widget in self.main_view.winfo_children():
            widget.destroy()

        # Tady se vykreslí seznam klientů
        label = ctk.CTkLabel(self.main_view, text="Seznam klientů", font=ctk.CTkFont(size=24))
        label.pack()

if __name__ == "__main__":
    app = ContextFlowGUI()
    app.mainloop()