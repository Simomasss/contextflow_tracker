import unittest
from unittest.mock import Mock, MagicMock

from src.core.engine import ContextEngine
from src.core.schemas import WindowInfo, ContextMatch

class TestContextEngine(unittest.TestCase):

    def setUp(self):
        """Set up a mock environment for the engine."""
        self.mock_watcher = Mock()
        self.mock_indexer = Mock()
        self.mock_db = Mock()
        self.mock_afk = Mock()
        self.mock_settings = Mock()

        # Configure settings for predictable testing
        self.mock_settings.CONFIRM_START_TICKS = 3
        self.mock_settings.CONFIRM_EXIT_TICKS = 2
        self.mock_settings.TICK_INTERVAL = 1 # Makes tick counting easy

        # Default mock behaviors
        self.mock_afk.watch.return_value = False # Not AFK by default
        self.mock_watcher.watch.return_value = None # No window by default
        self.mock_indexer.match_title.return_value = None # No match by default

        self.engine = ContextEngine(
            watcher=self.mock_watcher,
            indexer=self.mock_indexer,
            db=self.mock_db,
            afk_watcher=self.mock_afk,
            settings=self.mock_settings
        )

    def _set_window(self, title, exe, is_whitelisted, project_match=None):
        """Helper to configure the mock watchers for a specific window state."""
        window_info = WindowInfo(title=title, executable=exe, is_whitelisted=is_whitelisted)
        self.mock_watcher.watch.return_value = window_info
        
        if project_match:
            match_dict = {'client': project_match.client_name, 'project': project_match.project_name}
            self.mock_indexer.match_title.return_value = match_dict
        else:
            self.mock_indexer.match_title.return_value = None

    def test_start_new_activity(self):
        """Test the transition from IDLE to a confirmed activity."""
        proj_A = ContextMatch(client_name="Client", project_name="ProjectA")
        self._set_window("proj_a.py - VSCode", "code.exe", True, proj_A)

        # Tick 1: Pending activity is set
        self.engine._tick()
        self.assertEqual(self.engine.pending_activity, proj_A)
        self.assertEqual(self.engine.current_activity, None)
        self.assertEqual(self.engine.timer, 1)
        self.mock_db.log_activity.assert_not_called()

        # Tick 2: Timer increments
        self.engine._tick()
        self.assertEqual(self.engine.timer, 2)
        self.mock_db.log_activity.assert_not_called()

        # Tick 3: Limit reached, activity confirmed
        self.engine._tick()
        self.assertEqual(self.engine.current_activity, proj_A)
        self.assertEqual(self.engine.timer, 0) # Timer resets
        self.mock_db.log_activity.assert_called_once_with(
            client_name="Client", project_name="ProjectA", window_title="proj_a.py - VSCode", executable="code.exe"
        )

    def test_exit_grace_period_and_return(self):
        """Test switching away from an activity and returning before the exit limit."""
        proj_A = ContextMatch(client_name="Client", project_name="ProjectA")
        self.engine.current_activity = proj_A # Start in an active state

        # Tick 1: Switch to an un-indexed window (e.g., Desktop)
        self._set_window("Desktop", "explorer.exe", False, None)
        self.engine._tick()

        self.assertEqual(self.engine.current_activity, proj_A) # Still holding ProjectA
        self.assertEqual(self.engine.timer, 1)
        # Should log "Grace Period" under the original project
        self.mock_db.log_activity.assert_called_with(client_name="Client", project_name="ProjectA", window_title="Grace Period", executable="Unknown")

        # Tick 2: Return to the original project window
        self._set_window("proj_a.py - VSCode", "code.exe", True, proj_A)
        self.engine._tick()

        self.assertEqual(self.engine.timer, 0) # Timer resets because we are back
        self.assertIsNone(self.engine.pending_activity)
        # DB is called again, now with correct window info
        self.mock_db.log_activity.assert_called_with(client_name="Client", project_name="ProjectA", window_title="proj_a.py - VSCode", executable="code.exe")

    def test_exit_and_stop_activity(self):
        """Test switching away and staying away until the activity is stopped."""
        proj_A = ContextMatch(client_name="Client", project_name="ProjectA")
        self.engine.current_activity = proj_A

        # Tick 1: Switch away
        self._set_window("Desktop", "explorer.exe", False, None)
        self.engine._tick()
        self.assertEqual(self.engine.timer, 1)
        self.mock_db.log_activity.assert_called_once() # Grace period log

        # Tick 2: Stay away, exit limit is reached
        self.engine._tick()
        self.assertIsNone(self.engine.current_activity) # Activity is now stopped
        self.assertEqual(self.engine.timer, 0)
        self.assertIsNone(self.engine.pending_activity)
        self.assertEqual(self.mock_db.log_activity.call_count, 1) # No new log on stop

    def test_switch_to_new_project(self):
        """Test switching from Project A to Project B."""
        proj_A = ContextMatch(client_name="Client", project_name="ProjectA")
        proj_B = ContextMatch(client_name="Client", project_name="ProjectB")
        self.engine.current_activity = proj_A

        # Tick 1: Switch to Project B window
        self._set_window("proj_b.js - VSCode", "code.exe", True, proj_B)
        self.engine._tick()
        
        self.assertEqual(self.engine.current_activity, proj_A) # Still holding A
        self.assertEqual(self.engine.pending_activity, proj_B)
        self.assertEqual(self.engine.timer, 1)
        self.mock_db.log_activity.assert_called_once() # Grace log for A

        # Tick 2: Stay on B, exit limit reached, switch is confirmed
        self.engine._tick()
        self.assertEqual(self.engine.current_activity, proj_B) # Switched to B
        self.assertEqual(self.engine.timer, 0)
        self.assertIsNone(self.engine.pending_activity)
        # A new log for Project B should be created
        self.mock_db.log_activity.assert_called_with(
            client_name="Client", project_name="ProjectB", window_title="proj_b.js - VSCode", executable="code.exe"
        )