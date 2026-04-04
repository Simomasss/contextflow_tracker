from datetime import date
from src.billing.invoice_generator import InvoiceGenerator
from src.database.db_handler import DatabaseManager
from src.core.aggregator import ActivityAggregator
from src.core.config import AppSettings

def test_print_invoice():
    # Připojíme se k testovací DB
    settings = AppSettings(MAIN_FOLDER="C:/Users/donth/VSE/BAKALARKA/MAIN")
    db = DatabaseManager(settings=settings, db_url="sqlite:///TESTcontextflow.db")
    
    agg = ActivityAggregator(db)
    
    # Chceme fakturovat projekt 1 (Adam) za celé období testu
    # (Projekt ID 1 v testovací DB je 'projekt1')
    invoice_data = agg.get_invoice_data(
        project_id=1, 
        start_date=date(2026, 3, 1), # Nastav podle dat v testovací DB
        end_date=date(2026, 4, 30)
    )

    if not invoice_data:
        print("Projekt nenalezen!")
        return
    else: 
        gen = InvoiceGenerator(invoice_data)
    gen.generate("testovaci_faktura.pdf")

    

if __name__ == "__main__":
    test_print_invoice()

'''
print("\n" + "="*50)
    print(" NÁHLED PODKLADŮ PRO FAKTURU ".center(50, "="))
    print("="*50)
    
    print(f"\nODESÍLATEL: {invoice_data['sender']['name']}")
    print(f"IČO: {invoice_data['sender']['ico']} | Účet: {invoice_data['sender']['bank_account']}")
    
    print(f"\nPŘÍJEMCE: {invoice_data['recipient']['name']}")
    print(f"Adresa: {invoice_data['recipient']['address']}")
    print(f"IČO: {invoice_data['recipient']['ico']}")
    
    print("-" * 50)
    print(f"PROJEKT: {invoice_data['job']['project_name']}")
    print(f"OBDOBÍ:  {invoice_data['job']['period']}")
    print(f"ČAS:     {invoice_data['job']['total_hours']} h (zaokrouhleno)")
    print(f"SAZBA:   {invoice_data['job']['hourly_rate']} {invoice_data['job']['currency']}/h")
    print("-" * 50)
    print(f"CELKEM K ÚHRADĚ: {invoice_data['job']['total_price']:.2f} {invoice_data['job']['currency']}")
    print("="*50 + "\n")
'''