#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  分句服务管理 (Sentence Service)"
echo "========================================"
echo ""
echo "  [1] 启动服务 Start"
echo "  [2] 停止服务 Stop"
echo "  [3] 重启服务 Restart"
echo "  [4] 查看状态 Status"
echo "  [5] 查看日志 Logs"
echo "  [0] 退出 Exit"
echo ""
read -p "请选择 Please select (0-5): " choice

case $choice in
  1)
    python3 service_manager.py start
    ;;
  2)
    python3 service_manager.py stop
    ;;
  3)
    python3 service_manager.py restart
    ;;
  4)
    python3 service_manager.py status
    ;;
  5)
    python3 service_manager.py logs
    ;;
  0)
    exit
    ;;
  *)
    echo "无效选择 Invalid choice"
    ;;
esac
