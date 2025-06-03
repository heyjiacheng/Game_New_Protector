import random
from typing import Dict, Optional
from datetime import datetime

from config import Config
from news_generator import NewsGenerator, NewsEvent

class NewsService:
    """新闻服务类，管理AI生成和预设新闻"""
    
    def __init__(self):
        """初始化新闻服务"""
        self.ai_generator = None
        
        # 初始化AI新闻生成器
        if Config.validate_config():
            try:
                self.ai_generator = NewsGenerator(Config.OPENAI_API_KEY)
                print("AI新闻生成器已启用")
            except Exception as e:
                print(f"AI新闻生成器初始化失败: {e}")
                self.ai_generator = None
        
        # 预设新闻事件（作为备用）
        self.preset_news = [
            {
                "type": "natural_disaster",
                "title": "北方洪水肆虐",
                "description": "瑞典北部遭遇罕见洪水，基础设施受损",
                "effects": {"money": -200, "happiness": -10, "co2": 0}
            },
            {
                "type": "city_construction", 
                "title": "环保住宅建设",
                "description": "斯德哥尔摩新建环保住宅区",
                "effects": {"money": -150, "happiness": 8, "co2": 5}
            },
            {
                "type": "economy_growth",
                "title": "科技产业繁荣",
                "description": "瑞典科技产业蓬勃发展，创造大量就业机会",
                "effects": {"money": 300, "happiness": 7, "co2": 3}
            },
            {
                "type": "economy_decline",
                "title": "出口市场波动",
                "description": "全球市场波动影响瑞典出口",
                "effects": {"money": -250, "happiness": -8, "co2": -2}
            },
            {
                "type": "sustainability_event",
                "title": "国际环保会议",
                "description": "哥德堡举办国际环保会议，推广绿色技术",
                "effects": {"money": -50, "happiness": 5, "co2": -15}
            },
            {
                "type": "entertainment_news",
                "title": "马尔默音乐节",
                "description": "马尔默音乐节吸引全球游客，城市充满活力",
                "effects": {"money": 100, "happiness": 12, "co2": 5}
            }
        ]

    def _create_news_event_from_preset(self, preset: Dict) -> NewsEvent:
        """从预设数据创建新闻事件对象"""
        return NewsEvent(
            type=preset["type"],
            title=preset["title"],
            description=preset["description"],
            effects=preset["effects"],
            timestamp=datetime.now().isoformat()
        )

    def generate_news(self, news_type: Optional[str] = None, force_ai: bool = False) -> NewsEvent:
        """
        生成新闻事件
        
        Args:
            news_type: 指定新闻类型
            force_ai: 强制使用AI生成
            
        Returns:
            新闻事件对象
        """
        # 决定是否使用AI生成
        use_ai = force_ai or (
            self.ai_generator is not None and 
            random.random() < Config.NEWS_GENERATION_PROBABILITY
        )
        
        if use_ai and self.ai_generator:
            try:
                # 使用AI生成新闻
                ai_news = self.ai_generator.generate_news(news_type)
                
                # 应用难度倍数
                if Config.EFFECT_MULTIPLIER != 1.0:
                    for effect in ai_news.effects:
                        ai_news.effects[effect] = int(ai_news.effects[effect] * Config.EFFECT_MULTIPLIER)
                
                return ai_news
            except Exception as e:
                print(f"AI新闻生成失败，使用预设新闻: {e}")
        
        # 使用预设新闻
        if news_type:
            # 根据类型筛选预设新闻
            filtered_news = [n for n in self.preset_news if n["type"] == news_type]
            if filtered_news:
                preset = random.choice(filtered_news)
            else:
                preset = random.choice(self.preset_news)
        else:
            preset = random.choice(self.preset_news)
        
        # 为预设新闻添加一些随机性
        news_event = self._create_news_event_from_preset(preset)
        
        # 添加轻微的随机变化
        for effect in news_event.effects:
            variation = random.randint(-20, 20)  # ±20%的变化
            original_value = news_event.effects[effect]
            news_event.effects[effect] = int(original_value * (1 + variation / 100))
        
        # 应用难度倍数
        if Config.EFFECT_MULTIPLIER != 1.0:
            for effect in news_event.effects:
                news_event.effects[effect] = int(news_event.effects[effect] * Config.EFFECT_MULTIPLIER)
        
        return news_event

    def generate_news_by_severity(self, severity: str = "medium") -> NewsEvent:
        """
        根据严重程度生成新闻
        
        Args:
            severity: 严重程度 ("low", "medium", "high")
            
        Returns:
            新闻事件对象
        """
        if self.ai_generator and random.random() < Config.NEWS_GENERATION_PROBABILITY:
            try:
                return self.ai_generator.get_news_by_severity(severity)
            except Exception as e:
                print(f"AI新闻生成失败: {e}")
        
        # 根据严重程度选择预设新闻类型
        if severity == "low":
            news_types = ["entertainment_news", "sustainability_event"]
        elif severity == "high":
            news_types = ["natural_disaster", "economy_decline"]
        else:
            news_types = ["city_construction", "economy_growth"]
        
        return self.generate_news(random.choice(news_types))

    def get_news_statistics(self) -> Dict[str, int]:
        """获取新闻统计信息"""
        return {
            "ai_enabled": 1 if self.ai_generator else 0,
            "preset_news_count": len(self.preset_news),
            "ai_probability": int(Config.NEWS_GENERATION_PROBABILITY * 100)
        }

    def test_ai_generation(self) -> bool:
        """测试AI生成功能"""
        if not self.ai_generator:
            return False
        
        try:
            test_news = self.ai_generator.generate_news("sustainability_event")
            print(f"AI测试成功: {test_news.title}")
            return True
        except Exception as e:
            print(f"AI测试失败: {e}")
            return False 