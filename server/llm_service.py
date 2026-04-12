"""
LLM服务
提供与大语言模型交互的接口
"""
import json
import traceback
import configparser
from pathlib import Path
from openai import OpenAI
from typing import Optional, AsyncGenerator

# 读取配置文件
config = configparser.ConfigParser()
config_path = Path(__file__).parent / "config.ini"
config.read(config_path, encoding='utf-8')

# API配置
API_CONFIG = {
    "base_url": config.get("api", "base_url", fallback="https://api.siliconflow.cn/v1"),
    "default_model": config.get("api", "default_model", fallback="Qwen/Qwen3-14B"),
    "system_prompt": config.get("api", "system_prompt", fallback="你是英语句子解析助手，中文回答。")
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
