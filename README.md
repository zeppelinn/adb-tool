# ADB & Scrcpy Tool

一个简单易用的 Windows 端 ADB 管理和屏幕投射工具。

## 功能特性

- **设备连接**: 支持通过 IP:端口连接 ADB 设备
- **设备发现**: 自动发现已连接的设备，显示 USB/TCP 连接类型
- **多设备管理**: 支持多设备切换选择
- **基础操作**:
  - Root 设备 (adb root)
  - Remount 分区 (adb remount)
  - 安装 APK (-r -d -t)
  - 打开原生设置
  - 启用/禁用 Launcher
  - 重启设备
- **日志抓取**:
  - Logcat 日志
  - Dmesg 内核日志
  - Tombstones 崩溃日志
  - ANR 日志
- **屏幕投射**: 一键启动 scrcpy

## 环境要求

- Windows 10/11 64位
- Python 3.8+ (仅开发时需要)
- scrcpy-win64-v1.25 文件夹

## 快速开始

### 使用编译好的 exe

1. 下载 `AdbTool.exe`
2. 将 `scrcpy-win64-v1.25` 文件夹放在同一目录
3. 双击运行 `AdbTool.exe`

### 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python adb_tool.py
```

### 打包成 exe

```bash
# Windows 下运行
build.bat
```

或手动执行:

```bash
pip install -r requirements.txt
pyinstaller --clean build.spec
```

## 目录结构

```
dist/
├── AdbTool.exe
├── scrcpy-win64-v1.25/    # 需要放在同一目录
│   ├── adb.exe
│   ├── scrcpy.exe
│   └── ...
└── logs/                   # 抓取的日志保存位置
```

## 使用说明

1. **连接设备**
   - USB 连接: 插入设备后自动识别
   - TCP/IP 连接: 输入 IP 地址和端口，点击"连接"

2. **选择设备**
   - 点击设备列表中的行即可选择

3. **执行操作**
   - 选择设备后，点击对应按钮执行操作

4. **日志抓取**
   - 抓取的日志保存在 `logs/` 目录下
