import requests
import json
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from llm_service import rebuild_annotated_html

# 测试文本
test_text = "I will take my coat off."

# 调用/annotate接口
response = requests.post(
    "http://localhost:8000/annotate",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"text": test_text})
)

# 检查响应状态码
if response.status_code == 200:
    # 获取结构化标注数据
    structured_annotations = response.json()
    print("原始结构化标注数据:")
    print(json.dumps(structured_annotations, indent=2, ensure_ascii=False))
    
    # 重建HTML
    annotated_html = rebuild_annotated_html(structured_annotations)
    print("\n重建的HTML:")
    print(annotated_html)
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)
