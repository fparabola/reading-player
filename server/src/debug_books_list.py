#!/usr/bin/env python3
"""
详细诊断 /books/list 接口问题
"""
import sys
import time
from pathlib import Path

def log_time(message):
    """记录时间"""
    print(f"[{time.time():.2f}] {message}", flush=True)

def main():
    log_time("=== 诊断 /books/list 接口 ===")
    
    # 检查资源目录
    log_time("步骤1: 检查资源目录")
    resource_dir = Path(__file__).parent.parent / "resource"
    log_time(f"  资源目录路径: {resource_dir}")
    log_time(f"  目录是否存在: {resource_dir.exists()}")
    
    if resource_dir.exists():
        log_time("  目录内容:")
        try:
            for item in resource_dir.iterdir():
                if item.is_dir():
                    log_time(f"    📁 {item.name}")
                    # 统计子文件数量
                    file_count = sum(1 for f in item.iterdir() if f.is_file())
                    log_time(f"      (包含 {file_count} 个文件)")
        except Exception as e:
            log_time(f"    ✗ 无法读取目录内容: {e}")
    
    log_time("")
    
    # 测试直接调用 get_resource_books
    log_time("步骤2: 测试 get_resource_books 函数")
    start = time.time()
    
    try:
        # 只导入需要的部分，避免触发其他问题
        from sentence_service import get_resource_books
        
        books = get_resource_books()
        elapsed = time.time() - start
        log_time(f"  ✓ get_resource_books 执行成功 - {elapsed:.3f}s")
        log_time(f"  书籍数量: {len(books)}")
        for book in books:
            log_time(f"    - {book.name} (章节数: {len(book.chapters)})")
    except Exception as e:
        elapsed = time.time() - start
        log_time(f"  ✗ get_resource_books 执行失败 - {elapsed:.3f}s")
        log_time(f"    错误: {e}")
        import traceback
        traceback.print_exc()
    
    log_time("")
    log_time("=== 诊断完成 ===")

if __name__ == "__main__":
    main()
