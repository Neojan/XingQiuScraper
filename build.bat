@echo off
REM ============================================
REM 知识星球爬取工具 - Windows 打包脚本
REM ============================================

echo =========================================
echo   知识星球爬取工具 - Windows 打包脚本
echo =========================================

REM 安装依赖
echo.
echo 📦 安装依赖...
pip install pyinstaller requests

REM 打包
echo.
echo 🔨 开始打包...
pyinstaller build.spec --clean --noconfirm

echo.
echo ✅ 打包完成！
echo 📁 输出目录: dist\
echo    可执行文件: dist\知识星球爬取工具.exe
echo.
echo 提示: 可以将 dist\ 目录中的文件分发给其他用户使用
pause
