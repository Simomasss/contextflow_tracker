import customtkinter as ctk
from datetime import datetime, timedelta
from ..dialogs.edit_log import EditLogDialog

class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, aggregator, **kwargs):
        super().__init__(master, **kwargs)
        self.aggregator = aggregator
        
        # HLAVNÍ STAV: Jaký den právě prohlížíme
        self.current_date = datetime.now().date()
        
        # Slovníky pro propojení Osa <-> Seznam
        self.canvas_to_log = {}  # ID na plátně -> objekt Logu
        self.log_to_row = {}     # ID logu -> CTkFrame v seznamu
        self.last_hovered_log_id = None  # POMOCNÁ PROMĚNNÁ PRO OPTIMALIZACI

        # Konfigurace layoutu
        self.grid_columnconfigure(0, weight=3) # Levý sloupec (Logs)
        self.grid_columnconfigure(1, weight=1) # Pravý sloupec (Stats)
        self.grid_rowconfigure(2, weight=1)    # Spodní část se roztahuje

        # --- TOP: NAVIGACE A DATUM ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Osa aktivity", 
                                        font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=10)

        # Navigační kontejner
        self.nav_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.nav_frame.pack(side="right", padx=10)

        self.prev_btn = ctk.CTkButton(self.nav_frame, text="<", width=30, 
                                      command=self.prev_day)
        self.prev_btn.pack(side="left", padx=5)

        self.date_label = ctk.CTkLabel(self.nav_frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.date_label.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(self.nav_frame, text=">", width=30, 
                                      command=self.next_day)
        self.next_btn.pack(side="left", padx=5)

        self.today_btn = ctk.CTkButton(self.nav_frame, text="Dnes", width=60, fg_color="gray",
                                       command=self.go_today)
        self.today_btn.pack(side="left", padx=(10, 0))

        # --- MIDDLE: TIMELINE ---
        self.canvas = ctk.CTkCanvas(self, height=100, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # --- BOTTOM LEFT: RAW LOGS ---
        self.logs_frame = ctk.CTkScrollableFrame(self, label_text="Detailní výpis aktivity")
        self.logs_frame.grid(row=2, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # --- BOTTOM RIGHT: SUMMARY STATS ---
        self.stats_frame = ctk.CTkScrollableFrame(self, label_text="Souhrn dne")
        self.stats_frame.grid(row=2, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Načíst data a vykreslit
        self.after(100, self.refresh_data)

        # Nabindujeme pohyb myši na canvas
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        self.canvas.bind("<Leave>", self.on_canvas_leave)
        
        # Tooltip (blob) - schovaný label, který budeme posouvat
        self.tooltip = ctk.CTkLabel(self, text="", fg_color="#1a1a1a", text_color="white", 
                                   corner_radius=6, font=("Arial", 11), padx=10)
        self.tooltip.place_forget()

    # --- NAVIGAČNÍ LOGIKA ---

    def prev_day(self):
        self.current_date -= timedelta(days=1)
        self.refresh_data()

    def next_day(self):
        self.current_date += timedelta(days=1)
        self.refresh_data()

    def go_today(self):
        self.current_date = datetime.now().date()
        self.refresh_data()

    def refresh_data(self):
        formatted_date = self.current_date.strftime("%d. %m. %Y")
        self.date_label.configure(text=formatted_date)

        logs = self.aggregator.get_raw_logs(
            datetime.combine(self.current_date, datetime.min.time()),
            datetime.combine(self.current_date, datetime.max.time())
        )
        
        self.draw_timeline(logs)
        self.update_logs_list(logs)
        self.update_stats(self.current_date)

    
    def update_logs_list(self, logs):
        # 1. Vyčistit starý seznam
        for widget in self.logs_frame.winfo_children():
            widget.destroy()

        self.log_to_row = {} # Vyčistit staré reference
        self.logs_frame.grid_columnconfigure(2, weight=1)

        # 2. ZÁHLAVÍ (Header)
        header_row = ctk.CTkFrame(self.logs_frame, fg_color="#333333", height=30)
        header_row.pack(fill="x", padx=5, pady=(0, 5))
        
        header_row.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(header_row, text="Čas", width=120).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkLabel(header_row, text="Klient / Projekt", width=180, anchor="w").grid(row=0, column=1, padx=5, sticky="w")
        ctk.CTkLabel(header_row, text="Aktivita (Okno)", anchor="w").grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(header_row, text="Akce", width=50).grid(row=0, column=3, padx=5)

        if not logs:
            ctk.CTkLabel(self.logs_frame, text="Dnes zatím žádná aktivita.").pack(pady=20)
            return

        # 3. DATA
        for log in reversed(logs):
            row = ctk.CTkFrame(self.logs_frame, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)

            # Uložíme si frame pod ID logu
            self.log_to_row[log.id] = row
            row.grid_columnconfigure(2, weight=1) # Sloupec s titulkem okna je pružný
            
            # Čas
            time_str = f"{log.start_time.strftime('%H:%M:%S')} - {log.end_time.strftime('%H:%M:%S')}"
            ctk.CTkLabel(row, text=time_str, font=("Consolas", 11), width=120).grid(row=0, column=0, padx=5)
            
            # Klient / Projekt
            cp_text = f"{log.project.client.name} / {log.project.name}"
            ctk.CTkLabel(row, text=cp_text, font=("Arial", 11, "bold"), width=180, anchor="w").grid(row=0, column=1, padx=5)
            
            win_title = log.window_title[:60] + "..." if len(log.window_title) > 60 else log.window_title
            ctk.CTkLabel(row, text=win_title, font=("Arial", 11), anchor="w").grid(row=0, column=2, padx=5, sticky="ew")
            
            edit_btn = ctk.CTkButton(
                row, text="✎", width=35, height=24, fg_color="#444444",
                command=lambda l=log: self.open_edit_dialog(l)
            )
            edit_btn.grid(row=0, column=3, padx=5)
            
    def update_stats(self, target_date):
        stats = self.aggregator.get_daily_stats_v2(target_date)
        
        # 1. Definice palety barev
        COLORS = ["#3b8ed0", "#1f8d4e", "#d69e2e", "#8d1f1f", "#7d33ff", "#1fb18a"]
        
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        if not stats:
            ctk.CTkLabel(self.stats_frame, text="Žádná data pro tento den", font=("Arial", 12, "italic")).pack(pady=20)
            return

        total_day_seconds = sum(sum(p.values()) for p in stats.values())

        for i, (client, projects) in enumerate(stats.items()):
            client_color = COLORS[i % len(COLORS)]
            
            ctk.CTkLabel(
                self.stats_frame, 
                text=client.upper(), 
                font=("Arial", 11, "bold"), 
                text_color=client_color
            ).pack(anchor="w", padx=15, pady=(15, 5))
            
            for project, seconds in projects.items():
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                
                total_day_seconds = sum(sum(p.values()) for p in stats.values())
                ratio = seconds / total_day_seconds if total_day_seconds > 0 else 0
                
                if h > 0:
                    time_str = f"{h} h {m} min"
                else:
                    # Ochrana pro velmi krátké aktivity pod 1 minutu
                    time_str = f"{m} min" if m > 0 else "< 1 min"

                # "Projekt (1 h 36 min)"
                lbl_text = f"{project} ({time_str})"
                
                proj_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
                proj_frame.pack(fill="x", padx=20, pady=2)
                
                ctk.CTkLabel(proj_frame, text=lbl_text, font=("Arial", 12), anchor="w").pack(side="top", fill="x")
                
                bar = ctk.CTkProgressBar(proj_frame, height=14, corner_radius=6)
                bar.set(ratio)
                bar.configure(progress_color=client_color, fg_color="#242424")
                bar.pack(side="top", fill="x", pady=(2, 8))

        # Finální součet
        total_h = int(total_day_seconds // 3600)
        total_m = int((total_day_seconds % 3600) // 60)

        if total_h > 0:
            total_time_str = f"{total_h} h {total_m} min"
        else:
            total_time_str = f"{total_m} min"

        # Vykreslení
        ctk.CTkLabel(self.stats_frame, text="────────────────").pack(pady=5)
        total_lbl = ctk.CTkLabel(
            self.stats_frame, 
            text=f"CELKEM ODPRACOVÁNO: {total_time_str}", 
            font=("Arial", 15, "bold"),
            text_color="#ffffff"
        )
        total_lbl.pack(pady=10, padx=15)

    def open_edit_dialog(self, log):
        EditLogDialog(self, log, self.aggregator.db, self.refresh_data)

    def draw_timeline(self, logs):
        self.canvas.delete("all")
        self.canvas_to_log = {}
        
        w = self.canvas.winfo_width()
        if w <= 1: w = 800
        
        # 1. POZADÍ (Track) - Šedá linka
        self.canvas.create_rectangle(0, 35, w, 45, fill="#333333", outline="")

        for i in range(25):
            x = (i / 24) * w
            self.canvas.create_line(x, 30, x, 50, fill="#444444")
            if i % 3 == 0:
                self.canvas.create_text(x, 65, text=f"{i:02}:00", fill="#666666", font=("Arial", 9))

        # 2. BLOKY AKTIVITY
        colors = ["#1f538d", "#1f8d4e", "#8d531f", "#8d1f1f", "#5b1f8d"]
        project_colors = {}
        color_idx = 0

        day_start = datetime.combine(self.current_date, datetime.min.time())
        day_end = datetime.combine(self.current_date, datetime.max.time())

        for log in logs:
            p_name = log.project.name
            if p_name not in project_colors:
                project_colors[p_name] = colors[color_idx % len(colors)]
                color_idx += 1

            actual_start = max(log.start_time, day_start)
            actual_end = min(log.end_time, day_end)

            start_h = actual_start.hour + actual_start.minute/60 + actual_start.second/3600
            end_h = actual_end.hour + actual_end.minute/60 + actual_end.second/3600
            
            x1 = (start_h / 24) * w
            x2 = (end_h / 24) * w
            
            # Pokud je blok moc malý (sekundy), zvětšíme ho na aspoň 3px, aby šel vidět
            if x2 - x1 < 3: x2 = x1 + 3

            # Vykreslení hezčího bloku
            rect_id = self.draw_rounded_rect(
                x1, 25, x2, 55, 
                radius=5, 
                fill=project_colors[p_name], 
                outline=""
            )
            
            # Uložíme si, který log patří ke kterému ID na canvasu pro hover
            self.canvas_to_log[rect_id] = log

    def on_canvas_hover(self, event):
        """Zobrazí tooltip a posune seznam logů na příslušný záznam."""
        closest = self.canvas.find_closest(event.x, event.y)
        if not closest: 
            return
            
        item = closest[0]
        log = self.canvas_to_log.get(item)
        
        for row in self.log_to_row.values():
            row.configure(fg_color="transparent")

        if log and log.id in self.log_to_row:
            row_widget = self.log_to_row[log.id]
            
            row_widget.configure(fg_color="#2b5a8c") 

            self.update_idletasks()
            
            canvas = self.logs_frame._parent_canvas
            
            total_height = canvas.bbox("all")[3]
            if total_height > 0:
                target_y = row_widget.winfo_y()
                scroll_pos = target_y / total_height
                canvas.yview_moveto(scroll_pos)

    def on_canvas_leave(self, event):
        self.tooltip.place_forget()
        for row in self.log_to_row.values():
            row.configure(fg_color="transparent")

    def draw_rounded_rect(self, x1, y1, x2, y2, radius=8, **kwargs):
        points = [
            x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, 
            x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, 
            y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, 
            y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, 
            x1, y1+radius, x1, y1+radius, x1, y1
        ]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)