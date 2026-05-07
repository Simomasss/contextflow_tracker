import unittest
from datetime import datetime, date, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Client, Project, ActivityLog, BillingProfile
from src.core.aggregator import ActivityAggregator

class MockDBManager:
    """Mocks the DatabaseManager by providing a Session connected to an in-memory SQLite database."""
    def __init__(self, engine):
        self.Session = sessionmaker(bind=engine)

class TestActivityAggregator(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory database and populate it with test data."""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db_manager = MockDBManager(self.engine)
        self.aggregator = ActivityAggregator(self.db_manager)

        self.target_date = date(2024, 5, 15)
        
        with self.db_manager.Session() as session:
            # 1. Billing Profile (Rounding set to 15 mins)
            profile = BillingProfile(name="Test Sender", rounding_minutes=15)
            
            # 2. Client
            client_a = Client(name="Client A")
            session.add_all([profile, client_a])
            session.flush() # Flush to get IDs

            # 3. Projects
            p1 = Project(name="Project 1", client_id=client_a.id, hourly_rate=1000.0, currency="CZK")
            p2 = Project(name="Project 2", client_id=client_a.id, hourly_rate=500.0, currency="CZK")
            session.add_all([p1, p2])
            session.flush()

            # 4. Activity Logs for Project 1 (Total: 75 minutes = 4500 seconds)
            l1 = ActivityLog(
                project_id=p1.id,
                start_time=datetime(2024, 5, 15, 10, 0, 0),
                end_time=datetime(2024, 5, 15, 10, 30, 0), # 30 mins
                window_title="Doc", executable="word.exe"
            )
            l2 = ActivityLog(
                project_id=p1.id,
                start_time=datetime(2024, 5, 15, 11, 0, 0),
                end_time=datetime(2024, 5, 15, 11, 45, 0), # 45 mins
                window_title="Code", executable="code.exe"
            )
            
            # 5. Activity Logs for Project 2 (Total: 10 minutes = 600 seconds)
            l3 = ActivityLog(
                project_id=p2.id,
                start_time=datetime(2024, 5, 15, 14, 0, 0),
                end_time=datetime(2024, 5, 15, 14, 10, 0), # 10 mins
                window_title="Email", executable="chrome.exe"
            )
            
            session.add_all([l1, l2, l3])
            session.commit()
            
            self.p1_id = p1.id
            self.p2_id = p2.id
            self.client_id = client_a.id

    def tearDown(self):
        """Clean up the in-memory database."""
        Base.metadata.drop_all(self.engine)

    def test_get_raw_logs(self):
        start = datetime.combine(self.target_date, time.min)
        end = datetime.combine(self.target_date, time.max)
        logs = self.aggregator.get_raw_logs(start, end)
        self.assertEqual(len(logs), 3)

    def test_get_daily_stats_v2(self):
        stats = self.aggregator.get_daily_stats_v2(self.target_date)
        
        self.assertIn("Client A", stats)
        self.assertIn("Project 1", stats["Client A"])
        self.assertIn("Project 2", stats["Client A"])
        
        self.assertEqual(stats["Client A"]["Project 1"], 4500) # 75 mins
        self.assertEqual(stats["Client A"]["Project 2"], 600)  # 10 mins

    def test_get_summary_for_billing_rounding(self):
        start = datetime.combine(self.target_date, time.min)
        end = datetime.combine(self.target_date, time.max)
        
        # Project 1: 75 mins. Nearest 15 is 75 mins -> 1.25 hours
        summary1 = self.aggregator.get_summary_for_billing(self.p1_id, start, end)
        self.assertEqual(summary1["raw_seconds"], 4500)
        self.assertEqual(summary1["billable_hours"], 1.25)
        self.assertEqual(summary1["total_price"], 1250.0) # 1.25 * 1000

        # Project 2: 10 mins. Nearest 15 (rounding up) -> 15 mins -> 0.25 hours
        summary2 = self.aggregator.get_summary_for_billing(self.p2_id, start, end)
        self.assertEqual(summary2["billable_hours"], 0.25)
        self.assertEqual(summary2["total_price"], 125.0) # 0.25 * 500

    def test_get_project_hours(self):
        hours = self.aggregator.get_project_hours(self.p1_id, self.target_date, self.target_date)
        # Raw hours: 75 mins / 60 = 1.25 (No rounding applied in this raw query)
        self.assertEqual(hours, 1.25)
        
    def test_get_invoice_data(self):
        data = self.aggregator.get_invoice_data([self.p1_id, self.p2_id], self.target_date, self.target_date)
        
        self.assertEqual(data["sender"]["name"], "Test Sender")
        self.assertEqual(len(data["jobs"]), 2)
        # 1250.0 (P1) + 125.0 (P2) = 1375.0
        self.assertEqual(data["grand_total"], 1375.0)