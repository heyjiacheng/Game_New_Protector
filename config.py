import os
from typing import Optional

class Config:
    """游戏配置类"""
    
    # OpenAI API配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # 游戏平衡设置
    NEWS_GENERATION_PROBABILITY = 0.7  # 生成AI新闻的概率，其余使用预设新闻
    
    # API调用设置
    OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS = 200
    OPENAI_TEMPERATURE = 0.8
    
    # 游戏难度设置
    EFFECT_MULTIPLIER = 1.0  # 效果倍数，可以调整游戏难度
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否有效"""
        if not cls.OPENAI_API_KEY:
            print("警告: 未设置 OPENAI_API_KEY 环境变量，将使用预设新闻")
            return False
        return True
    
    @classmethod
    def set_api_key(cls, api_key: str):
        """手动设置API密钥"""
        cls.OPENAI_API_KEY = api_key
        os.environ["OPENAI_API_KEY"] = api_key 