#!/usr/bin/env python3
"""
详细诊断导入卡住问题的脚本
"""
import sys
import time
import traceback

def test_import(module_name, description=""):
    """测试导入模块并记录时间"""
    print(f"[DEBUG] 正在导入 {module_name}...", flush=True)
    start_time = time.time()
    try:
        __import__(module_name)
        elapsed = time.time() - start_time
        print(f"[SUCCESS] {module_name} 导入成功 - {elapsed:.3f}s {description}", flush=True)
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[FAILED] {module_name} 导入失败 - {elapsed:.3f}s: {e}", flush=True)
        return False

def main():
    print("=== 详细诊断服务启动问题 ===", flush=True)
    print(f"Python 版本: {sys.version}", flush=True)
    print(f"当前目录: {sys.path[0]}", flush=True)
    print(f"PID: {hash(time.time())}", flush=True)
    print("", flush=True)

    # 测试基本依赖
    print("=== 测试基本依赖 ===", flush=True)
    test_import("fastapi", "- Web框架")
    test_import("uvicorn", "- ASGI服务器")
    test_import("pydantic", "- 数据验证")
    test_import("asyncio", "- 异步支持")
    print("", flush=True)

    # 测试 numpy（可能是问题所在）
    print("=== 测试 numpy ===", flush=True)
    test_import("numpy", "- 数值计算")
    print("", flush=True)

    # 测试项目模块
    print("=== 测试项目模块 ===", flush=True)
    test_import("config_helper", "- 配置助手")
    test_import("prompt_helper", "- Prompt助手")
    test_import("llm_service", "- LLM服务")
    print("", flush=True)

    # 测试 edge_tts（延迟导入）
    print("=== 测试 edge_tts（延迟导入）===", flush=True)
    start_time = time.time()
    try:
        import edge_tts
        elapsed = time.time() - start_time
        print(f"[SUCCESS] edge_tts 导入成功 - {elapsed:.3f}s", flush=True)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[FAILED] edge_tts 导入失败 - {elapsed:.3f}s: {e}", flush=True)
    print("", flush=True)

    # 测试导入 sentence_service（这是卡住的地方）
    print("=== 测试导入 sentence_service ===", flush=True)
    print("注意：如果在此处卡住，请按 Ctrl+C 中断", flush=True)
    
    # 设置超时机制
    import signal
    
    class TimeoutException(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutException("导入超时")
    
    # 设置10秒超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)
    
    start_time = time.time()
    try:
        import sentence_service
        elapsed = time.time() - start_time
        signal.alarm(0)  # 取消超时
        print(f"[SUCCESS] sentence_service 导入成功 - {elapsed:.3f}s", flush=True)
        print("服务模块导入成功!", flush=True)
    except TimeoutException:
        elapsed = time.time() - start_time
        print(f"[TIMEOUT] sentence_service 导入超时 - {elapsed:.3f}s", flush=True)
        print("导入在以下位置卡住:", flush=True)
        traceback.print_stack()
    except Exception as e:
        elapsed = time.time() - start_time
        signal.alarm(0)  # 取消超时
        print(f"[FAILED] sentence_service 导入失败 - {elapsed:.3f}s: {e}", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    main()
