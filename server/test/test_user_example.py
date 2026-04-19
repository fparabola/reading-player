#!/usr/bin/env python3
"""
测试用户提供的例子
"""

import requests
import json

# 测试文本
test_text = '"It all gets so confusing if we keep saying \'You-Know-Who.\' I have never seen any reason to be frightened of saying Voldemort\'s name. \n "I know you haven \'t, said Professor McGonagall, sounding half exasperated, half admiring. \n' 

print("测试文本:")
print(repr(test_text))
print("\n文本长度:", len(test_text))
print("包含换行符:", '\n' in test_text)


# 测试split接口
def test_split_api():
    url = "http://localhost:8000/split"
    headers = {"Content-Type": "application/json"}
    data = {
        "text": test_text,
        "language": "en",
        "method": "r"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # 检查HTTP状态码
        result = response.json()
        
        print("接口返回结果:")
        print(f"句子数量: {result['count']}")
        print(f"使用的算法: {result['method']}")
        print("句子列表:")
        for i, sentence in enumerate(result['sentences']):
            print(f"句子 {i+1}: {repr(sentence)}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_split_api()
