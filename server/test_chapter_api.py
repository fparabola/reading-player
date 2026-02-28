"""
测试章节目录和内容接口
"""
import requests

BASE_URL = "http://localhost:8000"


def test_get_books():
    """测试获取书籍目录"""
    print("=" * 50)
    print("测试1: 获取书籍目录 /books")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/books")
        data = response.json()

        print(f"状态码: {response.status_code}")
        print(f"书籍数量: {len(data['books'])}")

        for book in data['books']:
            print(f"\n书名: {book['name']}")
            print(f"章节数: {len(book['chapters'])}")
            print("前5个章节:")
            for chapter in book['chapters'][:5]:
                print(f"  - {chapter['name']}")

        if data['books']:
            return data['books'][0]['name'], data['books'][0]['chapters'][0]['name']
        else:
            print("警告: 没有找到任何书籍")
            return None, None

    except Exception as e:
        print(f"错误: {e}")
        return None, None


def test_get_book_chapters(book_name):
    """测试获取指定书籍的章节"""
    if not book_name:
        print("跳过: 没有提供书名")
        return None

    print("\n" + "=" * 50)
    print(f"测试2: 获取书籍章节 /chapter/{book_name}")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/chapter/{book_name}")
        data = response.json()

        print(f"状态码: {response.status_code}")
        print(f"书名: {data['book_name']}")
        print(f"章节数: {len(data['chapters'])}")

        return data['chapters'][0]['name'] if data['chapters'] else None

    except Exception as e:
        print(f"错误: {e}")
        return None


def test_get_chapter_content(book_name, chapter_name):
    """测试获取章节内容"""
    if not book_name or not chapter_name:
        print("跳过: 没有提供书名或章节名")
        return

    print("\n" + "=" * 50)
    print(f"测试3: 获取章节内容 /chapter/{book_name}/{chapter_name}")
    print("=" * 50)

    try:
        # 从位置0开始获取内容
        response = requests.get(f"{BASE_URL}/chapter/{book_name}/{chapter_name}?position=0")
        data = response.json()

        print(f"状态码: {response.status_code}")
        print(f"书名: {data['book_name']}")
        print(f"章节名: {data['chapter_name']}")
        print(f"起始位置: {data['start_position']}")
        print(f"结束位置: {data['end_position']}")
        print(f"是否段落结尾: {data['paragraph_end']}")
        print(f"文本长度: {len(data['text'])} 字符")
        print(f"\n内容预览:")
        print("-" * 40)
        print(data['text'][:200] + "..." if len(data['text']) > 200 else data['text'])
        print("-" * 40)

        # 测试从不同位置获取内容
        if len(data['text']) > 500:
            print(f"\n测试从位置500获取内容:")
            response2 = requests.get(f"{BASE_URL}/chapter/{book_name}/{chapter_name}?position=500")
            data2 = response2.json()
            print(f"内容: {data2['text'][:100]}...")

    except Exception as e:
        print(f"错误: {e}")


def main():
    print("=" * 50)
    print("章节API测试")
    print("=" * 50)

    # 测试健康检查
    print("\n健康检查:")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态: {response.json()}")
    except:
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
