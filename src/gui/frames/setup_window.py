import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import os
import sys

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class SetupWindow(ctk.CTk):
    def __init__(self, on_folder_select):
        super().__init__()
        self.title("ContextFlow - Prvotní nastavení")
        self.geometry("850x700") 
        self.on_folder_select = on_folder_select

        self.after(10, lambda: self.state("normal")) 
        self.attributes("-topmost", True)
        
        # Ikona okna
        try:
            self.iconbitmap(resource_path("src/gui/assets/icon.ico"))
        except:
            pass

        # Container pro stránky
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=40, pady=20)

        self.current_step = 1
        self.show_step()

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_step(self):
        self.clear_container()
        if self.current_step == 1:
            self.show_step_1()
        elif self.current_step == 2:
            self.show_step_2()
        elif self.current_step == 3:
            self.show_step_3()

    # --- STRÁNKA 1: VÍTEJTE & ÚVOD ---
    def show_step_1(self):
        ctk.CTkLabel(self.main_container, text="Vítejte v ContextFlow!", font=("Arial", 30, "bold")).pack(pady=(40, 10))
        
        # Varování o alfa verzi
        warning_box = ctk.CTkFrame(self.main_container, fg_color="#3d2b1f", corner_radius=10)
        warning_box.pack(fill="x", pady=20)
        ctk.CTkLabel(warning_box, text="⚠️ Aplikace je v rané fázi vývoje (Alpha)", font=("Arial", 14, "bold"), text_color="#ffcc00").pack(pady=10)

        intro_text = (
            "ContextFlow je nástroj pro automatické měření času stráveného prací na vašich projektech.\n\n"
            "Po dokončení tohoto nastavení poběží aplikace tiše na pozadí a schová se do\n"
            "systémové lišty (System Tray) vedle hodin.\n\n"
            "Kliknutím pravým tlačítkem myši na ikonu kdykoliv otevřete přehled naměřeného času.\n\n"
            "Pojďme si v dalších krocích projít, jak ContextFlow správně používat."
        )
        ctk.CTkLabel(self.main_container, text=intro_text, font=("Arial", 15), justify="center", width=600).pack(pady=30)

        self.add_navigation_buttons()

    # --- STRÁNKA 2: CHYBY & WHITELIST ---
    def show_step_2(self):
        ctk.CTkLabel(self.main_container, text="Důležitá pravidla měření", font=("Arial", 28, "bold")).pack(pady=(20, 20))
        
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        tips = [
            ("🌐 Web a E-maily", "Měření webových prohlížečů a e-mailových klientů není zatím plně podporováno (s výjimkou čtení PDF souborů v prohlížeči)."),
            ("📝 Whitelist programů", "Aplikace měří pouze programy, které máte povolené. Zkontrolujte v 'Nastavení -> Whitelist', zda tam máte přesný název .exe souboru programu, který používáte (např. 'code.exe' pro VS Code nebo 'WINWORD.exe' pro Word). Pokud tam program chybí, čas se pro něj nebude počítat!"),
            ("📂 Kontext souboru", "Sledování času se spustí pouze tehdy, když aktivně pracujete se souborem, který fyzicky leží ve vaší zvolené MAIN složce. Aplikace z cesty souboru sama pozná, na kterém projektu u kterého klienta právě pracujete.")
        ]

        for title, desc in tips:
            box = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=8)
            box.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(box, text=title, font=("Arial", 16, "bold"), text_color="#3b8ed0").pack(anchor="w", padx=15, pady=(15, 5))
            ctk.CTkLabel(box, text=desc, font=("Arial", 14), justify="left", wraplength=700).pack(anchor="w", padx=15, pady=(0, 15))

        self.add_navigation_buttons()

    # --- STRÁNKA 3: STRUKTURA & VÝBĚR SLOŽKY ---
    def show_step_3(self):
        ctk.CTkLabel(self.main_container, text="Struktura projektů", font=("Arial", 28, "bold")).pack(pady=(10, 5))
        
        info_text = (
            "Aby ContextFlow spolehlivě poznal, ke kterému projektu vaše práce patří,\n"
            "je nutné ve vaší hlavní pracovní složce (MAIN) dodržovat následující strukturu:"
        )
        ctk.CTkLabel(self.main_container, text=info_text, font=("Arial", 14), justify="center").pack(pady=10)

        # Obrázek struktury
        try:
            img_path = resource_path("src/gui/assets/setup_folder.png")
            setup_img = ctk.CTkImage(light_image=Image.open(img_path), 
                                     dark_image=Image.open(img_path), 
                                     size=(700, 352))
            img_label = ctk.CTkLabel(self.main_container, image=setup_img, text="")
            img_label.pack(pady=10)
        except Exception as e:
            ctk.CTkLabel(self.main_container, text=f"[Obrázek struktury chybí]\n{e}", text_color="red").pack()

        action_text = "Nyní si tuto hlavní (MAIN) složku vyberte na svém disku."
        ctk.CTkLabel(self.main_container, text=action_text, font=("Arial", 15, "bold")).pack(pady=(10, 20))

        # Hlavní CTA
        ctk.CTkButton(self.main_container, text="Vybrat MAIN složku a začít", 
                       command=self.select_folder, height=45, width=250, font=("Arial", 15, "bold")).pack(pady=10)
        
        # Tlačítko zpět pro návrat
        nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        nav_frame.pack(side="bottom", fill="x", pady=20)
        ctk.CTkButton(nav_frame, text="Zpět", command=self.prev_step, width=100, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="left", padx=10)

    # --- POMOCNÉ FUNKCE ---
    def add_navigation_buttons(self):
        nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        nav_frame.pack(side="bottom", fill="x", pady=20)

        if self.current_step > 1:
            ctk.CTkButton(nav_frame, text="Zpět", command=self.prev_step, width=100, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="left", padx=10)
        
        ctk.CTkButton(nav_frame, text="Další krok →", command=self.next_step, width=150, font=("Arial", 14, "bold")).pack(side="right", padx=10)

    def next_step(self):
        self.current_step += 1
        self.show_step()

    def prev_step(self):
        self.current_step -= 1
        self.show_step()

    def select_folder(self):
        path = filedialog.askdirectory(title="Vyberte vaši hlavní složku projektů (MAIN)")
        if path:
            self.on_folder_select(path)
            self.destroy()
