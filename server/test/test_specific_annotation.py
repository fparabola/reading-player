import sys
import os
import json

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from llm_service import parse_annotations, rebuild_annotated_html, create_readable_annotations

def test_specific_annotation():
    """
    测试特定标注HTML的解析、重建和标注列表生成
    """
    print("测试特定标注HTML:")
    
    # 测试HTML
    test_html = """I will 
 <mark data-id="P1" data-part="1" data-type="phrase" data-risk="high">take</mark> 
 my coat 
 <mark data-id="P1" data-part="2" data-type="phrase" data-risk="high">off</mark>. 
"""
    
    print("原始HTML:")
    print(test_html)
    
    # 解析HTML
    parsed_annotations = parse_annotations(test_html)
    print("\n解析结果:")
    print(json.dumps(parsed_annotations, indent=2, ensure_ascii=False))
    
    # 重建HTML
    rebuilt_html = rebuild_annotated_html(parsed_annotations)
    print("\n重建的HTML:")
    print(rebuilt_html)
    
    # 生成标注列表
    readable_annotations = create_readable_annotations(parsed_annotations)
    print("\n生成的标注列表:")
    print(json.dumps(readable_annotations, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_specific_annotation()
