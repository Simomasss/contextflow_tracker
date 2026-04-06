from fpdf import FPDF
import os

class InvoiceGenerator:
    def __init__(self, invoice_data):
        self.data = invoice_data
        self.pdf = FPDF()
        self.pdf.add_page()
        # Použijeme standardní font, dokud si nenastavíš vlastní s CZ diakritikou
        # TODO: --- NASTAVENÍ FONTU (Nutné pro češtinu) ---
        # Stáhni si libovolný .ttf font s podporou CZ a dej k němu cestu
        # Pokud ho zatím nemáš, Python vyhodí chybu u diakritiky.
        # self.pdf.add_font('DejaVu', '', 'src/assets/fonts/DejaVuSans.ttf', uni=True)
        # self.pdf.set_font('DejaVu', size=10)
        
        # Pro začátek použijeme standardní font (pozor, ořeže české znaky!)
        self.pdf.set_font("Helvetica", size=10)

    def generate(self, output_path):
        # 1. HLAVIČKA
        if self.data['sender'].get('logo_path') and os.path.exists(self.data['sender']['logo_path']):
            self.pdf.image(self.data['sender']['logo_path'], 10, 8, 33)
        
        self.pdf.set_font("Helvetica", 'B', 16)
        self.pdf.cell(0, 10, "FAKTURA - DANOVY DOKLAD", new_x="LMARGIN", new_y="NEXT", align='R')
        self.pdf.ln(10)
        # --- TADY PŘIDÁME OBDOBÍ ---
        self.pdf.set_font("Helvetica", '', 10)
        self.pdf.cell(0, 10, f"Fakturacni obdobi: {self.data['period']}", new_x="LMARGIN", new_y="NEXT", align='R')
        self.pdf.ln(5)

        # 2. ADRESY
        self.pdf.set_font("Helvetica", 'B', 11)
        self.pdf.cell(95, 10, "DODAVATEL:", new_x="RIGHT", new_y="TOP")
        self.pdf.cell(95, 10, "ODBERATEL:", new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_font("Helvetica", size=10)
        y_start = self.pdf.get_y()
        # Multi_cell už defaultně odřádkovává, tam ln/new_x obvykle netřeba řešit tak striktně
        self.pdf.multi_cell(95, 5, f"{self.data['sender']['name']}\n{self.data['sender']['address']}\nICO: {self.data['sender']['ico']}\nDIC: {self.data['sender']['dic']}")
        
        self.pdf.set_xy(105, y_start)
        self.pdf.multi_cell(95, 5, f"{self.data['recipient']['name']}\n{self.data['recipient']['address']}\nICO: {self.data['recipient']['ico']}\nDIC: {self.data['recipient']['dic']}")
        
        self.pdf.ln(20)

        # 3. PLATEBNÍ INFORMACE
        self.pdf.set_fill_color(240, 240, 240)
        self.pdf.cell(0, 10, f"Bankovni ucet: {self.data['sender']['bank_account']}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.pdf.ln(5)

        # 4. TABULKA PRÁCE (Hlavička)
        self.pdf.set_font("Helvetica", 'B', 10)
        self.pdf.cell(100, 10, "Popis prace / Projekt", border=1, new_x="RIGHT", new_y="TOP")
        self.pdf.cell(30, 10, "Hodin", border=1, align='C', new_x="RIGHT", new_y="TOP")
        self.pdf.cell(30, 10, "Sazba", border=1, align='C', new_x="RIGHT", new_y="TOP")
        self.pdf.cell(30, 10, "Celkem", border=1, align='C', new_x="LMARGIN", new_y="NEXT")

        # 4b. ŘÁDKY TABULKY (Dynamicky pro každý projekt)
        self.pdf.set_font("Helvetica", size=10)
        for job in self.data['jobs']:
            self.pdf.cell(100, 10, f"{job['name']}", border=1, new_x="RIGHT", new_y="TOP")
            self.pdf.cell(30, 10, f"{job['hours']}", border=1, align='C', new_x="RIGHT", new_y="TOP")
            self.pdf.cell(30, 10, f"{job['rate']} {job['currency']}", border=1, align='C', new_x="RIGHT", new_y="TOP")
            self.pdf.cell(30, 10, f"{job['total']:.2f} {job['currency']}", border=1, align='C', new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.ln(10)

        # 5. REKAPITULACE (Z grand_total)
        self.pdf.set_font("Helvetica", 'B', 12)
        self.pdf.cell(160, 10, "CELKEM K UHRADE:", align='R', new_x="RIGHT", new_y="TOP")
        self.pdf.set_text_color(255, 0, 0)
        self.pdf.cell(30, 10, f"{self.data['grand_total']:.2f} {self.data['currency']}", align='R', new_x="LMARGIN", new_y="NEXT")
        # Export
        self.pdf.output(output_path)
        print(f"✓ PDF Faktura vytvořena: {output_path}")

        # TODO: Upravit to pdf at to vypada profesionalne, zatim jen zaklad