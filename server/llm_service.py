"""
LLM服务
提供与大语言模型交互的接口
"""
import json
import traceback
from pathlib import Path
from openai import OpenAI
from typing import Optional, AsyncGenerator
from config_helper import config_helper

# API配置
API_CONFIG = {
    "base_url": config_helper.get_base_url(),
    "default_model": config_helper.get_default_model(),
    "system_prompt": config_helper.get_system_prompt()
}


def build_analyze_prompt(text: str) -> str:
    """
    构建分析提示
    """
    # 从md文件中读取prompt
    prompt_path = Path(__file__).parent / "prompt" / "analyze_prompt.md"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    # 替换文本占位符
    return prompt_template.replace("{text}", text)





def analyze_text_stream(api_key: str, text: str, model: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    流式分析文本
    
    参数:
    - api_key: API密钥
    - text: 要分析的文本
    - model: 模型名称
    
    返回:
    - 流式分析结果
    """
    prompt = build_analyze_prompt(text)
    model_name = model or API_CONFIG["default_model"]
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=API_CONFIG["base_url"]
        )
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": API_CONFIG["system_prompt"]},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        print(f"LLM exception: {str(e)}")
        print(traceback.format_exc())
        pass
