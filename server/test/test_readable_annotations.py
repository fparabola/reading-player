import requests
import json
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from llm_service import create_readable_annotations

def test_readable_annotations():
    """
    测试create_readable_annotations函数
    """
    print("测试create_readable_annotations函数:")
    
    # 测试文本
    test_text = "I will take my coat off."
    
    # 调用/annotate接口获取结构化标注数据
    response = requests.post(
        "http://localhost:8000/annotate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": test_text})
    )
    
    if response.status_code == 200:
        # 获取结构化标注数据
        structured_annotations = response.json()
        print(f"原始文本: {structured_annotations['text']}")
        print(f"原始标注数量: {len(structured_annotations['annotations'])}")
        
        # 创建用户可读的标注列表
        readable_result = create_readable_annotations(structured_annotations)
        print(f"文本MD5: {readable_result['text_md5']}")
        print(f"可读标注数量: {len(readable_result['annotations'])}")
        
        # 打印可读标注列表
        print("\n可读标注列表:")
        for i, annotation in enumerate(readable_result['annotations']):
            print(f"标注 {i+1}: ID={annotation['id']}, Content={annotation['content']}")
        
        # 打印完整的JSON结果
        print("\n完整的JSON结果:")
        print(json.dumps(readable_result, indent=2, ensure_ascii=False))
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_readable_annotations()
