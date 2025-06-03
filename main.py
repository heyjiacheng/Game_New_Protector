from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import random
from datetime import datetime
import uvicorn
import copy

# 导入新的AI新闻系统
try:
    from news_service import NewsService
    from config import Config
    news_service_available = True
except ImportError:
    news_service_available = False
    print("Warning: AI news service not available. Install news_service and config modules for AI functionality.")

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 城市模型
class City(BaseModel):
    name: str
    happiness: int = 50
    co2: int = 50
    transportation: str = "bicycle"
    energy_source: str = "solar"
    eliminated: bool = False
    position: Dict[str, int] = {}  # 城市在地图上的位置

# 回合中的变更
class RoundChanges(BaseModel):
    transportation: Dict[str, str] = {}
    energy_source: Dict[str, str] = {}
    projected_effects: Dict[str, Dict[str, int]] = {}

# 游戏状态模型
class GameState(BaseModel):
    money: int = 1000
    cities: Dict[str, City] = {}
    last_news: dict = None
    game_over: bool = False
    year: int = 1  # 添加年份
    current_round_changes: RoundChanges = RoundChanges()

# 初始城市状态 - 存储原始值以便正确重置
initial_cities_data = {
    "stockholm": {
        "name": "Stockholm", 
        "happiness": 60, 
        "co2": 40, 
        "transportation": "bicycle", 
        "energy_source": "solar",
        "position": {"x": 300, "y": 180}
    },
    "gothenburg": {
        "name": "Gothenburg", 
        "happiness": 50, 
        "co2": 45, 
        "transportation": "bicycle", 
        "energy_source": "solar",
        "position": {"x": 150, "y": 300}
    },
    "malmo": {
        "name": "Malmö", 
        "happiness": 55, 
        "co2": 50, 
        "transportation": "bicycle", 
        "energy_source": "solar",
        "position": {"x": 180, "y": 420}
    }
}

# 初始化三个瑞典城市
initial_cities = {
    city_id: City(**data) for city_id, data in initial_cities_data.items()
}

# 初始游戏状态
game_state = GameState(cities=initial_cities)

# 初始化AI新闻服务
news_service = None
if news_service_available:
    try:
        news_service = NewsService()
    except Exception as e:
        print(f"Warning: Failed to initialize AI news service: {e}")
        news_service_available = False

# 新闻事件类型
NEWS_EVENTS = [
    {
        "type": "natural_disaster",
        "title": "Natural Disaster",
        "description": "Rare floods hit northern Sweden, damaging infrastructure",
        "effects": {"money": -200, "happiness": -10, "city": None}
    },
    {
        "type": "city_construction",
        "title": "City Construction",
        "description": "Stockholm builds new eco-friendly residential area",
        "effects": {"co2": 5, "money": -150, "happiness": 8, "city": "stockholm"}
    },
    {
        "type": "economy_plus",
        "title": "Economic Growth",
        "description": "Swedish tech industry flourishes, creating many job opportunities",
        "effects": {"money": 300, "happiness": 7, "co2": 3, "city": None}
    },
    {
        "type": "economy_minus",
        "title": "Economic Downturn",
        "description": "Global market fluctuations impact Swedish exports",
        "effects": {"money": -250, "happiness": -8, "co2": -2, "city": None}
    },
    {
        "type": "sustainability_event",
        "title": "Sustainability Initiative",
        "description": "Gothenburg hosts international environmental conference promoting green technology",
        "effects": {"co2": -15, "city": "gothenburg"}
    },
    {
        "type": "entertainment_news",
        "title": "Entertainment Event",
        "description": "Malmö music festival attracts global visitors, energizing the city",
        "effects": {"happiness": 12, "city": "malmo"}
    }
]

# 针对各城市的事件
CITY_SPECIFIC_NEWS = {
    "stockholm": [
        {
            "type": "local_event",
            "title": "Stockholm Innovation Center",
            "description": "Stockholm builds a new technology innovation center, attracting global talent",
            "effects": {"happiness": 8, "co2": 5, "money": -100}
        },
        {
            "type": "local_disaster",
            "title": "Stockholm Severe Cold",
            "description": "Stockholm experiences extremely cold weather, significantly increasing energy consumption",
            "effects": {"happiness": -5, "co2": 10, "money": -80}
        }
    ],
    "gothenburg": [
        {
            "type": "local_event",
            "title": "Gothenburg Port Expansion",
            "description": "Gothenburg port expansion completed, significantly increasing trade volume",
            "effects": {"happiness": 5, "co2": 8, "money": 150}
        },
        {
            "type": "local_disaster",
            "title": "Gothenburg Flooding",
            "description": "Gothenburg hit by flooding, coastal areas damaged",
            "effects": {"happiness": -8, "co2": 3, "money": -120}
        }
    ],
    "malmo": [
        {
            "type": "local_event",
            "title": "Malmö Renewable Energy",
            "description": "Malmö implements large-scale renewable energy plan, improving city image",
            "effects": {"happiness": 10, "co2": -12, "money": -180}
        },
        {
            "type": "local_disaster",
            "title": "Malmö Traffic Congestion",
            "description": "Severe traffic congestion in Malmö, citizens face difficulties commuting",
            "effects": {"happiness": -7, "co2": 9, "money": -50}
        }
    ]
}

