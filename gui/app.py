"""跑商助手主窗口（CustomTkinter）。"""

from __future__ import annotations

import os
import threading
import tkinter as tk

import customtkinter as ctk

from adb_ops.client import AdbClient
from adb_ops.connector import RunAdb
from config import DEFAULT_ADB_DIR, ICON_PATH
from data import cleaned_merchandises, load_cities
from state import state
from workers.trading import TradingThread
from . import settings as settings_io

# 浅色简洁主题
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

BTN_W = 118
ENTRY_W = 100
COMBO_W = 220
CONTROL_W = 420


def set_enabled(widget, enabled: bool) -> None:
    widget.configure(state="normal" if enabled else "disabled")


def style_tabview(tabview: ctk.CTkTabview) -> None:
    """让标签页更醒目。"""
    tabview.configure(
        border_width=1,
        border_color=("#C5CDD8", "#3A3A3A"),
        segmented_button_fg_color=("#D7DEE8", "#2B2B2B"),
        segmented_button_selected_color=("#2F6FED", "#1F5AD9"),
        segmented_button_selected_hover_color=("#255CC7", "#1A4FBF"),
        segmented_button_unselected_color=("#E8EEF5", "#333333"),
        segmented_button_unselected_hover_color=("#D5DDE8", "#3D3D3D"),
        text_color=("#1F2933", "#F5F5F5"),
        segmented_button_font=ctk.CTkFont(size=14, weight="bold"),
    )


class TradingAssistantApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.cities = load_cities()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.title("跑商助手")
        self.geometry("1080x700")
        self.minsize(960, 620)
        try:
            self.iconbitmap(ICON_PATH)
        except tk.TclError:
            pass

        self._init_vars()
        self.create_widgets()
        settings_io.load_settings(self)
        self._sync_comboboxes_from_vars()

    def _init_vars(self) -> None:
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.round_trip_times_var = tk.StringVar(value="9999")
        self.lollipop_var = tk.StringVar(value="0")
        self.gum_var = tk.StringVar(value="0")
        self.lighter_var = tk.StringVar(value="0")
        self.birch_stone_var = tk.StringVar(value="0")
        self.fatigue_recovery_var = tk.BooleanVar(value=False)
        self.auto_catch = tk.BooleanVar(value=False)
        self.adb_location = tk.StringVar()

        for var in (
            self.round_trip_times_var,
            self.lollipop_var,
            self.gum_var,
            self.lighter_var,
            self.birch_stone_var,
        ):
            self._bind_digits_only(var)

    def _bind_digits_only(self, var: tk.StringVar) -> None:
        def _on_write(*_args) -> None:
            value = var.get()
            filtered = "".join(ch for ch in value if ch.isdigit())
            if filtered != value:
                var.set(filtered)

        var.trace_add("write", _on_write)

    def create_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        style_tabview(self.tabview)
        self.tabview.add("跑商")
        self.tabview.add("交易所设置")
        self.tabview.add("连接设置")

        self._build_trading_tab(self.tabview.tab("跑商"))
        self._build_exchange_tab(self.tabview.tab("交易所设置"))
        self._build_connect_tab(self.tabview.tab("连接设置"))

    def _build_trading_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=0)
        parent.grid_rowconfigure(0, weight=1)

        log_card = ctk.CTkFrame(parent, corner_radius=10)
        log_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=4)
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_card, text="运行日志", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.log_text = ctk.CTkTextbox(log_card, font=ctk.CTkFont(size=13), wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")

        # 右侧用可滚动面板，避免控件被裁切
        control = ctk.CTkScrollableFrame(parent, corner_radius=10, width=CONTROL_W)
        control.grid(row=0, column=1, sticky="ns", pady=4)
        control.grid_columnconfigure(0, weight=1)

        section_font = ctk.CTkFont(size=14, weight="bold")
        label_font = ctk.CTkFont(size=13)
        city_names = list(self.cities.keys()) or [""]

        ctk.CTkLabel(control, text="跑商控制", font=section_font).grid(
            row=0, column=0, sticky="w", padx=12, pady=(8, 10)
        )

        # 起点 / 终点各占一行，避免挤出视口
        route = ctk.CTkFrame(control, fg_color="transparent")
        route.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        route.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(route, text="起点", font=label_font, width=56, anchor="w").grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.start_combobox = ctk.CTkComboBox(
            route,
            values=city_names,
            variable=self.start_var,
            width=COMBO_W,
            state="readonly",
            dropdown_font=ctk.CTkFont(size=13),
        )
        self.start_combobox.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)

        ctk.CTkLabel(route, text="终点", font=label_font, width=56, anchor="w").grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.end_combobox = ctk.CTkComboBox(
            route,
            values=city_names,
            variable=self.end_var,
            width=COMBO_W,
            state="readonly",
            dropdown_font=ctk.CTkFont(size=13),
        )
        self.end_combobox.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=6)

        times_row = ctk.CTkFrame(control, fg_color="transparent")
        times_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        ctk.CTkLabel(times_row, text="双程次数", font=label_font, width=56, anchor="w").pack(
            side="left"
        )
        ctk.CTkEntry(times_row, textvariable=self.round_trip_times_var, width=ENTRY_W).pack(
            side="left", padx=(8, 0)
        )

        action_row = ctk.CTkFrame(control, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.round_trip_button = ctk.CTkButton(
            action_row, text="双程跑商", width=BTN_W, command=self.on_round_trip
        )
        self.round_trip_button.pack(side="left", padx=(0, 8))
        self.one_way_button = ctk.CTkButton(
            action_row, text="单程跑商", width=BTN_W, command=self.on_one_way_trip
        )
        self.one_way_button.pack(side="left")

        control_row = ctk.CTkFrame(control, fg_color="transparent")
        control_row.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 4))
        self.stop_trading_button = ctk.CTkButton(
            control_row,
            text="停止",
            width=90,
            fg_color="#C0392B",
            hover_color="#A93226",
            command=self.on_stop_trading,
        )
        self.stop_trading_button.pack(side="left", padx=(0, 8))
        self.pause_trading_button = ctk.CTkButton(
            control_row, text="暂停", width=90, command=self.on_pause_trading
        )
        self.pause_trading_button.pack(side="left", padx=(0, 8))
        self.resume_trading_button = ctk.CTkButton(
            control_row, text="恢复", width=90, command=self.on_resume_trading
        )
        self.resume_trading_button.pack(side="left", padx=(0, 8))
        self.stop_when_finished_button = ctk.CTkButton(
            control_row, text="该趟后停", width=100, command=self.stop_when_finished
        )
        self.stop_when_finished_button.pack(side="left")

        for btn in (
            self.stop_trading_button,
            self.pause_trading_button,
            self.resume_trading_button,
            self.stop_when_finished_button,
        ):
            set_enabled(btn, False)

        # 控制区与补给区分隔线
        ctk.CTkFrame(control, height=2, fg_color=("#C5CDD8", "#4A4A4A")).grid(
            row=5, column=0, sticky="ew", padx=12, pady=(16, 12)
        )

        ctk.CTkLabel(control, text="补给道具", font=section_font).grid(
            row=6, column=0, sticky="w", padx=12, pady=(0, 8)
        )

        supply = ctk.CTkFrame(control, fg_color="transparent")
        supply.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 6))
        supply.grid_columnconfigure(1, weight=1)
        supply.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(supply, text="棒棒糖", font=label_font, width=56, anchor="w").grid(
            row=0, column=0, sticky="w", pady=6
        )
        ctk.CTkEntry(supply, textvariable=self.lollipop_var, width=ENTRY_W).grid(
            row=0, column=1, sticky="w", padx=(6, 16), pady=6
        )
        ctk.CTkLabel(supply, text="口香糖", font=label_font, width=56, anchor="w").grid(
            row=0, column=2, sticky="w", pady=6
        )
        ctk.CTkEntry(supply, textvariable=self.gum_var, width=ENTRY_W).grid(
            row=0, column=3, sticky="w", padx=(6, 0), pady=6
        )

        ctk.CTkLabel(supply, text="跳糖", font=label_font, width=56, anchor="w").grid(
            row=1, column=0, sticky="w", pady=6
        )
        ctk.CTkEntry(supply, textvariable=self.lighter_var, width=ENTRY_W).grid(
            row=1, column=1, sticky="w", padx=(6, 16), pady=6
        )
        ctk.CTkLabel(supply, text="桦石", font=label_font, width=56, anchor="w").grid(
            row=1, column=2, sticky="w", pady=6
        )
        ctk.CTkEntry(supply, textvariable=self.birch_stone_var, width=ENTRY_W).grid(
            row=1, column=3, sticky="w", padx=(6, 0), pady=6
        )

        checks = ctk.CTkFrame(control, fg_color="transparent")
        checks.grid(row=8, column=0, sticky="ew", padx=12, pady=(8, 16))
        ctk.CTkCheckBox(checks, text="疲劳恢复", variable=self.fatigue_recovery_var).pack(
            side="left", padx=(0, 18)
        )
        ctk.CTkCheckBox(checks, text="自动拾取", variable=self.auto_catch).pack(side="left")

    def _build_exchange_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        self.city_tabs = ctk.CTkTabview(parent, corner_radius=8)
        self.city_tabs.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        style_tabview(self.city_tabs)

        self.merchandise_vars = {}
        self.fill_merchandise_vars = {}
        self.bargain_times_vars = {}
        self.bargain_success_vars = {}
        self.raise_price_times_vars = {}
        self.raise_price_success_vars = {}
        self.purchase_book_vars = {}

        for city in self.cities:
            tab = self.city_tabs.add(city)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_columnconfigure(1, weight=1)
            tab.grid_rowconfigure(0, weight=1)

            left = ctk.CTkScrollableFrame(tab, corner_radius=8)
            left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)
            right = ctk.CTkFrame(tab, corner_radius=8)
            right.grid(row=0, column=1, sticky="nsew", pady=4)

            ctk.CTkLabel(left, text="购买商品", font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 6)
            )

            self.merchandise_vars[city] = {}
            self.fill_merchandise_vars[city] = tk.StringVar(value="")
            items = cleaned_merchandises(self.cities[city])
            row_i = 1
            for i, option in enumerate(items):
                if option == "nan":
                    continue
                self.merchandise_vars[city][option] = tk.BooleanVar(value=False)
                ctk.CTkCheckBox(
                    left, text=option, variable=self.merchandise_vars[city][option]
                ).grid(row=1 + i // 2, column=i % 2, sticky="w", padx=8, pady=3)
                row_i = 1 + i // 2

            ctk.CTkLabel(left, text="填补商品").grid(
                row=row_i + 1, column=0, sticky="w", padx=8, pady=(10, 6)
            )
            ctk.CTkComboBox(
                left,
                values=[""] + items,
                variable=self.fill_merchandise_vars[city],
                width=160,
                state="readonly",
            ).grid(row=row_i + 1, column=1, sticky="w", padx=8, pady=(10, 6))

            self.bargain_times_vars[city] = tk.StringVar(value="0")
            self.bargain_success_vars[city] = tk.StringVar(value="0")
            self.raise_price_times_vars[city] = tk.StringVar(value="0")
            self.raise_price_success_vars[city] = tk.StringVar(value="0")
            self.purchase_book_vars[city] = tk.StringVar(value="0")
            for var in (
                self.bargain_times_vars[city],
                self.bargain_success_vars[city],
                self.raise_price_times_vars[city],
                self.raise_price_success_vars[city],
                self.purchase_book_vars[city],
            ):
                self._bind_digits_only(var)

            ctk.CTkLabel(right, text="交易参数", font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8)
            )

            fields = [
                ("砍价次数", self.bargain_times_vars[city]),
                ("砍价成功次数", self.bargain_success_vars[city]),
                ("抬价次数", self.raise_price_times_vars[city]),
                ("抬价成功次数", self.raise_price_success_vars[city]),
                ("进货采买书", self.purchase_book_vars[city]),
            ]
            for idx, (label, var) in enumerate(fields):
                ctk.CTkLabel(right, text=label).grid(
                    row=1 + idx, column=0, sticky="w", padx=14, pady=6
                )
                ctk.CTkEntry(right, textvariable=var, width=120).grid(
                    row=1 + idx, column=1, sticky="w", padx=8, pady=6
                )

    def _build_connect_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=0)
        parent.grid_rowconfigure(0, weight=1)

        log_card = ctk.CTkFrame(parent, corner_radius=10)
        log_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_card, text="连接日志", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.connect_log_text = ctk.CTkTextbox(log_card, font=ctk.CTkFont(size=13), wrap="word")
        self.connect_log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.connect_log_text.configure(state="disabled")

        control = ctk.CTkFrame(parent, corner_radius=10, width=380)
        control.grid(row=0, column=1, sticky="ns", pady=4)
        control.grid_propagate(False)

        ctk.CTkLabel(control, text="ADB 连接", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 8)
        )
        ctk.CTkLabel(control, text="adb 目录").grid(row=1, column=0, sticky="w", padx=14, pady=4)
        ctk.CTkEntry(control, textvariable=self.adb_location, width=300).grid(
            row=2, column=0, sticky="w", padx=14, pady=4
        )
        self.connect_adb_button = ctk.CTkButton(
            control, text="重新连接 ADB", width=160, command=self.connect_adb
        )
        self.connect_adb_button.grid(row=3, column=0, sticky="w", padx=14, pady=(12, 14))

    def _sync_comboboxes_from_vars(self) -> None:
        if self.start_var.get():
            self.start_combobox.set(self.start_var.get())
        if self.end_var.get():
            self.end_combobox.set(self.end_var.get())

    def _resolve_adb_path(self) -> None:
        adb_location = self.adb_location.get().strip()
        if adb_location == "":
            self.update_log("adb 目录为空，使用默认路径。")
            adb_location = DEFAULT_ADB_DIR
        state.adb_path = os.path.join(adb_location, "adb.exe")
        print(state.adb_path)

    def _begin_adb_connect(self, on_finished=None) -> None:
        """后台发起 ADB 连接。"""
        self._resolve_adb_path()
        RunAdb(self, on_finished=on_finished).start()

    def connect_adb(self) -> None:
        """连接设置页：手动重连 ADB。"""
        set_enabled(self.connect_adb_button, False)
        self.update_log("正在重新连接 ADB...\n")

        def worker() -> None:
            try:
                if state.adb_server_used:
                    AdbClient().disconnect()
                    state.adb_connected = False
                    self.after(0, lambda: self.update_log("当前 ADB 连接已断开。\n"))
            except OSError as e:
                print(f"Error disconnecting ADB: {e}")

            def on_finished(ok: bool) -> None:
                self.after(0, lambda: self._on_manual_connect_finished(ok))

            self._begin_adb_connect(on_finished=on_finished)

        threading.Thread(target=worker, daemon=True).start()

    def _on_manual_connect_finished(self, ok: bool) -> None:
        set_enabled(self.connect_adb_button, True)
        if ok:
            self.update_log("ADB 重连完成。\n")
        else:
            self.update_log("ADB 重连失败，请检查模拟器与 adb 路径。\n")

    def on_validate(self, P: str) -> bool:
        return P.strip() == "" or P.isdigit()

    def _set_trading_controls_busy(self, busy: bool) -> None:
        set_enabled(self.round_trip_button, not busy)
        set_enabled(self.one_way_button, not busy)
        if busy:
            set_enabled(self.stop_trading_button, False)
            set_enabled(self.pause_trading_button, False)
            set_enabled(self.resume_trading_button, False)
            set_enabled(self.stop_when_finished_button, False)

    def _launch_trading_thread(
        self, times: str | int, start: str, end: str
    ) -> None:
        set_enabled(self.round_trip_button, False)
        set_enabled(self.one_way_button, False)
        set_enabled(self.stop_trading_button, True)
        set_enabled(self.pause_trading_button, True)
        set_enabled(self.stop_when_finished_button, True)

        trading_thread = TradingThread(
            self,
            start,
            end,
            times,
            self.lollipop_var.get(),
            self.gum_var.get(),
            self.lighter_var.get(),
            self.birch_stone_var.get(),
            self.fatigue_recovery_var.get(),
        )
        state.trading_thread = trading_thread
        trading_thread.start()

    def _start_trading(self, times: str | int, start: str, end: str) -> None:
        """开始跑商前先确保 ADB 已连接。"""
        self._set_trading_controls_busy(True)

        def on_finished(ok: bool) -> None:
            self.after(0, lambda: self._on_trading_connect_finished(ok, times, start, end))

        if state.adb_connected:
            self._launch_trading_thread(times, start, end)
            return

        self.update_log("开始跑商前正在连接 ADB...\n")
        self._begin_adb_connect(on_finished=on_finished)

    def _on_trading_connect_finished(
        self, ok: bool, times: str | int, start: str, end: str
    ) -> None:
        if not ok:
            self.update_log("ADB 连接失败，无法开始跑商。\n")
            self._set_trading_controls_busy(False)
            return
        self._launch_trading_thread(times, start, end)
    def on_round_trip(self) -> None:
        start = self.start_combobox.get()
        end = self.end_combobox.get()
        times = self.round_trip_times_var.get()
        if start == "" or end == "":
            self.update_log("起点或终点请勿为空")
            return
        self.update_log(f"起点：{start}\n终点：{end}\n往返次数：{times}次\n")
        self._start_trading(times, start, end)

    def on_one_way_trip(self) -> None:
        start = self.start_combobox.get()
        end = self.end_combobox.get()
        if start == "" or end == "":
            self.update_log("起点或终点请勿为空")
            return
        self.update_log(f"起点：{start}\n终点：{end}\n")
        self._start_trading(1, start, end)

    def on_stop_trading(self) -> None:
        self.update_log("停止跑商\n")
        if state.trading_thread is not None:
            state.trading_thread.resume()
            state.trading_thread.stop()
        if state.catch_rubbish is not None and state.catch_rubbish.is_alive():
            state.catch_rubbish.resume()
            state.catch_rubbish.stop()
        set_enabled(self.stop_trading_button, False)
        set_enabled(self.pause_trading_button, False)
        set_enabled(self.resume_trading_button, False)
        set_enabled(self.stop_when_finished_button, False)
        set_enabled(self.round_trip_button, True)
        set_enabled(self.one_way_button, True)

    def on_pause_trading(self) -> None:
        self.update_log("暂停跑商\n")
        if state.trading_thread is not None:
            state.trading_thread.pause()
        if state.catch_rubbish is not None and state.catch_rubbish.is_alive():
            state.catch_rubbish.pause()
        set_enabled(self.pause_trading_button, False)
        set_enabled(self.resume_trading_button, True)

    def on_resume_trading(self) -> None:
        self.update_log("恢复跑商\n")
        if state.trading_thread is not None:
            state.trading_thread.resume()
        if state.catch_rubbish is not None and state.catch_rubbish.is_alive():
            state.catch_rubbish.resume()
        set_enabled(self.pause_trading_button, True)
        set_enabled(self.resume_trading_button, False)

    def stop_when_finished(self) -> None:
        if state.trading_thread is not None and state.trading_thread.is_alive():
            self.update_log("完成此次跑商后停止跑商\n")
            state.trading_thread.stop_when_finished()
            set_enabled(self.stop_when_finished_button, False)

    def update_log(self, message: str) -> None:
        for box in (self.log_text, self.connect_log_text):
            box.configure(state="normal")
            box.insert("end", message + "\n")
            box.see("end")
            box.configure(state="disabled")

    def save_settings(self) -> None:
        settings_io.save_settings(self)

    def load_settings(self) -> None:
        settings_io.load_settings(self)
        self._sync_comboboxes_from_vars()

    def on_close(self) -> None:
        if state.trading_thread is not None and state.trading_thread.is_alive():
            state.trading_thread.resume()
            state.trading_thread.stop()
        if state.catch_rubbish is not None and state.catch_rubbish.is_alive():
            state.catch_rubbish.resume()
            state.catch_rubbish.stop()
        self.save_settings()
        if state.adb_server_used:
            try:
                AdbClient().shutdown()
                print("ADB server 已关闭。")
            except OSError as e:
                print(f"关闭 ADB 失败: {e}")
        self.destroy()
