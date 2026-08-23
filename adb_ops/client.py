"""ADB 命令封装。"""

from __future__ import annotations

import subprocess
import time
from typing import Optional, Sequence

from config import (
    CREATE_NO_WINDOW,
    SCREENSHOT_DEVICE_PATH,
    SCREENSHOT_LOCAL_PATH,
)
from state import state
from vision.resolution import design_to_device, normalize_screenshot_to_base, parse_wm_size, set_device_resolution


class AdbClient:
    """基于当前 state.adb_path / state.port 执行 ADB 操作。"""

    def __init__(self, serial: Optional[str] = None) -> None:
        self._serial = serial

    @property
    def adb_path(self) -> str:
        return state.adb_path

    @property
    def serial(self) -> str:
        if self._serial:
            return self._serial
        return f"127.0.0.1:{state.port}"

    def run(self, args: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess:
        cmd = [self.adb_path, *args]
        if capture:
            # Windows 默认 GBK 无法解码部分 adb 输出，统一按 utf-8 容错解码
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
            )
        return subprocess.run(cmd, creationflags=CREATE_NO_WINDOW)

    def run_on_device(self, args: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess:
        return self.run(["-s", self.serial, *args], capture=capture)

    def refresh_resolution(self) -> tuple[int, int] | None:
        """读取模拟器分辨率并写入 state。"""
        result = self.run_on_device(["shell", "wm", "size"], capture=True)
        output = (result.stdout or "") + (result.stderr or "")
        size = parse_wm_size(output)
        if size:
            set_device_resolution(size[0], size[1])
            return state.screen_width, state.screen_height
        return None

    def tap(self, x: int | float | str, y: int | float | str, delay: float = 0.0) -> None:
        dx, dy = design_to_device(x, y)
        self.run_on_device(["shell", "input", "tap", str(dx), str(dy)])
        if delay:
            time.sleep(delay)

    def tap_without_serial(self, x: int | float | str, y: int | float | str, delay: float = 0.0) -> None:
        """部分场景（如拾取）原逻辑未指定 -s，保持兼容。"""
        dx, dy = design_to_device(x, y)
        self.run(["shell", "input", "tap", str(dx), str(dy)])
        if delay:
            time.sleep(delay)

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500,
        delay: float = 1.0,
    ) -> None:
        sx, sy = design_to_device(start_x, start_y)
        ex, ey = design_to_device(end_x, end_y)
        self.run_on_device(
            [
                "shell",
                "input",
                "swipe",
                str(sx),
                str(sy),
                str(ex),
                str(ey),
                str(duration),
            ]
        )
        if delay:
            time.sleep(delay)

    def drag_and_drop(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500,
        delay: float = 1.0,
    ) -> None:
        sx, sy = design_to_device(start_x, start_y)
        ex, ey = design_to_device(end_x, end_y)
        self.run_on_device(
            [
                "shell",
                "input",
                "draganddrop",
                str(sx),
                str(sy),
                str(ex),
                str(ey),
                str(duration),
            ]
        )
        if delay:
            time.sleep(delay)

    def swipe_with_hold(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500,
        hold_delay: float = 1.0,
        delay: float = 0.0,
    ) -> None:
        """按住 -> 移动 -> 停止并保持按住 -> 抬起。

        移动阶段分多段 MOVE 事件，确保拖动被识别；移动结束后保持按住
        hold_delay 时长，等地图惯性消退后再抬起，避免松手后继续滑动。
        依赖设备 `input motionevent` 子命令，需要 Android 9+。
        """
        sx, sy = design_to_device(start_x, start_y)
        ex, ey = design_to_device(end_x, end_y)
        self.run_on_device(["shell", "input", "motionevent", "DOWN", str(sx), str(sy)])
        steps = max(4, duration // 50)
        for i in range(1, steps + 1):
            time.sleep(duration / 1000.0 / steps)
            x = int(sx + (ex - sx) * i / steps)
            y = int(sy + (ey - sy) * i / steps)
            self.run_on_device(["shell", "input", "motionevent", "MOVE", str(x), str(y)])
        # 关键：停止移动后按住不抬，等地图惯性消退，避免松手后继续滑动
        if hold_delay:
            time.sleep(hold_delay)
        self.run_on_device(["shell", "input", "motionevent", "UP", str(ex), str(ey)])
        if delay:
            time.sleep(delay)

    def take_screenshot(self) -> None:
        self.run_on_device(["shell", "screencap", SCREENSHOT_DEVICE_PATH])
        print("已截图")
        self.run_on_device(["pull", SCREENSHOT_DEVICE_PATH, SCREENSHOT_LOCAL_PATH])
        print("已保存至本地")
        # 缩放到模板基准分辨率，识别与业务坐标统一按 1920x1080
        raw_w, raw_h = normalize_screenshot_to_base(SCREENSHOT_LOCAL_PATH)
        print(f"截图原始分辨率: {raw_w}x{raw_h}, 缩放比: {state.scale_x:.3f}/{state.scale_y:.3f}")

    def connect(self, port: str) -> str:
        result = self.run(["connect", f"127.0.0.1:{port}"], capture=True)
        return result.stdout or ""

    def devices(self) -> str:
        result = self.run(["devices"], capture=True)
        return result.stdout or ""

    def disconnect(self) -> None:
        self.run(["disconnect"], capture=True)

    def kill_server(self) -> None:
        """关闭本程序使用的 ADB server 进程。"""
        self.run(["kill-server"], capture=True)

    def shutdown(self) -> None:
        """断开连接并结束 ADB server。"""
        try:
            self.disconnect()
        except OSError:
            pass
        try:
            self.kill_server()
        except OSError:
            pass
        state.adb_connected = False
        state.adb_server_used = False
