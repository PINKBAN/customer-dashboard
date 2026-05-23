@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   客户联络看板 - 一键更新
echo ========================================
echo.
python build_dashboard.py
echo.
echo 按任意键关闭...
pause >nul
