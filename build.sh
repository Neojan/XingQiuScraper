#!/usr/bin/env bash
# ============================================
# 知识星球爬取工具 - 打包脚本
# 支持 macOS 和 Windows（需在对应平台运行）
# ============================================

set -e

echo "========================================="
echo "  知识星球爬取工具 - 打包脚本"
echo "========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip3 install pyinstaller requests

# 打包
echo ""
echo "🔨 开始打包..."
python3 -m PyInstaller build.spec --clean --noconfirm

echo ""
echo "✅ 打包完成！"
echo "📁 输出目录: dist/"

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   macOS 可执行文件: dist/知识星球爬取工具.app"
    echo "   命令行可执行文件: dist/知识星球爬取工具"
else
    echo "   可执行文件: dist/知识星球爬取工具.exe"
fi

echo ""
echo "提示: 可以将 dist/ 目录中的文件分发给其他用户使用"
