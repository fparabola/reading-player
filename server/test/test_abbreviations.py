#!/usr/bin/env python3
"""
测试处理缩写
"""

import requests
import json

# 测试文本（包含缩写）
test_text = '''Mr. Smith went to the U.S. yesterday. He is a Ph.D. student.
Dr. Johnson will arrive at 3:30 p.m. tomorrow.
''' 

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
