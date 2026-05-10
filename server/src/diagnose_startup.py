#!/usr/bin/env python3
"""
诊断服务启动问题的脚本
"""
import sys
import time

def test_import(import_name, module_name=None):
    """测试导入模块"""
    start_time = time.time()
    try:
        if module_name:
            exec(f"from {import_name} import {module_name}")
        else:
            __import__(import_name)
        elapsed = time.time() - start_time
        print(f"✓ {import_name} ({module_name or ''}) - {elapsed:.2f}s")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ {import_name} ({module_name or ''}) - {elapsed:.2f}s - {e}")
        return False

def main():
    print("=== 诊断服务启动问题 ===")
    print(f"Python 版本: {sys.version}")
    print(f"当前目录: {sys.path[0]}")
    print()
    
    # 添加src目录到Python路径
    sys.path.append(sys.path[0])
    
    # 测试关键导入
    print("测试导入...")
    imports = [
        ("fastapi", None),
        ("uvicorn", None),
        ("pydantic", "BaseModel"),
        ("edge_tts", None),
        ("config_helper", "config_helper"),
        ("prompt_helper", "prompt_helper"),
        ("llm_service", "analyze_text_stream"),
    ]
    
    success = True
    for import_name, module_name in imports:
        if not test_import(import_name, module_name):
            success = False
    
    print()
    if success:
        print("所有导入测试通过!")
        print("尝试导入主服务模块...")
        start_time = time.time()
        try:
            import sentence_service
            elapsed = time.time() - start_time
            print(f"✓ sentence_service - {elapsed:.2f}s")
            print("服务模块导入成功!")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ sentence_service - {elapsed:.2f}s")
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("导入测试失败，请检查依赖安装情况。")

if __name__ == "__main__":
    main()
