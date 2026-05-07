import unittest
import tempfile
from pathlib import Path

from src.core.indexer import IndexManager

class TestIndexManager(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

        # Structure:
        # /ClientA/Project1/main.py
        # /ClientA/Project1/.vscode/settings.json (ignored)
        # /ClientA/Project2/report.docx
        # /ClientB/ProjectWithConflict/main.py

        (self.root / "ClientA").mkdir()
        (self.root / "ClientA" / "Project1").mkdir()
        (self.root / "ClientA" / "Project1" / "main.py").touch()
        (self.root / "ClientA" / "Project1" / ".vscode").mkdir()
        (self.root / "ClientA" / "Project1" / ".vscode" / "settings.json").touch()

        (self.root / "ClientA" / "Project2").mkdir()
        (self.root / "ClientA" / "Project2" / "report.docx").touch()

        (self.root / "ClientB").mkdir()
        (self.root / "ClientB" / "ProjectWithConflict").mkdir()
        (self.root / "ClientB" / "ProjectWithConflict" / "main.py").touch()

        self.indexer = IndexManager(str(self.root))

    def tearDown(self):
        """Clean up the temporary directory."""
        self.tmpdir.cleanup()

    def test_reindex(self):
        """Test if the index is built correctly."""
        self.assertIn("project1", self.indexer.lookup_map)
        self.assertIn("project2", self.indexer.lookup_map)
        self.assertIn("projectwithconflict", self.indexer.lookup_map)
        self.assertIn("main.py", self.indexer.lookup_map)
        self.assertIn("report.docx", self.indexer.lookup_map)

        # Check ignored folders
        self.assertNotIn(".vscode", self.indexer.lookup_map)
        self.assertNotIn("settings.json", self.indexer.lookup_map)

        # Check content
        self.assertEqual(len(self.indexer.lookup_map["main.py"]), 2)
        self.assertEqual(self.indexer.lookup_map["project1"][0]["client"], "ClientA")

    def test_match_by_project_name(self):
        """Should match a window title containing the project folder name."""
        match = self.indexer.match_title("C:\\Path\\To\\Work - Project1 - Visual Studio Code")
        assert match is not None
        self.assertEqual(match["client"], "ClientA")
        self.assertEqual(match["project"], "Project1")

    def test_match_by_file_name(self):
        """Should match a window title containing a file name from the index."""
        match = self.indexer.match_title("report.docx - Microsoft Word")
        assert match is not None
        self.assertEqual(match["client"], "ClientA")
        self.assertEqual(match["project"], "Project2")

    def test_no_match(self):
        """Should return None for a title that doesn't match anything."""
        match = self.indexer.match_title("Spotify - My Favorite Song")
        self.assertIsNone(match)

    def test_tie_breaker_with_conflict(self):
        """If a file exists in two projects, the title should resolve the conflict."""
        # 'main.py' exists in Project1 and ProjectWithConflict
        match = self.indexer.match_title("main.py - ProjectWithConflict - VS Code")
        assert match is not None
        self.assertEqual(match["client"], "ClientB")
        self.assertEqual(match["project"], "ProjectWithConflict")