# 运输方式影响
TRANSPORTATION_EFFECTS = {
    "bicycle": {"money": -5, "happiness": 3, "co2": -8},
    "scooter": {"money": -10, "happiness": 2, "co2": -5},
    "car": {"money": -50, "happiness": -5, "co2": 15},
    "electronic_car": {"money": -70, "happiness": 2, "co2": 5},
    "bus": {"money": -20, "happiness": -2, "co2": 8},
    "electronic_bus": {"money": -30, "happiness": 1, "co2": 3},
    "train": {"money": -25, "happiness": 4, "co2": 4},
    "airplane": {"money": -150, "happiness": 6, "co2": 40},
    "potogan": {"money": -200, "happiness": 10, "co2": -10}  # 未来环保交通工具
}

# 能源来源影响
ENERGY_EFFECTS = {
    "mining": {"money": -30, "happiness": -10, "co2": 20},
    "water": {"money": -50, "happiness": 5, "co2": -8},
    "nuclear": {"money": -100, "happiness": -5, "co2": -15},
    "solar": {"money": -80, "happiness": 8, "co2": -12},
    "wind": {"money": -70, "happiness": 7, "co2": -10},
    "automic": {"money": -150, "happiness": 3, "co2": -20},  # 自动化能源
    "anti_material": {"money": -300, "happiness": 15, "co2": -30}  # 反物质能源
}

def calculate_projected_effects(city_id, transport_type=None, energy_type=None):
    """计算预期的效果而不实际应用"""
    effects = {"money": 0, "happiness": 0, "co2": 0}
    
    # 如果指定了交通类型,计算其影响
    if transport_type and transport_type in TRANSPORTATION_EFFECTS:
        for key, value in TRANSPORTATION_EFFECTS[transport_type].items():
            effects[key] += value
    
    # 如果指定了能源类型,计算其影响
    if energy_type and energy_type in ENERGY_EFFECTS:
        for key, value in ENERGY_EFFECTS[energy_type].items():
            effects[key] += value
    
    # 存储计算的影响
    if city_id not in game_state.current_round_changes.projected_effects:
        game_state.current_round_changes.projected_effects[city_id] = effects
    else:
        # 如果已存在预测,则更新
        for key, value in effects.items():
            game_state.current_round_changes.projected_effects[city_id][key] = value
    
    return effects

def apply_effects(effects, city_id=None):
    """应用效果到游戏状态或特定城市"""
    global game_state
    
    # 应用金钱效果 (全局)
    if effects.get("money"):
        game_state.money += effects["money"]
    
    # 确定受影响的城市
    target_cities = []
    if city_id and city_id in game_state.cities:
        # 特定城市受影响
        target_cities = [city_id]
    elif effects.get("city") and effects["city"] in game_state.cities:
        # 新闻事件中指定的城市
        target_cities = [effects["city"]]
    else:
        # 影响所有城市
        target_cities = list(game_state.cities.keys())
    
    # 对每个受影响的城市应用效果
    for city_id in target_cities:
        city = game_state.cities[city_id]
        if not city.eliminated:
            if effects.get("happiness"):
                city.happiness = max(0, min(100, city.happiness + effects["happiness"]))
            if effects.get("co2"):
                city.co2 = max(0, min(100, city.co2 + effects["co2"]))
            
            # 检查城市是否应被淘汰
            if city.happiness <= 0 or city.co2 >= 100:
                city.eliminated = True
    
    # 检查游戏结束条件
    check_game_over()

def check_game_over():
    """检查游戏是否结束"""
    global game_state
    
    # 金钱小于等于0，游戏结束
    if game_state.money <= 0:
        game_state.game_over = True
        return
    
    # 所有城市都被淘汰，游戏结束
    all_eliminated = all(city.eliminated for city in game_state.cities.values())
    if all_eliminated:
        game_state.game_over = True

