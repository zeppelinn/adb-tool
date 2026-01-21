import flet as ft
import subprocess
import os
import sys
from datetime import datetime

TRANSLATIONS = {
    "zh": {
        "title": "ADB & Scrcpy 工具",
        "btn_connect": "连接",
        "btn_refresh": "刷新",
        "tab_devices": "设备",
        "tab_ops": "操作",
        "tab_logs": "日志",
        "msg_select_first": "请先选择设备！",
        "msg_scrcpy_error": "找不到 scrcpy.exe",
    },
    "en": {
        "title": "ADB & Scrcpy Tool",
        "btn_connect": "Connect",
        "btn_refresh": "Refresh",
        "tab_devices": "Devices",
        "tab_ops": "Operations",
        "tab_logs": "Capture",
        "msg_select_first": "Select a device first!",
        "msg_scrcpy_error": "scrcpy.exe not found",
    }
}

class AdbManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.adb_path = self.find_exe("adb.exe")
        self.scrcpy_path = self.find_exe("scrcpy.exe")
        self.current_device = None

    def find_exe(self, name):
        for p in [
            os.path.join(self.base_path, 'scrcpy-win64-v1.25', name),
            os.path.join(os.path.dirname(self.base_path), 'scrcpy-win64-v1.25', name),
            os.path.join(self.base_path, name), name
        ]:
            if os.path.exists(p): return p
        return name

    def run_cmd(self, args, use_device=True):
        cmd = [self.adb_path]
        if use_device and self.current_device:
            cmd.extend(["-s", self.current_device])
        cmd.extend(args)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, creationflags=0x08000000)
            return res.returncode == 0, res.stdout + res.stderr
        except Exception as e:
            return False, str(e)

