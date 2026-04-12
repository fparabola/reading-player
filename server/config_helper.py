"""
配置助手
用于统一管理配置的读取和访问
"""
import configparser
from pathlib import Path


class ConfigHelper:
    """
    配置助手类
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化配置助手
        
        参数:
        - config_path: 配置文件路径
        """
        self.config = configparser.ConfigParser()
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent / "config.ini"
        self._load_config()
    
    def _load_config(self):
        """
        加载配置文件
        """
        self.config.read(self.config_path, encoding='utf-8')
    
    def get(self, section: str, key: str, fallback=None):
        """
        获取配置值
        
        参数:
        - section: 配置节
        - key: 配置键
        - fallback: 默认值
        
        返回:
        - 配置值
        """
        if not self.config.has_section(section):
            return fallback
        if not self.config.has_option(section, key):
            return fallback
        return self.config.get(section, key)
    
    def get_api_key(self) -> str:
        """
        获取API密钥
        
        返回:
        - API密钥
        """
        return self.get("auth", "siliconflow_api_key")
    
    def get_base_url(self) -> str:
        """
        获取API基础URL
        
        返回:
        - API基础URL
        """
        return self.get("api", "base_url", fallback="https://api.siliconflow.cn/v1")
    
    def get_default_model(self) -> str:
        """
        获取默认模型名称
        
        返回:
        - 默认模型名称
        """
        return self.get("api", "default_model", fallback="Qwen/Qwen3-14B")
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示语
        
        返回:
        - 系统提示语
        """
        return self.get("api", "system_prompt", fallback="你是英语句子解析助手，中文回答。")


# 创建全局配置助手实例
config_helper = ConfigHelper()
