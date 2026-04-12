"""
LLM服务
提供文本分析和标注功能
"""
import asyncio
import json
import re
from typing import AsyncGenerator, Dict, Any, List
import httpx
from pathlib import Path

from prompt_helper import prompt_helper
from config_helper import config_helper

async def analyze_text_stream(api_key: str, text: str, model: str = None) -> AsyncGenerator[str, None]:
    """
    流式分析文本
    
    参数:
        api_key: SiliconFlow API密钥
        text: 要分析的文本
        model: 模型名称
    
    返回:
        流式返回分析结果
    """
    # 获取配置
    base_url = config_helper.get("api.base_url")
    default_model = model or config_helper.get("api.default_model")
    temperature = float(config_helper.get("api.temperature"))
    
    # 获取prompt
    prompt = prompt_helper.get_prompt("", "analyze_prompt")
    
    # 构建请求体
    payload = {
        "model": default_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": temperature,
        "stream": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", f"{base_url}/chat/completions", json=payload, headers=headers) as response:
            async for chunk in response.aiter_text():
                if chunk.startswith("data: "):
                    chunk_data = chunk[6:]
                    if chunk_data == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk_data)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue

async def annotate_text(api_key: str, text: str, model: str = None) -> str:
    """
    标注文本
    
    参数:
        api_key: SiliconFlow API密钥
        text: 要标注的文本
        model: 模型名称
    
    返回:
        标注后的HTML
    """
    # 获取配置
    base_url = config_helper.get("api.base_url")
    default_model = model or config_helper.get("api.default_model")
    temperature = float(config_helper.get("api.temperature"))
    
    # 获取prompt
    prompt = prompt_helper.get_prompt("", "ai_mark")
    
    # 构建请求体
    payload = {
        "model": default_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": temperature,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "choices" in data and data["choices"]:
            content = data["choices"][0].get("message", {}).get("content", "")
            print("Marked Content:")
            print(content)
            # # 提取HTML部分
            # html_match = re.search(r'<html>([\s\S]*)</html>', content)
            # if html_match:
            #     return html_match.group(1).strip()
            return content
        return ""

def parse_annotations(annotated_html: str) -> Dict[str, Any]:
    """
    解析标注HTML
    
    参数:
        annotated_html: 标注后的HTML
    
    返回:
        结构化的标注信息
    """
    # 提取纯文本
    text = re.sub(r'<[^>]+>', '', annotated_html)
    
    # 提取标注
    annotations = []
    
    # 匹配mark标签
    mark_pattern = re.compile(r'<mark\s+data-id="([^"]+)"\s+data-part="([^"]+)"\s+data-type="([^"]+)"\s+data-risk="([^"]+)"[^>]*>([^<]+)</mark>', re.DOTALL)
    
    matches = mark_pattern.finditer(annotated_html)
    
    for match in matches:
        id_value = match.group(1)
        part = match.group(2)
        type_value = match.group(3)
        risk = match.group(4)
        text_content = match.group(5).strip()
        
        # 查找该标注的所有部分
        annotation = None
        for existing_annotation in annotations:
            if existing_annotation["id"] == id_value:
                annotation = existing_annotation
                break
        
        if not annotation:
            annotation = {
                "id": id_value,
                "type": type_value,
                "risk": risk,
                "text": "",
                "parts": []
            }
            annotations.append(annotation)
        
        # 添加部分
        annotation["parts"].append({
            "part": int(part),
            "text": text_content,
            "start": 0,  # 暂时设置为0，后续可以根据需要计算
            "end": 0
        })
    
    # 构建完整的标注文本
    for annotation in annotations:
        # 按part排序
        annotation["parts"].sort(key=lambda x: x["part"])
        # 连接所有部分的文本
        annotation["text"] = " ".join([part["text"] for part in annotation["parts"]])
    
    return {
        "text": text,
        "annotations": annotations
    }

def fix_annotated_html(annotated_html: str) -> str:
    """
    修复标注HTML，确保mark标签之间有空格
    
    参数:
        annotated_html: 标注后的HTML
    
    返回:
        修复后的HTML
    """
    # 在mark标签之间添加空格
    fixed_html = re.sub(r'</mark><mark', '</mark> <mark', annotated_html)
    # 确保HTML开头和结尾的空格正确
    fixed_html = fixed_html.strip()
    return fixed_html

def create_readable_annotations(annotations: dict) -> dict:
    """
    创建用户可读的标注列表
    
    参数:
        annotations: annotate接口返回的结构化标注信息
    
    返回:
        用户可读的标注列表
    """
    import hashlib
    
    text = annotations.get('text', '')
    annotation_list = annotations.get('annotations', [])
    
    # 计算文本的MD5哈希值
    text_md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    # 处理标注列表
    readable_annotations = []
    for annotation in annotation_list:
        parts = annotation.get('parts', [])
        # 按part排序
        parts.sort(key=lambda x: x.get('part', 0))
        # 提取每个part的文本并连接
        part_texts = [part.get('text', '') for part in parts]
        content = ' ... '.join(part_texts)
        
        readable_annotations.append({
            'id': annotation.get('id'),
            'content': content,
            'type': annotation.get('type'),
            'risk': annotation.get('risk')
        })
    
    # 返回新的JSON对象
    return {
        'text_md5': text_md5,
        'text': text,
        'annotations': readable_annotations
    }

def rebuild_annotated_html(annotations: dict) -> str:
    """
    根据标注信息重建HTML
    
    参数:
        annotations: 结构化的标注信息
    
    返回:
        标注后的HTML
    """
    text = annotations.get('text', '')
    annotation_list = annotations.get('annotations', [])
    
    # 按标注位置排序
    sorted_annotations = []
    for annotation in annotation_list:
        parts = annotation.get('parts', [])
        for part in parts:
            sorted_annotations.append({
                'id': annotation.get('id'),
                'part': part.get('part'),
                'type': annotation.get('type'),
                'risk': annotation.get('risk'),
                'text': part.get('text'),
                'start': part.get('start', 0),
                'end': part.get('end', 0)
            })
    
    # 按起始位置排序
    sorted_annotations.sort(key=lambda x: x['start'])
    
    # 重建HTML
    result = []
    last_end = 0
    
    for item in sorted_annotations:
        # 添加标注前的文本
        if item['start'] > last_end:
            result.append(text[last_end:item['start']])
        
        # 添加标注
        result.append(f'<mark data-id="{item["id"]}" data-part="{item["part"]}" data-type="{item["type"]}" data-risk="{item["risk"]}">{item["text"]}</mark>')
        
        last_end = item['end']
    
    # 添加剩余的文本
    if last_end < len(text):
        result.append(text[last_end:])
    
    return ''.join(result)