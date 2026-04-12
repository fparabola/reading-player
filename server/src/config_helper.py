"""
配置助手
用于统一管理配置的读取和访问
"""
import configparser
from pathlib import Path


class ConfigError(Exception):
    """
    配置错误异常
    """
    pass


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
            self.config_path = Path(__file__).parent.parent / "config.ini"
        self._load_config()
    
    def _load_config(self):
        """
        加载配置文件
        """
        self.config.read(self.config_path, encoding='utf-8')
    
    def get(self, config_name: str) -> str:
        """
        获取配置值
        
        参数:
        - config_name: 配置名，格式为 "section.key"
        
        返回:
        - 配置值
        
        异常:
        - ConfigError: 当配置不存在时抛出
        """
        try:
            section, key = config_name.split('.', 1)
        except ValueError:
            raise ConfigError(f"Invalid config name format: {config_name}")
        
        if not self.config.has_section(section):
            raise ConfigError(f"Section '{section}' not found in config")
        if not self.config.has_option(section, key):
            raise ConfigError(f"Key '{key}' not found in section '{section}'")
        
        return self.config.get(section, key)


# 创建全局配置助手实例
config_helper = ConfigHelper()
