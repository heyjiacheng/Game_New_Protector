from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from datetime import datetime
import uvicorn

# 导入新的AI新闻系统
from news_service import NewsService
from config import Config

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

# 初始化AI新闻服务
news_service = NewsService()

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
    "potogan": {"money": -200, "happiness": 10, "co2": -10}
}

# 能源来源影响
ENERGY_EFFECTS = {
    "mining": {"money": -30, "happiness": -10, "co2": 20},
    "water": {"money": -50, "happiness": 5, "co2": -8},
    "nuclear": {"money": -100, "happiness": -5, "co2": -15},
    "solar": {"money": -80, "happiness": 8, "co2": -12},
    "wind": {"money": -70, "happiness": 7, "co2": -10},
    "automic": {"money": -150, "happiness": 3, "co2": -20},
    "anti_material": {"money": -300, "happiness": 15, "co2": -30}
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
    """获取AI生成的新闻事件并更新状态"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    # 使用新的AI新闻服务生成新闻
    news_event = news_service.generate_news()
    
    # 将新闻转换为字典格式
    news_dict = {
        "type": news_event.type,
        "title": news_event.title,
        "description": news_event.description,
        "effects": news_event.effects,
        "timestamp": news_event.timestamp
    }
    
    # 应用新闻效果
    apply_effects(news_event.effects)
    
    # 保存最新新闻到游戏状态
    game_state.last_news = news_dict
    
    return news_dict

@app.get("/news/type/{news_type}")
def get_specific_news(news_type: str):
    """获取特定类型的新闻"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    try:
        news_event = news_service.generate_news(news_type=news_type)
        
        news_dict = {
            "type": news_event.type,
            "title": news_event.title,
            "description": news_event.description,
            "effects": news_event.effects,
            "timestamp": news_event.timestamp
        }
        
        apply_effects(news_event.effects)
        game_state.last_news = news_dict
        
        return news_dict
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/news/severity/{severity}")
def get_news_by_severity(severity: str):
    """根据严重程度获取新闻"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    if severity not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Severity must be 'low', 'medium', or 'high'")
    
    news_event = news_service.generate_news_by_severity(severity)
    
    news_dict = {
        "type": news_event.type,
        "title": news_event.title,
        "description": news_event.description,
        "effects": news_event.effects,
        "timestamp": news_event.timestamp
    }
    
    apply_effects(news_event.effects)
    game_state.last_news = news_dict
    
    return news_dict

@app.get("/news/force-ai")
def get_ai_news():
    """强制使用AI生成新闻（用于测试）"""
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}
    
    news_event = news_service.generate_news(force_ai=True)
    
    news_dict = {
        "type": news_event.type,
        "title": news_event.title,
        "description": news_event.description,
        "effects": news_event.effects,
        "timestamp": news_event.timestamp
    }
    
    apply_effects(news_event.effects)
    game_state.last_news = news_dict
    
    return news_dict

@app.get("/news/statistics")
def get_news_statistics():
    """获取新闻系统统计信息"""
    return news_service.get_news_statistics()

@app.post("/config/api-key")
def set_api_key(api_key: str):
    """设置OpenAI API密钥"""
    Config.set_api_key(api_key)
    global news_service
    news_service = NewsService()  # 重新初始化新闻服务
    return {"message": "API key updated", "ai_enabled": news_service.ai_generator is not None}

@app.get("/test/ai")
def test_ai():
    """测试AI新闻生成功能"""
    success = news_service.test_ai_generation()
    return {"ai_test_passed": success}

@app.post("/restart")
def restart_game():
    """重启游戏"""
    global game_state
    game_state = GameState()
    return {"message": "Game restarted", "state": game_state}

if __name__ == "__main__":
    uvicorn.run("main_with_ai_news:app", host="0.0.0.0", port=8000, reload=True) 