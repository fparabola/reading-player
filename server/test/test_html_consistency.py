import sys
import os
import requests
import json

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import parse_annotations, rebuild_annotated_html

def test_html_consistency():
    """
    测试重建的HTML和标记的HTML的一致性
    """
    print("测试HTML一致性:")
    
    # 测试文本
    test_text = "I will take my coat off and put on my hat."
    
    # 调用/annotate接口获取原始的标注HTML
    response = requests.post(
        "http://localhost:8000/annotate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": test_text})
    )
    
    if response.status_code == 200:
        # 获取结构化标注数据
        structured_annotations = response.json()
        print(f"原始文本: {structured_annotations['text']}")
        
        # 模拟原始的标注HTML（通过重建得到）
        original_annotated_html = rebuild_annotated_html(structured_annotations)
        print(f"原始标注HTML: {original_annotated_html}")
        
        # 解析原始的标注HTML
        parsed_annotations = parse_annotations(original_annotated_html)
        print(f"解析后的文本: {parsed_annotations['text']}")
        
        # 重建HTML
        rebuilt_annotated_html = rebuild_annotated_html(parsed_annotations)
        print(f"重建的HTML: {rebuilt_annotated_html}")
        
        # 比较一致性
        if original_annotated_html == rebuilt_annotated_html:
            print("✅ HTML一致性测试通过: 重建的HTML与原始标注HTML一致")
        else:
            print("❌ HTML一致性测试失败: 重建的HTML与原始标注HTML不一致")
            
        # 比较文本一致性
        if structured_annotations['text'] == parsed_annotations['text']:
            print("✅ 文本一致性测试通过: 解析和重建后的文本与原始文本一致")
        else:
            print("❌ 文本一致性测试失败: 解析和重建后的文本与原始文本不一致")
            
        # 比较标注数量一致性
        if len(structured_annotations['annotations']) == len(parsed_annotations['annotations']):
            print("✅ 标注数量一致性测试通过: 解析和重建后的标注数量与原始标注数量一致")
        else:
            print("❌ 标注数量一致性测试失败: 解析和重建后的标注数量与原始标注数量不一致")
            print(f"原始标注数量: {len(structured_annotations['annotations'])}")
            print(f"解析后标注数量: {len(parsed_annotations['annotations'])}")
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_html_consistency()
