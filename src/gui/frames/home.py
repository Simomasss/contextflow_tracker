import customtkinter as ctk
from datetime import datetime, timedelta


class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, aggregator, **kwargs):
        super().__init__(master, **kwargs)
        self.aggregator = aggregator
        
        # Konfigurace layoutu
        self.grid_columnconfigure(0, weight=3) # Levý sloupec (Logs)
        self.grid_columnconfigure(1, weight=1) # Pravý sloupec (Stats)
        self.grid_rowconfigure(1, weight=1)

        # --- TOP: TIMELINE ---
        self.timeline_label = ctk.CTkLabel(self, text="Dnešní osa aktivity", font=ctk.CTkFont(size=16, weight="bold"))
        self.timeline_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        self.canvas = ctk.CTkCanvas(self, height=80, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # --- BOTTOM LEFT: RAW LOGS ---
        self.logs_frame = ctk.CTkScrollableFrame(self, label_text="Detailní výpis")
        self.logs_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # --- BOTTOM RIGHT: SUMMARY STATS ---
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=2, column=1, sticky="nsew", pady=10)
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Souhrn dne", font=ctk.CTkFont(weight="bold"))
        self.stats_label.pack(pady=10)

        # Načíst data a vykreslit
        self.after(100, self.refresh_data)  # Počkej 100ms, než se okno usadí
        
    def refresh_data(self):
        # 1. Získáme data pro dnešek
        today = datetime.now().date()
        logs = self.aggregator.get_raw_logs(
            datetime.combine(today, datetime.min.time()),
            datetime.combine(today, datetime.max.time())
        )
        
        self.draw_timeline(logs)
        self.update_logs_list(logs)
        self.update_stats(today)

    def draw_timeline(self, logs):
        self.canvas.delete("all") # Vyčistit plátno
        
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1: canvas_width = 800 # Fallback pro první vykreslení
        
        # Kreslení pozadí a hodinových značek
        for i in range(25):
            x = (i / 24) * canvas_width
            self.canvas.create_line(x, 0, x, 80, fill="#3d3d3d")
            if i % 3 == 0: # Každé 3 hodiny text
                self.canvas.create_text(x+5, 70, text=f"{i:02}:00", fill="gray", font=("Arial", 8))

        # Kreslení bloků aktivity
        colors = ["#1f538d", "#1f8d4e", "#8d531f", "#8d1f1f"] # Barvy pro různé projekty
        project_colors = {}
        color_index = 0

        for log in logs:
            if log.project.name not in project_colors:
                project_colors[log.project.name] = colors[color_index % len(colors)]
                color_index += 1
            
            # Přepočet času na X souřadnice (0-24h -> 0-Width)
            start_hour = log.start_time.hour + log.start_time.minute / 60
            end_hour = log.end_time.hour + log.end_time.minute / 60
            
            x_start = (start_hour / 24) * canvas_width
            x_end = (end_hour / 24) * canvas_width
            
            # Vykreslení obdélníku aktivity
            self.canvas.create_rectangle(x_start, 15, x_end, 55, 
                                         fill=project_colors[log.project.name], 
                                         outline="")

    def update_logs_list(self, logs):
        for widget in self.logs_frame.winfo_children():
            widget.destroy()
        
        for log in reversed(logs):
            time_str = f"{log.start_time.strftime('%H:%M')} - {log.end_time.strftime('%H:%M')}"
            txt = f"{time_str} | {log.project.name} | {log.window_title[:40]}..."
            lbl = ctk.CTkLabel(self.logs_frame, text=txt, anchor="w", font=("Consolas", 11))
            lbl.pack(fill="x", padx=5)

    def update_stats(self, target_date):
        stats = self.aggregator.get_daily_stats(target_date)
        for widget in self.stats_frame.winfo_children():
            if widget != self.stats_label: widget.destroy()
            
        for project, seconds in stats.items():
            hours = seconds / 3600
            lbl = ctk.CTkLabel(self.stats_frame, text=f"{project}: {hours:.2f} h")
            lbl.pack(pady=2)