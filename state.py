"""运行时共享状态（替代散落的全局变量）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from config import BASE_HEIGHT, BASE_WIDTH, DEFAULT_ADB_EXE, MUMU_PORT

if TYPE_CHECKING:
    from workers.rubbish import PickUpRubbish
    from workers.trading import TradingThread


class AppState:
    """进程内可变状态。"""

    def __init__(self) -> None:
        self.port: str = MUMU_PORT
        self.adb_path: str = DEFAULT_ADB_EXE
        self.adb_connected: bool = False
        self.adb_server_used: bool = False
        # 设备实际分辨率（默认等于模板基准）
        self.screen_width: int = BASE_WIDTH
        self.screen_height: int = BASE_HEIGHT
        self.scale_x: float = 1.0
        self.scale_y: float = 1.0
        self.trading_thread: Optional["TradingThread"] = None
        self.catch_rubbish: Optional["PickUpRubbish"] = None


# 单例，供各模块读写
state = AppState()
