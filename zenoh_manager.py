# zenoh_manager.py
import zenoh
from PySide6.QtCore import QObject, Signal

class ZenohManager(QObject):
    message_received = Signal(str, str)

    def __init__(self):
        super().__init__()
        cfg = zenoh.Config()
        self.session = zenoh.open(cfg)
        self.subscribers = {}
        self.publishers = {}
        self.routes = {}  # key → list of callbacks

    def route(self, key, callback):
        if not key:
            return

        if key not in self.routes:
            self.routes[key] = []

        self.routes[key].append(callback)

        # Connect Qt signal to callback (runs in GUI thread)
        self.message_received.connect(
            lambda k, p, cb=callback: cb(p) if k == key else None
        )

        self.subscribe(key)



    def subscribe(self, key):
        if key in self.subscribers:
            return

        def callback(sample):
            payload = bytes(sample.payload).decode("utf-8")
            # Emit Qt signal — SAFE
            self.message_received.emit(key, payload)

        self.subscribers[key] = self.session.declare_subscriber(key, callback)