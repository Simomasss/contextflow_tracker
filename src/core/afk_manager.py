from pynput import mouse, keyboard
import time

class AFKManager:
    def __init__(self, idle_threshold: int = 300):
        """
        :param idle_threshold: Po kolika sekundách bez pohybu jsi AFK (default 5 min)
        """
        self.last_activity = time.time()
        self.threshold = idle_threshold
        
        # Spustíme listenery na pozadí
        self.mouse_listener = mouse.Listener(on_move=self._on_activity)
        self.kb_listener = keyboard.Listener(on_press=self._on_activity)
        self.mouse_listener.start()
        self.kb_listener.start()

    def _on_activity(self, *args):
        self.last_activity = time.time()

    def is_afk(self) -> bool:
        return (time.time() - self.last_activity) > self.threshold