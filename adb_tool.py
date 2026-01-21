import flet as ft
import subprocess
import os
import sys
from datetime import datetime

# --- 国际化配置 ---
TRANSLATIONS = {
    "zh": {
        "title": "ADB & Scrcpy 极简工具",
        "ip_hint": "IP 地址",
        "port_hint": "端口",
        "btn_connect": "连接",
        "btn_refresh": "刷新列表",
        "tab_devices": "设备列表",
        "tab_ops": "快捷操作",
        "tab_logs": "日志抓取",
        "col_sn": "序列号/IP",
        "col_type": "类型",
        "col_status": "状态",
        "msg_select_first": "请先选择一个设备！",
        "msg_scrcpy_error": "找不到 scrcpy.exe",
    },
    "en": {
        "title": "ADB & Scrcpy Tool",
        "ip_hint": "IP Address",
        "port_hint": "Port",
        "btn_connect": "Connect",
        "btn_refresh": "Refresh",
        "tab_devices": "Devices",
        "tab_ops": "Operations",
        "tab_logs": "Capture",
        "col_sn": "Serial/IP",
        "col_type": "Type",
        "col_status": "Status",
        "msg_select_first": "Please select a device first!",
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
        search_paths = [
            os.path.join(self.base_path, 'scrcpy-win64-v1.25', name),
            os.path.join(os.path.dirname(self.base_path), 'scrcpy-win64-v1.25', name),
            os.path.join(self.base_path, name),
            name
        ]
        for p in search_paths:
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
    page.title = "ADB & Scrcpy Tool"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 800
    page.padding = 20

    lang = "zh"
    base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    adb_mgr = AdbManager(base_path)

    def t(key):
        return TRANSLATIONS[lang].get(key, key)

    console = ft.ListView(expand=True, spacing=5, auto_scroll=True)

    def log(msg, is_error=False):
        ts = datetime.now().strftime("%H:%M:%S")
        color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400
        console.controls.append(ft.Text(f"[{ts}] {msg}", color=color, size=13))
        page.update()

    device_rows = ft.Column()

    def refresh_devices(e=None):
        success, out = adb_mgr.run_cmd(["devices", "-l"], use_device=False)
        device_rows.controls.clear()
        lines = out.strip().split('\n')[1:]
        for line in lines:
            if not line.strip(): continue
            parts = line.split()
            sn, status = parts[0], parts[1]
            is_selected = sn == adb_mgr.current_device

            def make_select(s):
                def handler(e):
                    adb_mgr.current_device = s
                    refresh_devices()
                    log(f"Selected: {s}")
                return handler

            device_rows.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon("check_circle" if is_selected else "circle_outlined", color=ft.Colors.BLUE if is_selected else None),
                        ft.Text(sn, weight=ft.FontWeight.BOLD if is_selected else None, expand=True),
                        ft.Text("TCP/IP" if ":" in sn else "USB"),
                        ft.Text(status, color=ft.Colors.GREEN if status == "device" else ft.Colors.RED),
                    ]),
                    padding=10,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50 if is_selected else None,
                    on_click=make_select(sn),
                )
            )
        if not adb_mgr.current_device and lines:
            first = lines[0].split()
            if first: adb_mgr.current_device = first[0]
        page.update()

    def on_connect(e):
        addr = f"{ip_input.value}:{port_input.value or '5555'}"
        success, out = adb_mgr.run_cmd(["connect", addr], use_device=False)
        log(out.strip())
        refresh_devices()

    def on_action(args):
        if not adb_mgr.current_device:
            log(t("msg_select_first"), True)
            return
        success, out = adb_mgr.run_cmd(args)
        log(out.strip() or "Success")

    def on_scrcpy(e):
        if not adb_mgr.current_device: return log(t("msg_select_first"), True)
        if not os.path.exists(adb_mgr.scrcpy_path): return log(t("msg_scrcpy_error"), True)
        subprocess.Popen([adb_mgr.scrcpy_path, "-s", adb_mgr.current_device],
                         cwd=os.path.dirname(adb_mgr.scrcpy_path), creationflags=0x00000010)
        log(f"Scrcpy started for {adb_mgr.current_device}")

    def on_capture(log_type):
        if not adb_mgr.current_device: return log(t("msg_select_first"), True)
        sn_dir = adb_mgr.current_device.replace(":", "_")
        dir_path = os.path.join(base_path, "logs", sn_dir)
        os.makedirs(dir_path, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if log_type in ["logcat", "dmesg"]:
            file_path = os.path.join(dir_path, f"{ts}_{log_type}.txt")
            success, out = adb_mgr.run_cmd([log_type, "-d"] if log_type == "logcat" else ["shell", "dmesg"])
            with open(file_path, "w", encoding="utf-8") as f: f.write(out)
            log(f"Saved: {file_path}")
        else:
            folder_path = os.path.join(dir_path, f"{ts}_{log_type}")
            os.makedirs(folder_path, exist_ok=True)
            remote = "/data/tombstones" if log_type == "tombstones" else "/data/anr"
            success, out = adb_mgr.run_cmd(["pull", remote, folder_path])
            log(f"Pulled to: {folder_path}")

    ip_input = ft.TextField(label=t("ip_hint"), hint_text="192.168.1.100", expand=True)
    port_input = ft.TextField(label=t("port_hint"), value="5555", width=100)

    def toggle_lang(e):
        nonlocal lang
        lang = "en" if lang == "zh" else "zh"
        page.title = t("title")
        lang_btn.content = ft.Text("English" if lang == "zh" else "中文")
        page.update()

    lang_btn = ft.TextButton(content=ft.Text("English"), on_click=toggle_lang)

    # Tabs content
    tab_devices = ft.Container(content=ft.Column([device_rows], scroll=ft.ScrollMode.AUTO), padding=10)

    tab_ops = ft.Container(content=ft.Column([
        ft.Row([
            ft.Button(content=ft.Text("Root"), on_click=lambda _: on_action(["root"])),
            ft.Button(content=ft.Text("Remount"), on_click=lambda _: on_action(["remount"])),
            ft.Button(content=ft.Text("Settings"), on_click=lambda _: on_action(["shell", "am", "start", "-n", "com.android.settings/.Settings"])),
        ], spacing=10),
        ft.Row([
            ft.Button(content=ft.Text("Scrcpy"), on_click=on_scrcpy, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ft.Button(content=ft.Text("Reboot"), on_click=lambda _: on_action(["reboot"]), bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
        ], spacing=10),
        ft.Row([
            ft.TextButton(content=ft.Text("Enable Launcher"), on_click=lambda _: on_action(["shell", "pm", "enable", "com.android.launcher3"])),
            ft.TextButton(content=ft.Text("Disable Launcher"), on_click=lambda _: on_action(["shell", "pm", "disable", "com.android.launcher3"])),
        ], spacing=10),
    ], spacing=20), padding=20)

    tab_logs = ft.Container(content=ft.Row([
        ft.Button(content=ft.Row([ft.Icon("description"), ft.Text("Logcat")]), on_click=lambda _: on_capture("logcat")),
        ft.Button(content=ft.Row([ft.Icon("bug_report"), ft.Text("Dmesg")]), on_click=lambda _: on_capture("dmesg")),
        ft.Button(content=ft.Row([ft.Icon("folder_zip"), ft.Text("Tombstones")]), on_click=lambda _: on_capture("tombstones")),
        ft.Button(content=ft.Row([ft.Icon("error_outline"), ft.Text("ANR")]), on_click=lambda _: on_capture("anr")),
    ], spacing=10), padding=20)

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text=t("tab_devices"), content=tab_devices),
            ft.Tab(text=t("tab_ops"), content=tab_ops),
            ft.Tab(text=t("tab_logs"), content=tab_logs),
        ],
        expand=True,
    )

    page.add(
        ft.Row([ft.Text("ADB TOOL", size=28, weight=ft.FontWeight.BOLD), ft.Container(expand=True), lang_btn]),
        ft.Card(content=ft.Container(
            content=ft.Row([ip_input, port_input,
                ft.Button(content=ft.Row([ft.Icon("computer"), ft.Text(t("btn_connect"))]), on_click=on_connect),
                ft.OutlinedButton(content=ft.Row([ft.Icon("refresh"), ft.Text(t("btn_refresh"))]), on_click=refresh_devices),
            ], spacing=10),
            padding=15
        )),
        tabs,
        ft.Text("Console Output", size=16, weight=ft.FontWeight.BOLD),
        ft.Container(content=console, bgcolor=ft.Colors.BLACK87, border_radius=10, padding=10, height=180),
    )

    refresh_devices()

ft.app(target=main)
