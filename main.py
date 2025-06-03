from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import random
from datetime import datetime
import uvicorn
import copy

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

# 新闻事件类型
NEWS_EVENTS = [
    {
        "type": "natural_disaster",
        "title": "自然灾害",
        "description": "瑞典北部遭遇罕见洪水，基础设施受损",
        "effects": {"money": -200, "happiness": -10, "city": None}
    },
    {
        "type": "city_construction",
        "title": "城市建设",
        "description": "斯德哥尔摩新建环保住宅区",
        "effects": {"co2": 5, "money": -150, "happiness": 8, "city": "stockholm"}
    },
    {
        "type": "economy_plus",
        "title": "经济利好",
        "description": "瑞典科技产业蓬勃发展，创造大量就业机会",
        "effects": {"money": 300, "happiness": 7, "co2": 3, "city": None}
    },
    {
        "type": "economy_minus",
        "title": "经济衰退",
        "description": "全球市场波动影响瑞典出口",
        "effects": {"money": -250, "happiness": -8, "co2": -2, "city": None}
    },
    {
        "type": "sustainability_event",
        "title": "可持续发展活动",
        "description": "哥德堡举办国际环保会议，推广绿色技术",
        "effects": {"co2": -15, "city": "gothenburg"}
    },
    {
        "type": "entertainment_news",
        "title": "娱乐盛事",
        "description": "马尔默音乐节吸引全球游客，城市充满活力",
        "effects": {"happiness": 12, "city": "malmo"}
    }
]

# 针对各城市的事件
CITY_SPECIFIC_NEWS = {
    "stockholm": [
        {
            "type": "local_event",
            "title": "斯德哥尔摩创新中心",
            "description": "斯德哥尔摩新建技术创新中心，吸引全球人才",
            "effects": {"happiness": 8, "co2": 5, "money": -100}
        },
        {
            "type": "local_disaster",
            "title": "斯德哥尔摩严寒",
            "description": "斯德哥尔摩遭遇极寒天气，能源消耗大幅增加",
            "effects": {"happiness": -5, "co2": 10, "money": -80}
        }
    ],
    "gothenburg": [
        {
            "type": "local_event",
            "title": "哥德堡港口扩建",
            "description": "哥德堡港口扩建工程完成，贸易量大幅增加",
            "effects": {"happiness": 5, "co2": 8, "money": 150}
        },
        {
            "type": "local_disaster",
            "title": "哥德堡洪水",
            "description": "哥德堡遭遇洪水袭击，沿海地区受损",
            "effects": {"happiness": -8, "co2": 3, "money": -120}
        }
    ],
    "malmo": [
        {
            "type": "local_event",
            "title": "马尔默可再生能源",
            "description": "马尔默实施大规模可再生能源计划，城市形象提升",
            "effects": {"happiness": 10, "co2": -12, "money": -180}
        },
        {
            "type": "local_disaster",
            "title": "马尔默交通拥堵",
            "description": "马尔默交通严重拥堵，市民出行困难",
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

def generate_news():
    """生成随机新闻事件"""
    # 70%概率生成全国性新闻，30%概率生成城市特定新闻
    if random.random() < 0.7:
        news = random.choice(NEWS_EVENTS)
    else:
        # 选择一个未被淘汰的城市
        available_cities = [city_id for city_id, city in game_state.cities.items() if not city.eliminated]
        if not available_cities:
            # 如果所有城市都被淘汰，生成全国性新闻
            news = random.choice(NEWS_EVENTS)
        else:
            city_id = random.choice(available_cities)
            city_news = CITY_SPECIFIC_NEWS.get(city_id, [])
            if not city_news:
                news = random.choice(NEWS_EVENTS)
            else:
                news = random.choice(city_news)
                news["effects"]["city"] = city_id
    
    news["timestamp"] = datetime.now().isoformat()
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
    
    # 生成新闻
    news = generate_news()
    
    return {"news": news, "year": game_state.year, "state": game_state}

@app.get("/news")
def get_news():
    """获取新闻事件并更新状态 (保留以兼容旧版)"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    news = generate_news()
    return news

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