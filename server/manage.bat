@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo     分句服务管理 (Sentence Service)
echo ========================================
echo.
echo  [1] 启动服务 Start
echo  [2] 停止服务 Stop
echo  [3] 重启服务 Restart
echo  [4] 查看状态 Status
echo  [5] 查看日志 Logs
echo  [0] 退出 Exit
echo.
set /p choice="请选择 Please select (0-5): "

if "%choice%"=="1" (
    python service_manager.py start
    pause
) else if "%choice%"=="2" (
    python service_manager.py stop
    pause
) else if "%choice%"=="3" (
    python service_manager.py restart
    pause
) else if "%choice%"=="4" (
    python service_manager.py status
    pause
) else if "%choice%"=="5" (
    python service_manager.py logs
    pause
) else if "%choice%"=="0" (
    exit
) else (
    echo 无效选择 Invalid choice
    pause
)
