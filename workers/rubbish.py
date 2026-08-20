"""自动拾取线程。"""

from __future__ import annotations

import time

from adb_ops.client import AdbClient
from .base import ControllableThread


class PickUpRubbish(ControllableThread):
    def __init__(self) -> None:
        super().__init__()
        self.client = AdbClient()

    def run(self) -> None:
        while not self.stopped.is_set():
            if not self.should_continue():
                break
            self.pick_up_rubbish()

    def pick_up_rubbish(self) -> None:
        if not self.should_continue():
            return
        self.client.tap_without_serial(1151, 725, delay=0.1)
