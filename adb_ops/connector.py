"""模拟器 ADB 连接线程。"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Callable, Optional

from config import LDPLAYER_PORT, MUMU_PORT, NOX_PORT
from state import state
from vision.resolution import resolution_label
from .client import AdbClient

if TYPE_CHECKING:
    from gui.app import TradingAssistantApp


class RunAdb(threading.Thread):
    def __init__(
        self,
        app: "TradingAssistantApp",
        port: str = MUMU_PORT,
        on_finished: Optional[Callable[[bool], None]] = None,
    ) -> None:
        super().__init__(daemon=True)
        self.app = app
        self.port = port
        self.client = AdbClient()
        self.on_finished = on_finished

    def run(self) -> None:
        ok = self.connect(self.app)
        if self.on_finished is not None:
            self.on_finished(ok)

    def run_adb_command(self, command: list[str], app: "TradingAssistantApp") -> str:
        state.adb_server_used = True
        result = self.client.run(command, capture=True)
        if result.stderr:
            app.update_log("ADB命令执行出错: " + result.stderr)
        elif result.stdout is not None:
            app.update_log(result.stdout)
        return result.stdout or ""

    def connect_emulator(self, port: str = MUMU_PORT, app: "TradingAssistantApp | None" = None) -> str:
        assert app is not None
        return self.run_adb_command(["connect", f"127.0.0.1:{port}"], app)

    def check_connection(self, port: str = MUMU_PORT, app: "TradingAssistantApp | None" = None) -> bool:
        assert app is not None
        output = self.run_adb_command(["devices"], app)
        if output != "outline":
            return f"127.0.0.1:{port}" in output
        return False

    def connect(self, app: "TradingAssistantApp") -> bool:
        """尝试连接常见模拟器，成功返回 True。"""
        state.adb_connected = False

        if self.port == MUMU_PORT:
            candidates = [
                ("MuMu模拟器", MUMU_PORT),
                ("雷电模拟器", LDPLAYER_PORT),
                ("夜神模拟器", NOX_PORT),
            ]
        else:
            candidates = [(f"127.0.0.1:{self.port}", self.port)]
        for index, (name, port) in enumerate(candidates):
            if index > 0:
                app.update_log("连接失败")
            app.update_log(f"尝试连接到{name}...")
            state.port = port
            self.connect_emulator(port=port, app=app)
            if self.check_connection(port=port, app=app):
                state.adb_connected = True
                app.update_log(f"成功连接到{name}。")
                size = self.client.refresh_resolution()
                if size:
                    app.update_log(f"已识别模拟器分辨率: {resolution_label()}")
                else:
                    app.update_log(
                        "未能读取分辨率，将在首次截图时自动识别并缩放适配。"
                    )
                return True

        app.update_log("连接失败")
        state.adb_connected = False
        return False