def main(page: ft.Page):
    page.title = "ADB Tool"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    lang = "zh"
    base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    adb_mgr = AdbManager(base_path)
    current_tab = 0

    def t(key): return TRANSLATIONS[lang].get(key, key)

    console = ft.ListView(expand=True, spacing=5, auto_scroll=True)

    def log(msg, is_error=False):
        ts = datetime.now().strftime("%H:%M:%S")
        console.controls.append(ft.Text(f"[{ts}] {msg}", color=ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400, size=12))
        page.update()

    device_rows = ft.Column(spacing=5)

    def refresh_devices(e=None):
        success, out = adb_mgr.run_cmd(["devices", "-l"], use_device=False)
        device_rows.controls.clear()
        for line in out.strip().split('\n')[1:]:
            if not line.strip(): continue
            parts = line.split()
            sn, status = parts[0], parts[1]
            is_sel = sn == adb_mgr.current_device

            def make_click(s):
                def h(e):
                    adb_mgr.current_device = s
                    refresh_devices()
                    log(f"Selected: {s}")
                return h

            device_rows.controls.append(ft.Container(
                content=ft.Row([
                    ft.Icon("check_circle" if is_sel else "circle_outlined", color=ft.Colors.BLUE if is_sel else None, size=20),
                    ft.Text(sn, weight=ft.FontWeight.BOLD if is_sel else None, expand=True),
                    ft.Text("TCP" if ":" in sn else "USB", size=12),
                    ft.Text(status, color=ft.Colors.GREEN if status == "device" else ft.Colors.RED, size=12),
                ]),
                padding=8, border_radius=6,
                bgcolor=ft.Colors.BLUE_50 if is_sel else None,
                on_click=make_click(sn),
            ))
        page.update()

    def on_connect(e):
        addr = f"{ip_input.value}:{port_input.value or '5555'}"
        _, out = adb_mgr.run_cmd(["connect", addr], use_device=False)
        log(out.strip())
        refresh_devices()

    def on_action(args):
        if not adb_mgr.current_device: return log(t("msg_select_first"), True)
        _, out = adb_mgr.run_cmd(args)
        log(out.strip() or "OK")

    def on_scrcpy(e):
        if not adb_mgr.current_device: return log(t("msg_select_first"), True)
        if not os.path.exists(adb_mgr.scrcpy_path): return log(t("msg_scrcpy_error"), True)
        subprocess.Popen([adb_mgr.scrcpy_path, "-s", adb_mgr.current_device], cwd=os.path.dirname(adb_mgr.scrcpy_path), creationflags=0x10)
        log(f"Scrcpy: {adb_mgr.current_device}")

    def on_capture(log_type):
        if not adb_mgr.current_device: return log(t("msg_select_first"), True)
        dir_path = os.path.join(base_path, "logs", adb_mgr.current_device.replace(":", "_"))
        os.makedirs(dir_path, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if log_type in ["logcat", "dmesg"]:
            fp = os.path.join(dir_path, f"{ts}_{log_type}.txt")
            _, out = adb_mgr.run_cmd([log_type, "-d"] if log_type == "logcat" else ["shell", "dmesg"])
            with open(fp, "w", encoding="utf-8") as f: f.write(out)
            log(f"Saved: {fp}")
        else:
            fp = os.path.join(dir_path, f"{ts}_{log_type}")
            os.makedirs(fp, exist_ok=True)
            adb_mgr.run_cmd(["pull", "/data/tombstones" if log_type == "tombstones" else "/data/anr", fp])
            log(f"Pulled: {fp}")

    ip_input = ft.TextField(hint_text="192.168.1.100", expand=True, height=40)
    port_input = ft.TextField(hint_text="5555", value="5555", width=80, height=40)

    # 三个面板
    panel_devices = ft.Container(content=ft.Column([device_rows], scroll=ft.ScrollMode.AUTO, expand=True), expand=True)
    panel_ops = ft.Container(content=ft.Column([
        ft.Row([
            ft.FilledButton("Root", on_click=lambda _: on_action(["root"])),
            ft.FilledButton("Remount", on_click=lambda _: on_action(["remount"])),
            ft.FilledButton("Settings", on_click=lambda _: on_action(["shell", "am", "start", "-n", "com.android.settings/.Settings"])),
        ], spacing=10, wrap=True),
        ft.Row([
            ft.FilledButton("Scrcpy", on_click=on_scrcpy, bgcolor=ft.Colors.GREEN_700),
            ft.FilledButton("Reboot", on_click=lambda _: on_action(["reboot"]), bgcolor=ft.Colors.ORANGE_700),
        ], spacing=10),
        ft.Row([
            ft.TextButton(content=ft.Text("Enable Launcher"), on_click=lambda _: on_action(["shell", "pm", "enable", "com.android.launcher3"])),
            ft.TextButton(content=ft.Text("Disable Launcher"), on_click=lambda _: on_action(["shell", "pm", "disable", "com.android.launcher3"])),
        ], spacing=10),
    ], spacing=15), padding=10, expand=True, visible=False)
    panel_logs = ft.Container(content=ft.Row([
        ft.FilledButton("Logcat", on_click=lambda _: on_capture("logcat")),
        ft.FilledButton("Dmesg", on_click=lambda _: on_capture("dmesg")),
        ft.FilledButton("Tombstones", on_click=lambda _: on_capture("tombstones")),
        ft.FilledButton("ANR", on_click=lambda _: on_capture("anr")),
    ], spacing=10, wrap=True), padding=10, expand=True, visible=False)

    panels = [panel_devices, panel_ops, panel_logs]

    def switch_tab(idx):
        nonlocal current_tab
        current_tab = idx
        for i, p in enumerate(panels): p.visible = (i == idx)
        for i, b in enumerate(tab_btns): b.style = ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100 if i == idx else None)
        page.update()

    tab_btns = [
        ft.TextButton(content=ft.Text(t("tab_devices")), on_click=lambda _: switch_tab(0)),
        ft.TextButton(content=ft.Text(t("tab_ops")), on_click=lambda _: switch_tab(1)),
        ft.TextButton(content=ft.Text(t("tab_logs")), on_click=lambda _: switch_tab(2)),
    ]

    def toggle_lang(e):
        nonlocal lang
        lang = "en" if lang == "zh" else "zh"
        lang_btn.content = ft.Text("EN" if lang == "zh" else "中")
        page.update()

    lang_btn = ft.TextButton(content=ft.Text("EN"), on_click=toggle_lang)

    page.add(
        ft.Row([ft.Text("ADB TOOL", size=24, weight=ft.FontWeight.BOLD), ft.Container(expand=True), lang_btn]),
        ft.Row([ip_input, port_input,
            ft.FilledButton(t("btn_connect"), on_click=on_connect),
            ft.OutlinedButton(content=ft.Text(t("btn_refresh")), on_click=refresh_devices),
        ], spacing=10),
        ft.Row(tab_btns, spacing=5),
        ft.Container(content=ft.Stack(panels), expand=True, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=8),
        ft.Text("Console", size=14, weight=ft.FontWeight.BOLD),
        ft.Container(content=console, bgcolor=ft.Colors.BLACK87, border_radius=8, padding=10, height=150),
    )

    switch_tab(0)
    refresh_devices()

ft.app(target=main)