def generate_news(use_ai=False, news_type=None, severity=None, force_ai=False):
    """生成新闻事件，支持AI和传统新闻"""
    news = None
    
    # 如果请求使用AI且AI服务可用
    if (use_ai or force_ai) and news_service_available and news_service:
        try:
            if news_type:
                news_event = news_service.generate_news(news_type=news_type)
            elif severity:
                news_event = news_service.generate_news_by_severity(severity)
            else:
                news_event = news_service.generate_news(force_ai=force_ai)
            
            # 将AI新闻事件转换为字典格式
            news = {
                "type": news_event.type,
                "title": news_event.title,
                "description": news_event.description,
                "effects": news_event.effects,
                "timestamp": news_event.timestamp,
                "source": "AI"
            }
        except Exception as e:
            print(f"AI news generation failed: {e}")
            # 如果AI生成失败，回退到传统新闻
            news = None
    
    # 如果没有使用AI或AI生成失败，使用传统新闻生成
    if not news:
        # 70%概率生成全国性新闻，30%概率生成城市特定新闻
        if random.random() < 0.7:
            news = random.choice(NEWS_EVENTS).copy()
        else:
            # 选择一个未被淘汰的城市
            available_cities = [city_id for city_id, city in game_state.cities.items() if not city.eliminated]
            if not available_cities:
                # 如果所有城市都被淘汰，生成全国性新闻
                news = random.choice(NEWS_EVENTS).copy()
            else:
                city_id = random.choice(available_cities)
                city_news = CITY_SPECIFIC_NEWS.get(city_id, [])
                if not city_news:
                    news = random.choice(NEWS_EVENTS).copy()
                else:
                    news = random.choice(city_news).copy()
                    news["effects"]["city"] = city_id
        
        news["timestamp"] = datetime.now().isoformat()
        news["source"] = "Traditional"
    
    game_state.last_news = news
    
    # 应用新闻效果
    apply_effects(news["effects"])
    
    return news

@app.get("/state")
def get_state():
    """获取当前游戏状态"""
    return game_state

@app.post("/action/transportation/{city_id}/{transport_type}")
def set_transportation(city_id: str, transport_type: str):
    """为指定城市设置运输方式(仅预览效果)"""
    if transport_type not in TRANSPORTATION_EFFECTS:
        raise HTTPException(status_code=400, detail="Invalid transportation type")
    
    if city_id not in game_state.cities:
        raise HTTPException(status_code=404, detail="City not found")
    
    if game_state.cities[city_id].eliminated:
        raise HTTPException(status_code=400, detail="This city has been eliminated")
    
    # 保存到当前回合更改
    game_state.current_round_changes.transportation[city_id] = transport_type
    
    # 计算预期效果
    effects = calculate_projected_effects(
        city_id, 
        transport_type=transport_type, 
        energy_type=game_state.current_round_changes.energy_source.get(city_id, game_state.cities[city_id].energy_source)
    )
    
    return {
        "message": f"Transportation for {city_id} set to {transport_type}", 
        "state": game_state,
        "projected_effects": effects
    }

@app.post("/action/energy/{city_id}/{energy_type}")
def set_energy(city_id: str, energy_type: str):
    """为指定城市设置能源来源(仅预览效果)"""
    if energy_type not in ENERGY_EFFECTS:
        raise HTTPException(status_code=400, detail="Invalid energy type")
    
    if city_id not in game_state.cities:
        raise HTTPException(status_code=404, detail="City not found")
    
    if game_state.cities[city_id].eliminated:
        raise HTTPException(status_code=400, detail="This city has been eliminated")
    
    # 保存到当前回合更改
    game_state.current_round_changes.energy_source[city_id] = energy_type
    
    # 计算预期效果
    effects = calculate_projected_effects(
        city_id, 
        transport_type=game_state.current_round_changes.transportation.get(city_id, game_state.cities[city_id].transportation),
        energy_type=energy_type
    )
    
    return {
        "message": f"Energy source for {city_id} set to {energy_type}", 
        "state": game_state,
        "projected_effects": effects
    }

