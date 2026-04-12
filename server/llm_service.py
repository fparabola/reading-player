"""
LLM服务
提供与大语言模型交互的接口
"""
import json
import traceback
from openai import AsyncOpenAI
from typing import Optional
from config_helper import config_helper
from prompt_helper import prompt_helper

API_CONFIG = {
    "base_url": config_helper.get("api.base_url"),
    "default_model": config_helper.get("api.default_model"),
    "temperature": float(config_helper.get("api.temperature"))
}

async def analyze_text_stream(api_key: str, text: str, model: Optional[str] = None):
    """
    流式分析文本
    
    参数:
    - api_key: API密钥
    - text: 要分析的文本
    - model: 模型名称
    
    返回:
    - 流式分析结果
    """
    system_prompt = prompt_helper.get_prompt("", "analyze_prompt")
    user_prompt = text
    model_name = model or API_CONFIG["default_model"]
    
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=API_CONFIG["base_url"]
        )
        
        # 使用异步流式API
        stream = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=API_CONFIG["temperature"],
            stream=True
        )
        
        # 异步迭代stream
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        print(f"LLM exception: {str(e)}")
        print(traceback.format_exc())
        pass

async def annotate_text(api_key: str, text: str, model: Optional[str] = None):
    """
    标注文本
    
    参数:
    - api_key: API密钥
    - text: 要标注的文本
    - model: 模型名称
    
    返回:
    - 标注结果
    """
    system_prompt = prompt_helper.get_prompt("", "ai_mark")
    user_prompt = text
    model_name = model or API_CONFIG["default_model"]
    
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=API_CONFIG["base_url"]
        )
        
        # 使用异步非流式API
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=API_CONFIG["temperature"]
        )
        
        # 返回完整的响应
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM exception: {str(e)}")
        print(traceback.format_exc())
        return ""

def parse_annotations(annotated_html: str):
    """
    解析标注结果，转换为结构化格式
    
    参数:
    - annotated_html: 带有<mark>标签的HTML文本
    
    返回:
    - 结构化的标注信息
    """
    import re
    from collections import defaultdict
    
    # 正则表达式匹配mark标签（支持内联样式）
    pattern = r'<mark[^>]*data-id="([^"]+)"[^>]*data-part="([^"]+)"[^>]*data-type="([^"]+)"[^>]*data-risk="([^"]+)"[^>]*>([^<]+)</mark>'
    
    # 提取所有mark标签
    matches = re.findall(pattern, annotated_html)
    
    # 重建原始文本
    original_text = re.sub(pattern, r'\5', annotated_html)
    
    # 计算每个标注部分的位置
    current_pos = 0
    annotations = []
    
    # 分割文本和mark标签
    parts = re.split(pattern, annotated_html)
    
    for i in range(0, len(parts), 6):
        # 处理mark标签前的文本
        text_before = parts[i]
        current_pos += len(text_before)
        
        # 处理mark标签
        if i + 5 < len(parts):
            data_id = parts[i+1]
            data_part = int(parts[i+2])
            data_type = parts[i+3]
            data_risk = parts[i+4]
            text = parts[i+5]
            
            # 计算位置
            start = current_pos
            end = current_pos + len(text)
            current_pos = end
            
            # 添加到标注列表
            annotations.append({
                "id": data_id,
                "type": data_type,
                "risk": data_risk,
                "part": data_part,
                "text": text,
                "start": start,
                "end": end
            })
    
    # 按data-id分组
    groups = defaultdict(list)
    for item in annotations:
        groups[item["id"]].append(item)
    
    # 构建最终的标注结构
    final_annotations = []
    for data_id, items in groups.items():
        # 按part排序
        items.sort(key=lambda x: x["part"])
        
        # 收集parts
        parts = []
        annotation_text = ""
        for item in items:
            parts.append({
                "part": item["part"],
                "text": item["text"],
                "start": item["start"],
                "end": item["end"]
            })
            annotation_text += item["text"]
        
        # 获取类型和风险等级（取第一个item的值）
        annotation_type = items[0]["type"]
        annotation_risk = items[0]["risk"]
        
        # 添加到最终标注列表
        final_annotations.append({
            "id": data_id,
            "type": annotation_type,
            "risk": annotation_risk,
            "text": annotation_text,
            "parts": parts
        })
    
    # 返回结构化结果
    return {
        "text": original_text,
        "annotations": final_annotations
    }

def rebuild_annotated_html(structured_annotations: dict):
    """
    重建标注的HTML，对标注文本添加划线效果
    
    参数:
    - structured_annotations: 结构化的标注信息
    
    返回:
    - 带有划线效果的HTML文本
    """
    # 获取原始文本
    original_text = structured_annotations.get("text", "")
    annotations = structured_annotations.get("annotations", [])
    
    # 按起始位置排序，确保正确处理重叠标注
    sorted_annotations = []
    for annotation in annotations:
        for part in annotation["parts"]:
            sorted_annotations.append({
                "start": part["start"],
                "end": part["end"],
                "text": part["text"],
                "type": annotation["type"],
                "risk": annotation["risk"],
                "id": annotation["id"],
                "part": part["part"]
            })
    
    # 按起始位置排序
    sorted_annotations.sort(key=lambda x: x["start"])
    
    # 重建HTML
    result = []
    last_pos = 0
    
    for item in sorted_annotations:
        # 添加标注前的文本
        if item["start"] > last_pos:
            result.append(original_text[last_pos:item["start"]])
        
        # 添加带有划线效果的标注文本
        result.append(f'<mark data-id="{item["id"]}" data-part="{item["part"]}" data-type="{item["type"]}" data-risk="{item["risk"]}" style="text-decoration: line-through; color: red;">{item["text"]}</mark>')
        
        # 更新last_pos
        last_pos = item["end"]
    
    # 添加最后一部分文本
    if last_pos < len(original_text):
        result.append(original_text[last_pos:])
    
    # 合并结果
    return "".join(result)



