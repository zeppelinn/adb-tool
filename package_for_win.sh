#!/bin/bash
# 在 macOS 上使用 Docker 打包 Windows exe 的脚本

echo "正在启动 Docker 进行 Windows 打包..."

# 使用 cdrx/pyinstaller-windows 镜像
# 它内部集成了 Wine 和 PyInstaller
docker run --rm \
    -v "$(pwd):/src" \
    cdrx/pyinstaller-windows:python3 \
    "pip install -r requirements.txt && pyinstaller --clean --onefile --windowed --name AdbTool adb_tool.py"

echo "------------------------------------------"
echo "打包完成！请检查 dist/windows/AdbTool.exe"
