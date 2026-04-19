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

