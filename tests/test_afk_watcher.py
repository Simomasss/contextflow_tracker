import unittest
from unittest.mock import patch

from src.watchers.afk_watcher import AFKWatcher

class TestAFKWatcher(unittest.TestCase):

    def test_is_not_afk(self):
        """Should return False if idle time is below the threshold."""
        watcher = AFKWatcher(threshold_seconds=300)
        with patch.object(watcher, 'get_idle_time', return_value=150 * 1000): # 150 seconds
            self.assertFalse(watcher.watch())

    def test_is_afk(self):
        """Should return True if idle time is above the threshold."""
        watcher = AFKWatcher(threshold_seconds=300)
        with patch.object(watcher, 'get_idle_time', return_value=301 * 1000): # 301 seconds
            self.assertTrue(watcher.watch())

    @patch('win32api.GetLastInputInfo')
    @patch('win32api.GetTickCount')
    def test_get_idle_time_normal(self, mock_get_tick_count, mock_get_last_input):
        """Test idle time calculation in a normal scenario."""
        mock_get_tick_count.return_value = 20000
        mock_get_last_input.return_value = 15000
        watcher = AFKWatcher()
        self.assertEqual(watcher.get_idle_time(), 5000)

    @patch('win32api.GetLastInputInfo')
    @patch('win32api.GetTickCount')
    def test_get_idle_time_wraparound(self, mock_get_tick_count, mock_get_last_input):
        """Test idle time calculation when the system tick counter wraps around (after 49.7 days)."""
        UINT_MAX = (1 << 32)
        mock_get_tick_count.return_value = 5000  # Counter has wrapped to a small number
        mock_get_last_input.return_value = UINT_MAX - 10000  # Last input was just before the wrap
        watcher = AFKWatcher()
        # The expected idle time should be 5000 - (-10000) = 15000
        self.assertEqual(watcher.get_idle_time(), 15000)