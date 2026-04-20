"""
分句服务管理脚本 v3.0 - 简化版
支持启动、停止、重启、状态查看
"""
import subprocess
import sys
import time
from pathlib import Path

PID_FILE = Path(__file__).parent / ".service.pid"


def get_pid():
    """获取服务进程ID"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return None


def is_running(pid):
    """检查进程是否运行"""
    if not pid:
        return False
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
            capture_output=True, text=True
        ) if sys.platform == 'win32' else None

        if sys.platform == 'win32':
            return str(pid) in result.stdout
        else:
            import os
            os.kill(pid, 0)
            return True
    except:
        return False


def start_service():
    """启动服务"""
    pid = get_pid()
    if pid and is_running(pid):
        print(f"服务已在运行中 (PID: {pid})")
        print(f"API: http://localhost:8000")
        return

    print("启动服务...")
    service_file = Path(__file__).parent / "sentence_service.py"

    # 根据平台选择启动方式
    if sys.platform == 'win32':
        # Windows下启动
        process = subprocess.Popen(
            [sys.executable, str(service_file)],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Linux/Termux下启动
        process = subprocess.Popen(
            [sys.executable, str(service_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

    with open(PID_FILE, 'w') as f:
        f.write(str(process.pid))

    time.sleep(3)

    if is_running(process.pid):
        print(f"服务启动成功 (PID: {process.pid})")
        print(f"API地址: http://localhost:8000")
        print(f"API文档: http://localhost:8000/docs")
    else:
        print("服务启动失败")
        PID_FILE.unlink(missing_ok=True)


def stop_service():
    """停止服务"""
    pid = get_pid()
    if not pid:
        print("服务未运行")
        return

    if not is_running(pid):
        print("服务未运行")
        PID_FILE.unlink(missing_ok=True)
        return

    print(f"停止服务 (PID: {pid})...")
    
    # 根据平台选择停止方式
    if sys.platform == 'win32':
        # Windows下停止
        subprocess.run(
            ['taskkill', '/F', '/PID', str(pid)],
            capture_output=True
        )
    else:
        # Linux/Termux下停止
        import os
        os.kill(pid, 9)  # 发送 SIGKILL 信号

    time.sleep(1)
    PID_FILE.unlink(missing_ok=True)
    print("服务已停止")


def restart_service():
    """重启服务"""
    print("重启服务...")
    stop_service()
    time.sleep(2)
    start_service()


def show_status():
    """显示服务状态"""
    pid = get_pid()
    if pid and is_running(pid):
        print(f"状态: 运行中 ● PID={pid}")
        print(f"API: http://localhost:8000")
        return
    print("状态: 未运行")


def show_logs():
    """查看服务日志"""
    log_file = Path(__file__).parent / "service.log"
    if log_file.exists():
        print("服务日志:")
        print("=" * 50)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 显示最后 50 行
                for line in lines[-50:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"读取日志失败: {e}")
    else:
        print("日志文件不存在")


def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else 'help'

    if cmd == 'start':
        start_service()
    elif cmd == 'stop':
        stop_service()
    elif cmd == 'restart':
        restart_service()
    elif cmd == 'status':
        show_status()
    elif cmd == 'logs':
        show_logs()
    else:
        print("用法: python service_manager.py start|stop|restart|status|logs")


if __name__ == '__main__':
    main()
