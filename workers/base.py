"""可暂停/停止的工作线程基类。"""

from __future__ import annotations

import threading


class ControllableThread(threading.Thread):
    """提供 stop / pause / resume 与等待循环。"""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.stopped = threading.Event()
        self.paused = threading.Event()
        self.paused.set()

    def stop(self) -> None:
        self.stopped.set()

    def pause(self) -> None:
        self.paused.clear()

    def resume(self) -> None:
        self.paused.set()

    def wait_if_paused(self) -> bool:
        """
        若已暂停则阻塞等待恢复。
        返回 True 表示应继续执行；False 表示已停止。
        """
        while not self.paused.is_set():
            self.paused.wait()
            if self.stopped.is_set():
                return False
        return not self.stopped.is_set()

    def should_continue(self) -> bool:
        """未停止且处理完暂停后返回 True。"""
        if self.stopped.is_set():
            return False
        return self.wait_if_paused()
