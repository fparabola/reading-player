"""
分句服务测试/示例代码
"""
import requests
import json


def test_split_service():
    """测试分句服务"""
    url = "http://localhost:8000/split"

    # 测试用例
    test_cases = [
        {
            "name": "简单句子",
            "text": "Hello world. How are you? I'm fine!",
            "language": "en"
        },
        {
            "name": "带缩写的文本",
            "text": "Dr. Smith lives on Main St. He works at IBM Inc. Mr. Johnson is his neighbor.",
            "language": "en"
        },
        {
            "name": "带问号和感叹号",
            "text": "What a beautiful day! Do you like it? Yes, I do.",
            "language": "en"
        },
        {
            "name": "带引号的文本",
            "text": 'She said, "I love Python." He replied, "Me too."',
            "language": "en"
        },
        {
            "name": "空文本",
            "text": "",
            "language": "en"
        }
    ]

    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"测试: {test['name']}")
        print(f"输入: {test['text'][:50]}{'...' if len(test['text']) > 50 else ''}")

        try:
            response = requests.post(
                url,
                json={"text": test["text"], "language": test["language"]},
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                print(f"\n结果 (共 {result['count']} 句):")
                for i, sent in enumerate(result['sentences'], 1):
                    print(f"  {i}. {sent}")
            else:
                print(f"\n错误: {response.status_code}")
                print(response.text)

        except requests.exceptions.ConnectionError:
            print("\n错误: 无法连接到服务，请确保服务正在运行")
            print("运行命令: python sentence_service.py")
            break
        except Exception as e:
            print(f"\n错误: {e}")


def test_with_curl():
    """打印curl命令示例"""
    print("\n" + "="*50)
    print("curl 命令示例:")
    print("="*50)
    print('# 基本使用')
    print("""curl -X POST "http://localhost:8000/split" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Hello world. How are you?", "language": "en"}'""")
    print('\n# 使用带缩写的文本')
    print("""curl -X POST "http://localhost:8000/split" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Dr. Smith lives on Main St. He is nice.", "language": "en"}'""")


def test_health():
    """健康检查"""
    url = "http://localhost:8000/health"
    try:
        response = requests.get(url, timeout=5)
        print("\n健康检查:", response.json())
    except requests.exceptions.ConnectionError:
        print("\n服务未运行")


if __name__ == "__main__":
    test_health()
    test_split_service()
    test_with_curl()
