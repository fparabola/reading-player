#!/usr/bin/env python3
"""
测试split接口的实际返回结果
"""

import requests
import json

# 测试文本
test_text = """CHAPTER TWO 
 THE VANISHING GLASS 
 Nearly ten years had passed since the Dursleys had woken up to find their nephew on the front step, but Privet Drive had hardly changed at all. 
"""

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
