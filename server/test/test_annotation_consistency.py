import requests
import json
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from llm_service import parse_annotations, rebuild_annotated_html

def test_annotation_consistency():
    """
    测试标注重建的一致性
    """
    print("测试标注重建的一致性:")
    
    # 测试文本
    test_text = """At half past eight, Mr. Dursley picked up his briefcase, pecked Mrs. Dursley on the cheek, and tried to kiss Dudley good-bye but missed, because Dudley was now having a tantrum and throwing his cereal at the walls. \"Little tyke,\" chortled Mr. Dursley as he left the house. He got into his car and backed out of number four's drive. 
 It was on the corner of the street that he noticed the first sign of something peculiar -- a cat reading a map. For a second, Mr. Dursley didn't realize what he had seen -- then he jerked his head around to look again. There was a tabby cat standing on the corner of Privet Drive, but there wasn't a map in sight. What could he have been thinking of? It must have been a trick of the light. Mr. Dursley blinked and stared at the cat. It stared back. As Mr. Dursley drove around the corner and up the road, he watched the cat in his mirror. It was now reading the sign that said Privet Drive -- no, looking at the sign; cats couldn't read maps or signs. Mr. Dursley gave himself a little shake and put the cat out of his mind. As he drove toward town he thought of nothing except a large order of drills he was hoping to get that day."""
    
    # 调用/annotate接口获取结构化标注数据
    response = requests.post(
        "http://localhost:8000/annotate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": test_text})
    )
    
    if response.status_code == 200:
        # 获取结构化标注数据
        structured_annotations = response.json()
        print(f"原始文本长度: {len(structured_annotations['text'])}")
        print(f"标注数量: {len(structured_annotations['annotations'])}")
        
        # 重建HTML
        rebuilt_annotated_html = rebuild_annotated_html(structured_annotations)
        print(f"重建的HTML长度: {len(rebuilt_annotated_html)}")
        
        # 解析重建的HTML
        parsed_annotations = parse_annotations(rebuilt_annotated_html)
        print(f"解析后的文本长度: {len(parsed_annotations['text'])}")
        print(f"解析后的标注数量: {len(parsed_annotations['annotations'])}")
        
        # 再次重建HTML
        re_rebuilt_annotated_html = rebuild_annotated_html(parsed_annotations)
        print(f"再次重建的HTML长度: {len(re_rebuilt_annotated_html)}")
        
        # 比较一致性
        if rebuilt_annotated_html == re_rebuilt_annotated_html:
            print("✅ HTML一致性测试通过: 重建的HTML与再次重建的HTML一致")
        else:
            print("❌ HTML一致性测试失败: 重建的HTML与再次重建的HTML不一致")
            
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
        
        # 打印部分标注信息
        print("\n部分标注信息:")
        for i, annotation in enumerate(structured_annotations['annotations'][:5]):
            print(f"标注 {i+1}: {annotation['text']} (类型: {annotation['type']}, 风险: {annotation['risk']})")
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_annotation_consistency()
