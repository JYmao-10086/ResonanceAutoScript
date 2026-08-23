"""日志记录。"""

from __future__ import annotations

import os
import sys
import time
from typing import List

from config import ROOT_DIR

LOGS_DIR = os.path.join(ROOT_DIR, "logs")
FRONT_LOG_DIR = os.path.join(LOGS_DIR, "front")
BACK_LOG_DIR = os.path.join(LOGS_DIR, "back")


class LogRecorder:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.front_logs: List[str] = []
        self.back_logs: List[str] = []

    def add_front(self, message: str) -> None:
        self.front_logs.append(message.rstrip("\n"))

    def add_back(self, message: str) -> None:
        self.back_logs.append(message.rstrip("\n"))

    def save(self) -> None:
        self._save(FRONT_LOG_DIR, self.front_logs)
        self._save(BACK_LOG_DIR, self.back_logs)

    def _save(self, folder: str, lines: List[str]) -> None:
        if not lines:
            return
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(
            folder, time.strftime("%Y-%m-%d.log", time.localtime(self.start_time))
        )
        header = time.strftime(
            "[%Y-%m-%d %H:%M:%S]", time.localtime(self.start_time)
        )
        block = header + "\n" + "\n".join(lines)
        has_old = os.path.exists(path) and os.path.getsize(path) > 0
        with open(path, "a", encoding="utf-8") as f:
            if has_old:
                f.write("\n\n")
            f.write(block + "\n")


class StdoutCapture:
    def __init__(self, real_stream, recorder: LogRecorder) -> None:
        self._real = real_stream
        self._recorder = recorder

    def write(self, message: str) -> int:
        self._recorder.add_back(message)
        if self._real is None:
            return len(message)
        return self._real.write(message)

    def flush(self) -> None:
        if self._real is not None:
            self._real.flush()