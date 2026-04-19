#!/usr/bin/env python3
"""
测试test_content.txt的文本
"""

import requests
import json

# 读取test_content.txt文件
with open('test/test_content.txt', 'r', encoding='utf-8') as f:
    test_text = f.read()

print("测试文本:")
print(test_text)
print("\n文本长度:", len(test_text))
print("包含换行符:", '\n' in test_text)

# 测试split接口（使用n算法）
def test_split_api_n():
    url = "http://localhost:8000/split"
    headers = {"Content-Type": "application/json"}
    data = {
        "text": test_text,
        "language": "en",
        "method": "n"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # 检查HTTP状态码
        result = response.json()
        
        print("\n使用n算法的接口返回结果:")
        print(f"句子数量: {result['count']}")
        print(f"使用的算法: {result['method']}")
        print("句子列表:")
        for i, sentence in enumerate(result['sentences']):
            print(f"句子 {i+1}: {repr(sentence)}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

# 测试split接口（使用r算法）
def test_split_api_r():
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
        
        print("\n使用r算法的接口返回结果:")
        print(f"句子数量: {result['count']}")
        print(f"使用的算法: {result['method']}")
        print("句子列表:")
        for i, sentence in enumerate(result['sentences']):
            print(f"句子 {i+1}: {repr(sentence)}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_split_api_n()
    test_split_api_r()
