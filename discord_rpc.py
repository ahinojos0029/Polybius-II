# discord_rpc.py
import time

class DiscordManager:
    def __init__(self, client_id="1529672643945431090"):
        self.client_id = client_id
        self.rpc = None
        self.connected = False
        self.start_time = time.time()

    def connect(self):
        try:
            from pypresence import Presence
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
        except Exception:
            self.connected = False
            self.rpc = None

    def update(self, enabled, details_text, state_text=""):
        if self.connected and enabled and self.rpc:
            try:
                self.rpc.update(
                    details=details_text,
                    state=state_text if state_text else None,
                    start=self.start_time,
                    large_image="polybius_logo",
                    large_text="POLYBIUS II",
                )
            except Exception:
                pass

    def clear(self):
        if self.connected and self.rpc:
            try:
                self.rpc.clear()
            except Exception:
                pass