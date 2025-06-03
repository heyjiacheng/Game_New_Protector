from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from datetime import datetime
import uvicorn

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 游戏状态模型
class GameState(BaseModel):
    money: int = 1000
    happiness: int = 50
    co2: int = 50
    transportation: str = "bicycle"
    energy_source: str = "solar"
    last_news: dict = None
    game_over: bool = False

# 初始游戏状态
game_state = GameState()

# 新闻事件类型
NEWS_EVENTS = [
    {
        "type": "natural_disaster",
        "title": "自然灾害",
        "description": "瑞典北部遭遇罕见洪水，基础设施受损",
        "effects": {"money": -200, "happiness": -10}
    },
    {
        "type": "city_construction",
        "title": "城市建设",
        "description": "斯德哥尔摩新建环保住宅区",
        "effects": {"co2": 5, "money": -150, "happiness": 8}
    },
    {
        "type": "economy_plus",
        "title": "经济利好",
        "description": "瑞典科技产业蓬勃发展，创造大量就业机会",
        "effects": {"money": 300, "happiness": 7, "co2": 3}
    },
    {
        "type": "economy_minus",
        "title": "经济衰退",
        "description": "全球市场波动影响瑞典出口",
        "effects": {"money": -250, "happiness": -8, "co2": -2}
    },
    {
        "type": "sustainability_event",
        "title": "可持续发展活动",
        "description": "哥德堡举办国际环保会议，推广绿色技术",
        "effects": {"co2": -15}
    },
    {
        "type": "entertainment_news",
        "title": "娱乐盛事",
        "description": "马尔默音乐节吸引全球游客，城市充满活力",
        "effects": {"happiness": 12}
    }
]

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
    "potogan": {"money": -200, "happiness": 10, "co2": -10}  # 假设是未来环保交通工具
}

# 能源来源影响
ENERGY_EFFECTS = {
    "mining": {"money": -30, "happiness": -10, "co2": 20},
    "water": {"money": -50, "happiness": 5, "co2": -8},
    "nuclear": {"money": -100, "happiness": -5, "co2": -15},
    "solar": {"money": -80, "happiness": 8, "co2": -12},
    "wind": {"money": -70, "happiness": 7, "co2": -10},
    "automic": {"money": -150, "happiness": 3, "co2": -20},  # 假设是自动化能源
    "anti_material": {"money": -300, "happiness": 15, "co2": -30}  # 假设是反物质能源
}

def apply_effects(effects):
    """应用效果到游戏状态"""
    global game_state
    
    if effects.get("money"):
        game_state.money += effects["money"]
    if effects.get("happiness"):
        game_state.happiness = max(0, min(100, game_state.happiness + effects["happiness"]))
    if effects.get("co2"):
        game_state.co2 = max(0, min(100, game_state.co2 + effects["co2"]))
    
    # 检查游戏结束条件
    if game_state.money <= 0 or game_state.happiness <= 0 or game_state.co2 >= 100:
        game_state.game_over = True

def generate_news():
    """生成随机新闻事件"""
    news = random.choice(NEWS_EVENTS)
    news["timestamp"] = datetime.now().isoformat()
    game_state.last_news = news
    apply_effects(news["effects"])
    return news

@app.get("/state")
def get_state():
    """获取当前游戏状态"""
    return game_state

@app.post("/action/transportation/{transport_type}")
def set_transportation(transport_type: str):
    """设置运输方式"""
    if transport_type not in TRANSPORTATION_EFFECTS:
        raise HTTPException(status_code=400, detail="Invalid transportation type")
    
    game_state.transportation = transport_type
    apply_effects(TRANSPORTATION_EFFECTS[transport_type])
    return {"message": f"Transportation set to {transport_type}", "state": game_state}

@app.post("/action/energy/{energy_type}")
def set_energy(energy_type: str):
    """设置能源来源"""
    if energy_type not in ENERGY_EFFECTS:
        raise HTTPException(status_code=400, detail="Invalid energy type")
    
    game_state.energy_source = energy_type
    apply_effects(ENERGY_EFFECTS[energy_type])
    return {"message": f"Energy source set to {energy_type}", "state": game_state}

@app.get("/news")
def get_news():
    """获取新闻事件并更新状态"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    news = generate_news()
    return news

@app.post("/restart")
def restart_game():
    """重启游戏"""
    global game_state
    game_state = GameState()
    return {"message": "Game restarted", "state": game_state}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)