import openai
import random
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class NewsEvent(BaseModel):
    type: str
    title: str
    description: str
    effects: Dict[str, int]
    timestamp: str

class NewsGenerator:
    def __init__(self, api_key: str):
        """
        初始化新闻生成器
        
        Args:
            api_key: OpenAI API密钥
        """
        self.client = openai.OpenAI(api_key=api_key)
        
        # 新闻类型和对应的影响模板
        self.news_types = {
            "natural_disaster": {
                "description": "自然灾害相关新闻",
                "typical_effects": {"money": (-300, -100), "happiness": (-15, -5), "co2": (-5, 5)},
                "context": "瑞典面临的自然灾害，如洪水、暴风雪、干旱等"
            },
            "city_construction": {
                "description": "城市建设新闻",
                "typical_effects": {"money": (-200, -50), "happiness": (3, 12), "co2": (2, 8)},
                "context": "斯德哥尔摩及其他瑞典城市的基础设施建设项目"
            },
            "economy_growth": {
                "description": "经济增长新闻",
                "typical_effects": {"money": (150, 400), "happiness": (5, 12), "co2": (3, 10)},
                "context": "瑞典经济发展、就业增长、科技创新等积极经济新闻"
            },
            "economy_decline": {
                "description": "经济衰退新闻",
                "typical_effects": {"money": (-350, -150), "happiness": (-12, -4), "co2": (-5, 0)},
                "context": "经济困难、失业率上升、市场波动等负面经济新闻"
            },
            "sustainability_event": {
                "description": "可持续发展活动",
                "typical_effects": {"money": (-100, 50), "happiness": (0, 8), "co2": (-25, -5)},
                "context": "环保活动、绿色技术推广、可持续发展倡议"
            },
            "entertainment_news": {
                "description": "娱乐盛事新闻",
                "typical_effects": {"money": (-50, 100), "happiness": (8, 20), "co2": (2, 8)},
                "context": "文化活动、音乐节、体育赛事等娱乐新闻"
            }
        }

    def _get_news_prompt(self, news_type: str) -> str:
        """
        根据新闻类型生成对应的提示词
        
        Args:
            news_type: 新闻类型
            
        Returns:
            GPT提示词字符串
        """
        type_info = self.news_types[news_type]
        
        prompt = f"""
        请生成一条关于{type_info['description']}的新闻，背景是{type_info['context']}。

        要求：
        1. 新闻标题要简洁有力（8-15个汉字）
        2. 新闻描述要详细生动（60-120个汉字），包含具体的数据、地点、影响等信息
        3. 内容要符合瑞典的地理、文化和社会背景
        4. 可以提及具体的瑞典城市如斯德哥尔摩、哥德堡、马尔默、乌普萨拉等
        5. 语言要自然流畅，像真实的新闻报道
        6. 可以包含一些具体的数字、时间、机构名称等细节

        请直接返回纯JSON格式，不要包含任何markdown标记或代码块标记：
        {{"title": "新闻标题", "description": "详细的新闻描述"}}
        """
        
        return prompt.strip()

    def _clean_json_response(self, content: str) -> str:
        """
        清理GPT响应中的格式标记
        
        Args:
            content: GPT原始响应
            
        Returns:
            清理后的JSON字符串
        """
        # 移除markdown代码块标记
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'```$', '', content)
        
        # 移除其他可能的格式标记
        content = content.strip()
        
        # 如果内容不是以{开头，尝试找到JSON部分
        if not content.startswith('{'):
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
        
        return content

    def _calculate_effects(self, news_type: str) -> Dict[str, int]:
        """
        根据新闻类型计算随机效果值
        
        Args:
            news_type: 新闻类型
            
        Returns:
            包含money、happiness、co2效果的字典
        """
        type_info = self.news_types[news_type]
        effects = {}
        
        for effect, (min_val, max_val) in type_info["typical_effects"].items():
            # 添加一些随机性，让效果不那么固定
            base_effect = random.randint(min_val, max_val)
            # 20%的概率产生意外效果（相反或加强）
            if random.random() < 0.2:
                if random.random() < 0.5:
                    # 相反效果
                    base_effect = -base_effect // 2
                else:
                    # 加强效果
                    base_effect = int(base_effect * 1.5)
            
            effects[effect] = base_effect
        
        return effects

    def generate_news(self, news_type: Optional[str] = None) -> NewsEvent:
        """
        生成新闻事件
        
        Args:
            news_type: 指定新闻类型，如果为None则随机选择
            
        Returns:
            生成的新闻事件对象
        """
        if news_type is None:
            news_type = random.choice(list(self.news_types.keys()))
        
        if news_type not in self.news_types:
            raise ValueError(f"不支持的新闻类型: {news_type}")

        # 生成新闻内容
        prompt = self._get_news_prompt(news_type)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻编辑，专门为瑞典斯德哥尔摩的可持续发展游戏生成真实、详细的新闻。你的回复必须是纯JSON格式，不包含任何markdown或代码块标记。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            # 解析GPT响应
            content = response.choices[0].message.content.strip()
            
            # 清理格式标记
            clean_content = self._clean_json_response(content)
            
            # 尝试解析JSON
            try:
                news_data = json.loads(clean_content)
                title = news_data.get("title", "").strip()
                description = news_data.get("description", "").strip()
                
                # 确保标题和描述不为空
                if not title:
                    title = f"{self.news_types[news_type]['description']}事件"
                if not description:
                    description = "详情待更新"
                    
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始内容: {content}")
                print(f"清理后内容: {clean_content}")
                
                # 如果JSON解析失败，尝试从文本中提取信息
                title_match = re.search(r'"title":\s*"([^"]+)"', clean_content)
                desc_match = re.search(r'"description":\s*"([^"]+)"', clean_content)
                
                title = title_match.group(1) if title_match else f"{self.news_types[news_type]['description']}事件"
                description = desc_match.group(1) if desc_match else clean_content[:100] if clean_content else "AI生成的新闻事件"
        
        except Exception as e:
            print(f"调用GPT API失败: {e}")
            # 使用备用新闻
            title = f"{self.news_types[news_type]['description']}事件"
            description = f"系统生成的{news_type}相关新闻事件"

        # 计算效果
        effects = self._calculate_effects(news_type)
        
        # 创建新闻事件
        news_event = NewsEvent(
            type=news_type,
            title=title,
            description=description,
            effects=effects,
            timestamp=datetime.now().isoformat()
        )
        
        return news_event

    def generate_multiple_news(self, count: int = 3) -> List[NewsEvent]:
        """
        生成多条新闻
        
        Args:
            count: 生成新闻数量
            
        Returns:
            新闻事件列表
        """
        news_list = []
        for _ in range(count):
            try:
                news = self.generate_news()
                news_list.append(news)
            except Exception as e:
                print(f"生成新闻失败: {e}")
                continue
        
        return news_list

    def get_news_by_severity(self, severity: str = "medium") -> NewsEvent:
        """
        根据严重程度生成新闻
        
        Args:
            severity: 严重程度 ("low", "medium", "high")
            
        Returns:
            新闻事件对象
        """
        if severity == "low":
            # 低影响新闻：娱乐、小型可持续发展活动
            news_type = random.choice(["entertainment_news", "sustainability_event"])
        elif severity == "high":
            # 高影响新闻：自然灾害、重大经济变化
            news_type = random.choice(["natural_disaster", "economy_growth", "economy_decline"])
        else:
            # 中等影响新闻：城市建设
            news_type = "city_construction"
        
        return self.generate_news(news_type) 