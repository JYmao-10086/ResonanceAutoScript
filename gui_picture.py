"""
跑商助手入口。

启动：
    python gui_picture.py
"""

from __future__ import annotations

from config import DEFAULT_ADB_EXE
from gui.app import TradingAssistantApp
from state import state


def main() -> None:
    app = TradingAssistantApp()
    app.update_log(
        "注意：游戏分辨率设置为高，否则跑商助手将无法正常工作。"
    )
    app.update_log("ADB 将在开始跑商或手动重连时进行连接。")
    if not state.adb_path:
        state.adb_path = DEFAULT_ADB_EXE
    app.mainloop()


if __name__ == "__main__":
    main()
