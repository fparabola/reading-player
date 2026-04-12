"""
Prompt助手
用于管理和获取prompt模板
"""
from pathlib import Path
from typing import Optional


class PromptHelper:
    """
    Prompt助手类
    """
    
    def __init__(self, prompt_dir: str = None):
        """
        初始化Prompt助手
        
        参数:
        - prompt_dir: prompt目录路径
        """
        if prompt_dir:
            self.prompt_dir = Path(prompt_dir)
        else:
            self.prompt_dir = Path(__file__).parent.parent / "prompt"
    
    def get_prompt(self, relative_path: str, file_name: str) -> Optional[str]:
        """
        根据相对路径和文件名（省略后缀）获取prompt字符串
        
        参数:
        - relative_path: 相对于prompt目录的路径
        - file_name: 文件名（省略后缀）
        
        返回:
        - prompt字符串，如果文件不存在则返回None
        """
        # 构建完整的文件路径
        prompt_path = self.prompt_dir / relative_path / f"{file_name}.md"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            # 如果文件不存在或读取失败，返回None
            return None
    
    def get_prompt_with_text(self, relative_path: str, file_name: str, text: str) -> Optional[str]:
        """
        根据相对路径和文件名（省略后缀）获取prompt字符串，并替换{text}占位符
        
        参数:
        - relative_path: 相对于prompt目录的路径
        - file_name: 文件名（省略后缀）
        - text: 要替换的文本
        
        返回:
        - 替换后的prompt字符串，如果文件不存在则返回None
        """
        prompt = self.get_prompt(relative_path, file_name)
        if prompt:
            return prompt.replace("{text}", text)
        return None


# 创建全局Prompt助手实例
prompt_helper = PromptHelper()
