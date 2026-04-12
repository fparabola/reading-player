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
