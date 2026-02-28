"""
测试章节目录和内容接口
使用 Python 内置 urllib 模块
"""
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"


def http_get(url):
    """发送 GET 请求"""
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            return json.loads(data), response.status
    except urllib.error.HTTPError as e:
        try:
            error_data = e.read().decode('utf-8')
            return json.loads(error_data), e.code
        except:
            return None, e.code
    except Exception as e:
        print(f"请求失败: {e}")
        return None, None


def test_get_books():
    """测试获取书籍目录"""
    print("=" * 50)
    print("测试1: 获取书籍目录 /books")
    print("=" * 50)

    data, status_code = http_get(f"{BASE_URL}/books")

    if status_code and data:
        print(f"状态码: {status_code}")
        print(f"书籍数量: {len(data.get('books', []))}")

        for book in data.get('books', []):
            print(f"\n书名: {book['name']}")
            print(f"章节数: {len(book['chapters'])}")
            print("前5个章节:")
            for chapter in book['chapters'][:5]:
                print(f"  - {chapter['name']}")

        if data.get('books'):
            return data['books'][0]['name'], data['books'][0]['chapters'][0]['name']
        else:
            print("警告: 没有找到任何书籍")
            return None, None
    else:
        print(f"请求失败，状态码: {status_code}")
        return None, None


def test_get_book_chapters(book_name):
    """测试获取指定书籍的章节"""
    if not book_name:
        print("跳过: 没有提供书名")
        return None

    print("\n" + "=" * 50)
    print(f"测试2: 获取书籍章节 /chapter/{book_name}")
    print("=" * 50)

    # 对书名进行 URL 编码
    encoded_book = urllib.parse.quote(book_name, safe='')
    data, status_code = http_get(f"{BASE_URL}/chapter/{encoded_book}")

    if status_code and data:
        print(f"状态码: {status_code}")
        print(f"书名: {data.get('book_name', book_name)}")
        print(f"章节数: {len(data.get('chapters', []))}")

        return data['chapters'][0]['name'] if data.get('chapters') else None
    else:
        print(f"请求失败，状态码: {status_code}")
        return None


def test_get_chapter_content(book_name, chapter_name):
    """测试获取章节内容"""
    if not book_name or not chapter_name:
        print("跳过: 没有提供书名或章节名")
        return

    print("\n" + "=" * 50)
    print(f"测试3: 获取章节内容 /chapter/{book_name}/{chapter_name}")
    print("=" * 50)

    # 进行 URL 编码
    encoded_book = urllib.parse.quote(book_name, safe='')
    encoded_chapter = urllib.parse.quote(chapter_name, safe='')

    # 从位置0开始获取内容（默认min_size=100）
    data, status_code = http_get(f"{BASE_URL}/chapter/{encoded_book}/{encoded_chapter}?position=0")

    if status_code and data:
        print(f"状态码: {status_code}")
        print(f"书名: {data.get('book_name', book_name)}")
        print(f"章节名: {data.get('chapter_name', chapter_name)}")
        print(f"起始位置: {data.get('start_position', 0)}")
        print(f"结束位置: {data.get('end_position', 0)}")
        print(f"是否段落结尾: {data.get('paragraph_end', False)}")
        print(f"文本长度: {len(data.get('text', ''))} 字符")
        print(f"\n内容预览:")
        print("-" * 40)
        text = data.get('text', '')
        print(text[:200] + "..." if len(text) > 200 else text)
        print("-" * 40)

    # 测试不同的min_size值
    print(f"\n测试4: min_size=500")
    data2, status2 = http_get(f"{BASE_URL}/chapter/{encoded_book}/{encoded_chapter}?position=0&min_size=500")
    if data2:
        text2 = data2.get('text', '')
        print(f"  文本长度: {len(text2)} 字符 (要求 >=500)")
        print(f"  内容预览: {text2[:100]}...")

    print(f"\n测试5: min_size=2000")
    data3, status3 = http_get(f"{BASE_URL}/chapter/{encoded_book}/{encoded_chapter}?position=0&min_size=2000")
    if data3:
        text3 = data3.get('text', '')
        print(f"  文本长度: {len(text3)} 字符 (要求 >=2000)")

    # 测试从不同位置获取内容
    if len(text) > 500:
        print(f"\n测试6: position=500, min_size=300")
        data4, status4 = http_get(f"{BASE_URL}/chapter/{encoded_book}/{encoded_chapter}?position=500&min_size=300")
        if data4:
            text4 = data4.get('text', '')
            print(f"  起始位置: {data4.get('start_position', 0)}")
            print(f"  文本长度: {len(text4)} 字符")

    if status_code and data:
        return
    print(f"请求失败，状态码: {status_code}")
    if data:
        print(f"错误信息: {data}")


def main():
    print("=" * 50)
    print("章节 API 测试")
    print("=" * 50)

    # 测试健康检查
    print("\n健康检查:")
    data, status = http_get(f"{BASE_URL}/health")
    if status == 200 and data:
        print(f"状态: {data}")
    else:
        print("服务未运行，请先启动服务")
        return

    # 测试获取书籍
    book_name, chapter_name = test_get_books()

    # 测试获取书籍章节
    chapter_name = test_get_book_chapters(book_name) or chapter_name

    # 测试获取章节内容
    test_get_chapter_content(book_name, chapter_name)

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
