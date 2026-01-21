import flet as ft
import subprocess
import os
import sys
import threading
from datetime import datetime
import time

# --- 国际化配置 ---
TRANSLATIONS = {
    "zh": {
        "title": "ADB & Scrcpy 极简工具",
        "ip_hint": "IP 地址 (例如 192.168.1.100)",
        "port_hint": "端口",
        "btn_connect": "连接",
        "btn_disconnect": "断开",
        "btn_refresh": "刷新列表",
        "tab_devices": "设备列表",
        "tab_ops": "快捷操作",
        "tab_logs": "日志抓取",
        "status_ready": "准备就绪",
        "status_connected": "已连接",
        "status_failed": "操作失败",
        "col_sn": "序列号/IP",
        "col_type": "类型",
        "col_status": "状态",
        "btn_root": "Root",
        "btn_remount": "Remount",
        "btn_settings": "原生设置",
        "btn_install": "安装 APK",
        "btn_scrcpy": "启动投屏",
        "btn_reboot": "重启",
        "btn_launcher_en": "启用 Launcher",
        "btn_launcher_dis": "禁用 Launcher",
        "log_logcat": "Logcat",
        "log_dmesg": "Dmesg",
        "log_tomb": "Tombstones",
        "log_anr": "ANR Traces",
        "console_title": "输出控制台",
        "msg_select_first": "请先选择一个设备！",
        "msg_scrcpy_error": "找不到 scrcpy.exe",
    },
    "en": {
        "title": "ADB & Scrcpy Modern Tool",
        "ip_hint": "IP Address (e.g. 192.168.1.100)",
        "port_hint": "Port",
        "btn_connect": "Connect",
        "btn_disconnect": "Disconnect",
        "btn_refresh": "Refresh",
        "tab_devices": "Devices",
        "tab_ops": "Operations",
        "tab_logs": "Capture",
        "status_ready": "Ready",
        "status_connected": "Connected",
        "status_failed": "Failed",
        "col_sn": "Serial/IP",
        "col_type": "Type",
        "col_status": "Status",
        "btn_root": "ADB Root",
        "btn_remount": "Remount",
        "btn_settings": "Settings",
        "btn_install": "Install APK",
        "btn_scrcpy": "Start Mirror",
        "btn_reboot": "Reboot",
        "btn_launcher_en": "Enable Launcher",
        "btn_launcher_dis": "Disable Launcher",
        "log_logcat": "Logcat",
        "log_dmesg": "Dmesg",
        "log_tomb": "Tombstones",
        "log_anr": "ANR",
        "console_title": "Console Output",
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
    # --- 初始化 ---
    page.title = "ADB & Scrcpy Tool"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1000
    page.window_height = 800
    page.padding = 20

    lang = "zh"
    base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    adb_mgr = AdbManager(base_path)

    # --- UI 控件 ---
    def get_text(key):
        return TRANSLATIONS[lang][key]

    console = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    device_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("")),
            ft.DataColumn(ft.Text("SN/IP")),
            ft.DataColumn(ft.Text("Type")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[],
    )

    def log(msg, is_error=False):
        ts = datetime.now().strftime("%H:%M:%S")
        color = ft.colors.RED_400 if is_error else ft.colors.GREEN_400
        console.controls.append(ft.Text(f"[{ts}] {msg}", color=color, size=13, font_family="Consolas"))
        page.update()

    def refresh_devices(e=None):
        success, out = adb_mgr.run_cmd(["devices", "-l"], use_device=False)
        device_table.rows.clear()
        lines = out.strip().split('\n')[1:]
        for line in lines:
            if not line.strip(): continue
            parts = line.split()
            sn = parts[0]
            status = parts[1]
            is_selected = sn == adb_mgr.current_device

            def on_row_select(sn_val):
                adb_mgr.current_device = sn_val
                refresh_devices()
                log(f"Selected: {sn_val}")

            device_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Icon(ft.icons.CHECK_CIRCLE, color="blue") if is_selected else ft.Icon(ft.icons.CIRCLE_OUTLINED)),
                        ft.DataCell(ft.Text(sn)),
                        ft.DataCell(ft.Text("TCP/IP" if ":" in sn else "USB")),
                        ft.DataCell(ft.Text(status, color="green" if status == "device" else "red")),
                    ],
                    on_select_changed=lambda _, s=sn: on_row_select(s)
                )
            )
        if not adb_mgr.current_device and device_table.rows:
            adb_mgr.current_device = lines[0].split()[0]
        page.update()

    # --- 按钮回调 ---
    def on_connect(e):
        addr = f"{ip_input.value}:{port_input.value or '5555'}"
        success, out = adb_mgr.run_cmd(["connect", addr], use_device=False)
        log(out.strip())
        refresh_devices()

    def on_action(args):
        if not adb_mgr.current_device:
            log(get_text("msg_select_first"), True)
            return
        success, out = adb_mgr.run_cmd(args)
        log(out.strip() or "Success")

    def on_scrcpy(e):
        if not adb_mgr.current_device: return log(get_text("msg_select_first"), True)
        if not os.path.exists(adb_mgr.scrcpy_path): return log(get_text("msg_scrcpy_error"), True)
        subprocess.Popen([adb_mgr.scrcpy_path, "-s", adb_mgr.current_device],
                         cwd=os.path.dirname(adb_mgr.scrcpy_path), creationflags=0x00000010)
        log(f"Scrcpy started for {adb_mgr.current_device}")

    def on_capture(log_type):
        if not adb_mgr.current_device: return log(get_text("msg_select_first"), True)
        sn_dir = adb_mgr.current_device.replace(":", "_")
        dir_path = os.path.join(base_path, "logs", sn_dir)
        os.makedirs(dir_path, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if log_type in ["logcat", "dmesg"]:
            file_path = os.path.join(dir_path, f"{ts}_{log_type}.txt")
            success, out = adb_mgr.run_cmd([log_type, "-d"] if log_type=="logcat" else ["shell", "dmesg"])
            with open(file_path, "w", encoding="utf-8") as f: f.write(out)
            log(f"Saved: {file_path}")
        else:
            folder_path = os.path.join(dir_path, f"{ts}_{log_type}")
            os.makedirs(folder_path, exist_ok=True)
            remote = "/data/tombstones" if log_type=="tombstones" else "/data/anr"
            success, out = adb_mgr.run_cmd(["pull", remote, folder_path])
            log(f"Pulled to: {folder_path}")

    # --- UI 组件布局 ---
    ip_input = ft.TextField(label="IP", placeholder="192.168.1.100", expand=True)
    port_input = ft.TextField(label="Port", value="5555", width=100)

    def toggle_lang(e):
        nonlocal lang
        lang = "en" if lang == "zh" else "zh"
        update_ui_text()

    def update_ui_text():
        page.title = get_text("title")
        ip_input.label = get_text("ip_hint")
        port_input.label = get_text("port_hint")
        btn_conn.text = get_text("btn_connect")
        btn_refresh.text = get_text("btn_refresh")
        tab1.label = get_text("tab_devices")
        tab2.label = get_text("tab_ops")
        tab3.label = get_text("tab_logs")
        lang_btn.text = "English" if lang == "zh" else "中文"
        page.update()

    btn_conn = ft.ElevatedButton(text="Connect", on_click=on_connect, icon=ft.icons.LAN)
    btn_refresh = ft.OutlineButton(text="Refresh", on_click=refresh_devices, icon=ft.icons.REFRESH)
    lang_btn = ft.TextButton(text="English", on_click=toggle_lang)

    tab1 = ft.Tab(text="Devices", content=ft.Column([device_table], scroll=ft.ScrollMode.ALWAYS))

    tab2 = ft.Tab(text="Operations", content=ft.Column([
        ft.Row([
            ft.ElevatedButton("Root", on_click=lambda _: on_action(["root"])),
            ft.ElevatedButton("Remount", on_click=lambda _: on_action(["remount"])),
            ft.ElevatedButton("Settings", on_click=lambda _: on_action(["shell", "am", "start", "-n", "com.android.settings/.Settings"])),
        ]),
        ft.Row([
            ft.ElevatedButton("Scrcpy", on_click=on_scrcpy, bgcolor=ft.colors.GREEN_700, color="white"),
            ft.ElevatedButton("Reboot", on_click=lambda _: on_action(["reboot"]), bgcolor=ft.colors.ORANGE_700, color="white"),
        ]),
        ft.Row([
            ft.TextButton("Enable Launcher", on_click=lambda _: on_action(["shell", "pm", "enable", "com.android.launcher3"])),
            ft.TextButton("Disable Launcher", on_click=lambda _: on_action(["shell", "pm", "disable", "com.android.launcher3"])),
        ])
    ], spacing=20, padding=20))

    tab3 = ft.Tab(text="Capture", content=ft.Row([
        ft.ElevatedButton("Logcat", on_click=lambda _: on_capture("logcat"), icon=ft.icons.DESCRIPTION),
        ft.ElevatedButton("Dmesg", on_click=lambda _: on_capture("dmesg"), icon=ft.icons.BUG_REPORT),
        ft.ElevatedButton("Tombstones", on_click=lambda _: on_capture("tombstones"), icon=ft.icons.FOLDER_ZIP),
        ft.ElevatedButton("ANR", on_click=lambda _: on_capture("anr"), icon=ft.icons.ERROR_OUTLINE),
    ], spacing=10, padding=20))

    page.add(
        ft.Row([ft.Text("ADB TOOL", size=30, weight="bold"), ft.Spacer(), lang_btn]),
        ft.Card(ft.Container(ft.Row([ip_input, port_input, btn_conn, btn_refresh]), padding=15)),
        ft.Tabs(expand=True, tabs=[tab1, tab2, tab3]),
        ft.Text("Console Output", size=16, weight="bold"),
        ft.Container(console, bgcolor=ft.colors.BLACK87, border_radius=10, padding=10, height=200)
    )

    update_ui_text()
    refresh_devices()

ft.app(target=main)
