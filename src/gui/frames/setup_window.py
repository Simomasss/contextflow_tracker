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
        self.geometry("800x700") 
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

    # --- STRÁNKA 1: VÍTEJTE & STRUKTURA ---
    def show_step_1(self):
        ctk.CTkLabel(self.main_container, text="Vítejte v ContextFlow!", font=("Arial", 28, "bold")).pack(pady=(10, 5))
        
        # Varování o alfa verzi
        warning_box = ctk.CTkFrame(self.main_container, fg_color="#3d2b1f", corner_radius=10)
        warning_box.pack(fill="x", pady=10)
        ctk.CTkLabel(warning_box, text="⚠️ Aplikace je v rané fázi vývoje (Alpha)", font=("Arial", 13, "bold"), text_color="#ffcc00").pack(pady=5)

        # Obrázek struktury
        try:
            img_path = resource_path("src/gui/assets/setup_folder.png")
            setup_img = ctk.CTkImage(light_image=Image.open(img_path), 
                                     dark_image=Image.open(img_path), 
                                     size=(700, 352))
            img_label = ctk.CTkLabel(self.main_container, image=setup_img, text="")
            img_label.pack(pady=15)
        except Exception as e:
            ctk.CTkLabel(self.main_container, text=f"[Obrázek struktury chybí]\n{e}", text_color="red").pack()

        info_text = (
            "Aby ContextFlow věděl, ke kterému projektu práce patří, je nutné dodržovat\n"
            "tuto strukturu složek. Na konci průvodce si zvolíte vaši hlavní 'MAIN' složku."
        )
        ctk.CTkLabel(self.main_container, text=info_text, font=("Arial", 13), justify="center").pack(pady=10)

        self.add_navigation_buttons()

    # --- STRÁNKA 2: CHYBY & WHITELIST ---
    def show_step_2(self):
        ctk.CTkLabel(self.main_container, text="Něco se neměří správně?", font=("Arial", 24, "bold")).pack(pady=(20, 20))
        
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        tips = [
            ("🌐 Web a E-maily", "V této verzi aplikace zatím nepodporuje měření webových prohlížečů (kromě PDF otevřených v prohlížečích např. Chrome/Edge) ani e-mailových klientů."),
            ("📝 Whitelist programů", "Pokud pracujete v editoru a čas neběží, zkontrolujte, zda máte název .exe souboru v 'Nastavení -> Whitelist'. Např. 'code.exe' pro VS Code nebo 'WINWORD.exe' pro word.\nPokud aplikace není ve whitelistu -> nebude sledována!!!\nPro dohledání .exe názvu, napište do prohlížeče 'danou aplikaci a exe name'."),
            ("📂 Kontext souboru", "Tracker se aktivuje pouze tehdy, pokud máte otevřený soubor, který fyzicky leží uvnitř vaší MAIN složky.\nKontext se následně přiřadí, když je soubor správně pod klientem a určitým projektem.")
        ]

        for title, desc in tips:
            box = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=8)
            box.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(box, text=title, font=("Arial", 15, "bold"), text_color="#3b8ed0").pack(anchor="w", padx=15, pady=(10, 0))
            ctk.CTkLabel(box, text=desc, font=("Arial", 12), justify="left", wraplength=600).pack(anchor="w", padx=15, pady=(5, 10))

        self.add_navigation_buttons()

    # --- STRÁNKA 3: FINÁLE ---
    def show_step_3(self):
        ctk.CTkLabel(self.main_container, text="Vše je připraveno!", font=("Arial", 28, "bold")).pack(pady=(50, 20))
        
        final_info = (
            "Po kliknutí na tlačítko níže si vyberete (nebo vytvoříte) svou MAIN složku.\n\n"
            "Aplikace se poté schová do systémové lišty (vpravo dole u hodin).\n"
            "Kliknutím pravým tlačítkem na ikonu otevřete přehled naměřeného času.\n\n"
            "A to je vše! Přeji hodně štěstí a produktivní práci s ContextFlow! 🚀"
        )
        ctk.CTkLabel(self.main_container, text=final_info, font=("Arial", 15), justify="center").pack(pady=20)

        # Hlavní tlačítko
        ctk.CTkButton(self.main_container, text="VYBRAT SLOŽKU A ZAČÍT", 
                       command=self.select_folder, height=60, font=("Arial", 16, "bold"),
                       fg_color="#28a745", hover_color="#218838").pack(pady=40)
        
        # Tlačítko zpět
        ctk.CTkButton(self.main_container, text="Zpět", command=self.prev_step, width=100).pack(side="bottom", pady=20)

    # --- POMOCNÉ FUNKCE ---
    def add_navigation_buttons(self):
        nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        nav_frame.pack(side="bottom", fill="x", pady=20)

        if self.current_step > 1:
            ctk.CTkButton(nav_frame, text="Zpět", command=self.prev_step, width=100).pack(side="left", padx=10)
        
        ctk.CTkButton(nav_frame, text="Další →", command=self.next_step, width=150, font=("Arial", 13, "bold")).pack(side="right", padx=10)

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