@app.post("/next-round")
def next_round():
    """进入下一回合，应用当前更改，更新年份并生成新闻"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    # 应用当前回合中的所有更改
    total_money_change = 0
    
    # 应用交通方式变更
    for city_id, transport_type in game_state.current_round_changes.transportation.items():
        if city_id in game_state.cities and not game_state.cities[city_id].eliminated:
            # 只有当设置确实发生变化时才应用效果
            if game_state.cities[city_id].transportation != transport_type:
                effects = TRANSPORTATION_EFFECTS[transport_type]
                
                # 应用金钱效果（累积）
                if "money" in effects:
                    total_money_change += effects["money"]
                
                # 应用其他效果
                for key, value in effects.items():
                    if key == "happiness":
                        game_state.cities[city_id].happiness = max(0, min(100, game_state.cities[city_id].happiness + value))
                    elif key == "co2":
                        game_state.cities[city_id].co2 = max(0, min(100, game_state.cities[city_id].co2 + value))
                
                # 更新城市的交通设置
                game_state.cities[city_id].transportation = transport_type
    
    # 应用能源来源变更
    for city_id, energy_type in game_state.current_round_changes.energy_source.items():
        if city_id in game_state.cities and not game_state.cities[city_id].eliminated:
            # 只有当设置确实发生变化时才应用效果
            if game_state.cities[city_id].energy_source != energy_type:
                effects = ENERGY_EFFECTS[energy_type]
                
                # 应用金钱效果（累积）
                if "money" in effects:
                    total_money_change += effects["money"]
                
                # 应用其他效果
                for key, value in effects.items():
                    if key == "happiness":
                        game_state.cities[city_id].happiness = max(0, min(100, game_state.cities[city_id].happiness + value))
                    elif key == "co2":
                        game_state.cities[city_id].co2 = max(0, min(100, game_state.cities[city_id].co2 + value))
                
                # 更新城市的能源设置
                game_state.cities[city_id].energy_source = energy_type
    
    # 应用总体金钱变化
    game_state.money += total_money_change
    
    # 检查城市是否应被淘汰
    for city_id, city in game_state.cities.items():
        if not city.eliminated and (city.happiness <= 0 or city.co2 >= 100):
            city.eliminated = True
    
    # 检查游戏结束条件
    check_game_over()
    
    # 增加年份
    game_state.year += 1
    
    # 清除当前回合的更改
    game_state.current_round_changes = RoundChanges()
    
    # 生成新闻（默认使用传统新闻，可以通过其他端点获取AI新闻）
    news = generate_news()
    
    return {"news": news, "year": game_state.year, "state": game_state}

@app.get("/news")
def get_news():
    """获取新闻事件并更新状态 (保留以兼容旧版)"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    news = generate_news()
    return news

# ===== AI新闻相关端点 =====

@app.get("/news/ai")
def get_ai_news():
    """获取AI生成的新闻事件并更新状态"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    if not news_service_available or not news_service:
        raise HTTPException(status_code=503, detail="AI news service not available")
    
    news = generate_news(use_ai=True)
    return news

@app.get("/news/type/{news_type}")
def get_specific_news(news_type: str):
    """获取特定类型的新闻"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    if not news_service_available or not news_service:
        raise HTTPException(status_code=503, detail="AI news service not available")
    
    try:
        news = generate_news(use_ai=True, news_type=news_type)
        return news
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/news/severity/{severity}")
def get_news_by_severity(severity: str):
    """根据严重程度获取新闻"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    if severity not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Severity must be 'low', 'medium', or 'high'")
    
    if not news_service_available or not news_service:
        raise HTTPException(status_code=503, detail="AI news service not available")
    
    news = generate_news(use_ai=True, severity=severity)
    return news

@app.get("/news/force-ai")
def get_force_ai_news():
    """强制使用AI生成新闻（用于测试）"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    if not news_service_available or not news_service:
        raise HTTPException(status_code=503, detail="AI news service not available")
    
    news = generate_news(force_ai=True)
    return news

@app.get("/news/statistics")
def get_news_statistics():
    """获取新闻系统统计信息"""
    if not news_service_available or not news_service:
        raise HTTPException(status_code=503, detail="AI news service not available")
    
    return news_service.get_news_statistics()

@app.post("/config/api-key")
def set_api_key(api_key: str):
    """设置OpenAI API密钥"""
    if not news_service_available:
        raise HTTPException(status_code=503, detail="AI news service not available")
    
    Config.set_api_key(api_key)
    global news_service
    news_service = NewsService()  # 重新初始化新闻服务
    return {"message": "API key updated", "ai_enabled": news_service.ai_generator is not None}

@app.get("/test/ai")
def test_ai():
    """测试AI新闻生成功能"""
    if not news_service_available or not news_service:
        return {"ai_test_passed": False, "message": "AI news service not available"}
    
    success = news_service.test_ai_generation()
    return {"ai_test_passed": success}

# ===== 传统游戏端点保持不变 =====

@app.post("/restart")
def restart_game():
    """重启游戏"""
    global game_state
    
    # 创建一个新的GameState实例，使用原始城市数据
    new_cities = {}
    for city_id, data in initial_cities_data.items():
        # 创建全新的城市对象，确保完全重置所有属性
        new_cities[city_id] = City(**data)
    
    # 创建新的游戏状态
    game_state = GameState(cities=new_cities, year=1)
    
    return {"message": "Game restarted", "state": game_state}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)