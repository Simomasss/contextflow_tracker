import unittest
from src.core.config import AppSettings
from src.database.db_handler import DatabaseManager
from src.database.models import Base, Client, Project, BillingProfile

class TestDatabaseBilling(unittest.TestCase):
    def setUp(self):
        # Uložíme si AppSettings s in-memory DB_URL
        settings = AppSettings()
        self.db = DatabaseManager(settings=settings, db_url='sqlite:///:memory:')
        Base.metadata.create_all(self.db.engine)

    def test_get_and_save_billing_details(self):
        # 1. Pro neexistujícího klienta vrací prázdný dict
        details = self.db.get_billing_details(999)
        self.assertEqual(details, {})

        # 2. Vložíme testovací data
        with self.db.Session() as session:
            client = Client(name="Acme Corp", address="123 Road", ico="123", dic="CZ123", email="acme@corp.com")
            session.add(client)
            session.flush()
            
            project = Project(name="Website", client_id=client.id, hourly_rate=500.0)
            session.add(project)
            session.commit()
            
            client_id = client.id
            project_id = project.id

        # 3. Načtení detailů
        details = self.db.get_billing_details(client_id)
        self.assertIn("client", details)
        self.assertEqual(details["client"]["name"], "Acme Corp")
        self.assertEqual(details["client"]["address"], "123 Road")
        self.assertEqual(details["profile"]["name"], "") # prázdný profil na začátku
        self.assertEqual(len(details["projects"]), 1)
        self.assertEqual(details["projects"][0]["name"], "Website")
        self.assertEqual(details["projects"][0]["hourly_rate"], 500.0)

        # 4. Uložení nových údajů
        profile_data = {
            "name": "Freelancer John",
            "address": "456 Lane",
            "ico": "987",
            "dic": "",
            "bank_account": "123456/0100",
            "logo_path": "/path/to/logo.png"
        }
        client_data = {
            "name": "Acme Corp Updated",
            "address": "123 Road Updated",
            "ico": "1234",
            "dic": "CZ1234",
            "email": "updated@acme.com"
        }
        project_rates = {
            project_id: 600.0
        }
        
        self.db.save_billing_details(client_id, profile_data, client_data, project_rates)

        # 5. Ověření, že se data uložila a načtou správně
        details = self.db.get_billing_details(client_id)
        self.assertEqual(details["profile"]["name"], "Freelancer John")
        self.assertEqual(details["profile"]["bank_account"], "123456/0100")
        self.assertEqual(details["profile"]["logo_path"], "/path/to/logo.png")
        self.assertEqual(details["client"]["name"], "Acme Corp Updated")
        self.assertEqual(details["client"]["email"], "updated@acme.com")
        self.assertEqual(details["projects"][0]["hourly_rate"], 600.0)
