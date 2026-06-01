import os
import sys
import tempfile
import logging
import re
from datetime import datetime, timedelta
from fpdf import FPDF
import qrcode

def resource_path(relative_path):
    """ Pomocná funkce pro získání absolutní cesty k prostředkům (pro PyInstaller) """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class InvoiceGenerator:
    def __init__(self, invoice_data):
        self.data = invoice_data
        self.pdf = FPDF()
        self.pdf.add_page()
        
        self.font_regular = resource_path("src/gui/assets/Roboto-Regular.ttf")
        
        try:
            self.pdf.add_font('Roboto', '', self.font_regular)
            self.base_font = 'Roboto'
        except Exception as e:
            logging.warning(f"Failed to load Roboto font from {self.font_regular}: {e}")
            self.base_font = 'Helvetica'

    def _convert_to_iban(self, account_str):
        cleaned = re.sub(r'[^0-9/-]', '', account_str)
        if not "/" in cleaned:
            return ""

        prefix_and_account, bank_code = cleaned.split("/", 1)

        if "-" in prefix_and_account:
            prefix, account_num = prefix_and_account.split("-", 1)
        else:
            prefix, account_num = "0", prefix_and_account

        prefix = prefix.zfill(6)
        account_num = account_num.zfill(10)
        bank_code = bank_code.zfill(4)

        # Základní kód pro výpočet kontrolního součtu IBAN pro ČR (CZ)
        # Pro jednoduchost a neprůstřelnost využijeme standardní český algoritmus:
        # Bank_code + Prefix + Account_num + '123500' (převod CZ00 na čísla)
        # Výsledný IBAN formát: CZ + 2 kontrolní číslice + bank_code + prefix + account_num
        # Abychom se vyhnuli složité matematice, můžeme použít ověřený vzorec nebo nuly, 
        # ale nejlepší je sestavit čistý IBAN. Pro ČR platí výpočet mod97.

        buffer = f"{bank_code}{prefix}{account_num}123500"
        remainder = int(buffer) % 97
        check_digits = f"{98 - remainder}".zfill(2)

        return f"CZ{check_digits}{bank_code}{prefix}{account_num}"

    def _clean_bank_account(self, account_str):
        if not account_str:
            return ""
        return account_str.replace(" ", "")

    def generate(self, output_path):
        sender = self.data.get('sender', {})
        recipient = self.data.get('recipient', {})
        
        # INVOICE NUMBER
        invoice_number = self.data.get('invoice_number')
        if not invoice_number:
            # Fallback dokud neni DB implementovana
            # TODO: Unikatni cisla aby prichazeli z DB
            invoice_number = datetime.now().strftime('%Y%m%d%H%M')
            
        grand_total = self.data.get('grand_total', 0.0)
        
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)
        
        issue_date_str = issue_date.strftime('%d.%m.%Y')
        due_date_str = due_date.strftime('%d.%m.%Y')

        # 1. HEADER
        y_header_start = self.pdf.get_y()
        
        logo_path = sender.get('logo_path')
        if logo_path and os.path.exists(logo_path):
            self.pdf.image(logo_path, x=10, y=10, w=35)
            
        self.pdf.set_y(y_header_start)
        
        try:
            self.pdf.set_font(self.base_font, 'B', 12)
        except:
            self.pdf.set_font(self.base_font, '', 12)

        self.pdf.cell(0, 6, f"FAKTURA - DAŇOVÝ DOKLAD [{invoice_number}]", new_x="LMARGIN", new_y="NEXT", align='R')

        self.pdf.set_y(55)

        # 2. ADDRESS BLOCKS
        y_blocks = self.pdf.get_y()
        
        # DODAVATEL
        self.pdf.set_left_margin(10)
        self.pdf.set_y(y_blocks)
        try:
            self.pdf.set_font(self.base_font, 'B', 12)
        except:
            self.pdf.set_font(self.base_font, '', 12)

        self.pdf.cell(90, 8, "DODAVATEL:", new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_font(self.base_font, '', 10)
        sender_text = f"{sender.get('name', '')}\n"
        sender_text += f"{sender.get('address', '')}\n"
        sender_text += f"IČO: {sender.get('ico', '')}\n"
        if sender.get('dic'):
            sender_text += f"DIČ: {sender.get('dic', '')}\n"
        
        self.pdf.multi_cell(90, 5, sender_text)
        
        self.pdf.set_font(self.base_font, '', 8)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.multi_cell(90, 4, "Fyzická osoba zapsaná v živnostenském rejstříku.")
        self.pdf.set_text_color(0, 0, 0) # reset
        
        y_after_dodavatel = self.pdf.get_y()
        
        # ODBĚRATEL
        self.pdf.set_left_margin(110)
        self.pdf.set_y(y_blocks)
        try:
            self.pdf.set_font(self.base_font, 'B', 12)
        except:
            self.pdf.set_font(self.base_font, '', 12)

        self.pdf.cell(90, 8, "ODBĚRATEL:", new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_font(self.base_font, '', 10)
        recipient_text = f"{recipient.get('name', '')}\n"
        recipient_text += f"{recipient.get('address', '')}\n"
        recipient_text += f"IČO: {recipient.get('ico', '')}\n"
        if recipient.get('dic'):
            recipient_text += f"DIČ: {recipient.get('dic', '')}\n"
        
        self.pdf.multi_cell(90, 5, recipient_text)
        y_after_odberatel = self.pdf.get_y()
        
        self.pdf.set_left_margin(10) # Reset margin
        
        y_after_addresses = max(y_after_dodavatel, y_after_odberatel) + 10
        self.pdf.set_y(y_after_addresses)
        
        # 3. PAYMENT DETAILS & DATES (Gray block)
        self.pdf.set_fill_color(245, 245, 245)
        y_payment = self.pdf.get_y()
        self.pdf.rect(10, y_payment, 190, 25, style='F')
        
        self.pdf.set_xy(15, y_payment + 3)
        
        def set_bold_10():
            try:
                self.pdf.set_font(self.base_font, 'B', 10)
            except:
                self.pdf.set_font(self.base_font, '', 10)

        set_bold_10()
        self.pdf.cell(35, 6, "Číslo účtu:", new_x="RIGHT", new_y="TOP")
        self.pdf.set_font(self.base_font, '', 10)
        self.pdf.cell(65, 6, f"{sender.get('bank_account', '')}", new_x="RIGHT", new_y="TOP")
        
        set_bold_10()
        self.pdf.cell(35, 6, "Datum vystavení:", new_x="RIGHT", new_y="TOP")
        self.pdf.set_font(self.base_font, '', 10)
        self.pdf.cell(40, 6, f"{issue_date_str}", new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_x(15)
        set_bold_10()
        self.pdf.cell(35, 6, "Variabilní symbol:", new_x="RIGHT", new_y="TOP")
        self.pdf.set_font(self.base_font, '', 10)
        self.pdf.cell(65, 6, f"{invoice_number}", new_x="RIGHT", new_y="TOP")
        
        set_bold_10()
        self.pdf.cell(35, 6, "Datum zd. plnění:", new_x="RIGHT", new_y="TOP")
        self.pdf.set_font(self.base_font, '', 10)
        self.pdf.cell(40, 6, f"{issue_date_str}", new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_x(15)
        set_bold_10()
        self.pdf.cell(35, 6, "", new_x="RIGHT", new_y="TOP") 
        self.pdf.cell(65, 6, "", new_x="RIGHT", new_y="TOP")
        
        set_bold_10()
        self.pdf.cell(35, 6, "Datum splatnosti:", new_x="RIGHT", new_y="TOP")
        self.pdf.set_text_color(220, 53, 69) # Red color
        self.pdf.cell(40, 6, f"{due_date_str}", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_text_color(0, 0, 0) # reset
        
        self.pdf.set_y(y_payment + 35)

        # 4. TABLE
        set_bold_10()
        self.pdf.set_fill_color(245, 245, 245)
        self.pdf.cell(100, 10, "Popis práce / Projekt", border=0, align='L', fill=True, new_x="RIGHT", new_y="TOP")
        self.pdf.cell(30, 10, "Hodin", border=0, align='R', fill=True, new_x="RIGHT", new_y="TOP")
        self.pdf.cell(30, 10, "Sazba", border=0, align='R', fill=True, new_x="RIGHT", new_y="TOP")
        self.pdf.cell(30, 10, "Celkem", border=0, align='R', fill=True, new_x="LMARGIN", new_y="NEXT")

        self.pdf.set_font(self.base_font, '', 10)
        jobs = self.data.get('jobs', [])
        for job in jobs:
            name = job.get('name', '')
            hours = job.get('hours', 0)
            rate = job.get('rate', 0)
            total = job.get('total', 0)
            
            rate_int = int(round(float(rate)))
            total_int = int(round(float(total)))
            
            self.pdf.cell(100, 10, f"{name}", border=0, align='L', new_x="RIGHT", new_y="TOP")
            self.pdf.cell(30, 10, f"{hours}", border=0, align='R', new_x="RIGHT", new_y="TOP")
            self.pdf.cell(30, 10, f"{rate_int} Kč", border=0, align='R', new_x="RIGHT", new_y="TOP")
            self.pdf.cell(30, 10, f"{total_int} Kč", border=0, align='R', new_x="LMARGIN", new_y="NEXT")
            
            curr_y = self.pdf.get_y()
            self.pdf.line(10, curr_y, 200, curr_y)
        
        self.pdf.ln(15)

        # 5. FOOTER & QR CODE
        y_footer = self.pdf.get_y()
        
        # Generate QR code
        iban = self._convert_to_iban(sender.get('bank_account', ''))
        qr_temp_path = None
        if iban:
            vs_cleaned = re.sub(r'[^0-9]', '', str(invoice_number))[:10]
            spayd_str = f"SPD*1.0*ACC:{iban}*AM:{grand_total:.2f}*CC:CZK*X-VS:{vs_cleaned}"
            
            try:
                # qrcode library exposes ERROR_CORRECT_M either at module level or in qrcode.constants
                try:
                    error_const = qrcode.ERROR_CORRECT_M
                except AttributeError:
                    from qrcode import constants as _qrcode_constants
                    error_const = _qrcode_constants.ERROR_CORRECT_M

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=error_const,
                    box_size=10,
                    border=4,
                )
                qr.add_data(spayd_str)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    qr_temp_path = temp_file.name
                    # Write image to the open binary temp file to satisfy type expectations
                    img.save(temp_file, 'PNG')
                
                # Draw QR code
                self.pdf.image(qr_temp_path, x=10, y=y_footer, w=40)
            except Exception as e:
                logging.error(f"Failed to generate QR code: {e}")
        
        # Summary Box
        self.pdf.set_xy(110, y_footer)
        self.pdf.set_fill_color(245, 245, 245)
        self.pdf.rect(110, y_footer, 90, 20, style='F')
        
        self.pdf.set_xy(115, y_footer + 5)
        try:
            self.pdf.set_font(self.base_font, 'B', 14)
        except:
            self.pdf.set_font(self.base_font, '', 14)
            
        grand_total_int = int(round(float(grand_total)))
        self.pdf.cell(80, 10, f"CELKEM K ÚHRADĚ: {grand_total_int} Kč", align='R', new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_xy(110, y_footer + 25)
        self.pdf.set_font(self.base_font, '', 10)
        self.pdf.cell(90, 6, "Sazba DPH: 0% (Nejsem plátce DPH).", align='R', new_x="LMARGIN", new_y="NEXT")

        # Export
        self.pdf.output(output_path)
        logging.info(f"✓ PDF Faktura vytvořena: {output_path}")
        
        # Clean up QR code
        if qr_temp_path and os.path.exists(qr_temp_path):
            try:
                os.unlink(qr_temp_path)
            except Exception as e:
                logging.warning(f"Failed to delete temp QR code file: {e}")
