# 斯德哥尔摩保护者游戏 - AI 新闻系统

这个模块为你的可持续发展游戏添加了智能新闻生成功能，使用 OpenAI GPT API 动态创建符合游戏逻辑的新闻事件。

## 功能特点

- 🤖 **AI 动态新闻生成**: 使用 GPT-3.5 生成符合瑞典背景的新闻
- 🎲 **混合新闻系统**: AI 生成和预设新闻的智能混合
- 📊 **游戏平衡**: 根据新闻类型自动计算对游戏状态的影响
- 🔧 **可配置**: 支持调整 AI 使用概率和游戏难度
- 🛡️ **故障恢复**: API 失败时自动回退到预设新闻

## 文件结构

```
├── news_generator.py      # AI新闻生成核心逻辑
├── news_service.py        # 新闻服务统一接口
├── config.py             # 配置管理
├── main_with_ai_news.py  # 集成示例
├── requirements.txt      # 依赖包列表
└── AI_NEWS_README.md     # 使用说明（本文件）
```

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 OpenAI API 密钥

**方法一：环境变量（推荐）**

```bash
export OPENAI_API_KEY="your-api-key-here"
```

**方法二：代码中设置**

```python
from config import Config
Config.set_api_key("your-api-key-here")
```

**方法三：API 接口设置**

```bash
curl -X POST "http://localhost:8000/config/api-key?api_key=your-api-key-here"
```

### 3. 启动游戏

```bash
python main_with_ai_news.py
```

## 新闻类型和影响

| 新闻类型               | 金钱影响     | 幸福感影响 | CO2 影响  | 说明                     |
| ---------------------- | ------------ | ---------- | --------- | ------------------------ |
| `natural_disaster`     | -300 到 -100 | -15 到 -5  | -5 到 +5  | 自然灾害，如洪水、暴风雪 |
| `city_construction`    | -200 到 -50  | +3 到 +12  | +2 到 +8  | 城市建设项目             |
| `economy_growth`       | +150 到 +400 | +5 到 +12  | +3 到 +10 | 经济增长，就业增加       |
| `economy_decline`      | -350 到 -150 | -12 到 -4  | -5 到 0   | 经济衰退，失业率上升     |
| `sustainability_event` | -100 到 +50  | 0 到 +8    | -25 到 -5 | 环保活动，绿色技术       |
| `entertainment_news`   | -50 到 +100  | +8 到 +20  | +2 到 +8  | 文化活动，音乐节         |

## API 接口

### 基础新闻接口

- `GET /news` - 获取随机新闻（AI 或预设）
- `GET /news/type/{news_type}` - 获取指定类型新闻
- `GET /news/severity/{severity}` - 根据严重程度获取新闻
  - `low`: 娱乐、环保活动
  - `medium`: 城市建设
  - `high`: 自然灾害、重大经济变化

### AI 相关接口

- `GET /news/force-ai` - 强制使用 AI 生成新闻
- `GET /test/ai` - 测试 AI 功能是否正常
- `GET /news/statistics` - 获取新闻系统统计信息

### 配置接口

- `POST /config/api-key` - 设置 OpenAI API 密钥

## 与现有代码集成

### 方法一：替换现有新闻系统

在你的 `main.py` 中：

```python
# 替换原有的 generate_news() 函数
from news_service import NewsService

news_service = NewsService()

@app.get("/news")
def get_news():
    if game_state.game_over:
        return {"message": "Game over! Please restart the game."}

    news_event = news_service.generate_news()
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
```

### 方法二：添加新的 AI 新闻接口

保留现有接口，添加新的 AI 接口：

```python
from news_service import NewsService

news_service = NewsService()

@app.get("/news/ai")
def get_ai_news():
    # 你的AI新闻逻辑
    pass
```

## 配置选项

在 `config.py` 中可以调整以下参数：

```python
# AI新闻生成概率（0.0-1.0）
NEWS_GENERATION_PROBABILITY = 0.7

# 游戏难度倍数
EFFECT_MULTIPLIER = 1.0  # 1.5 = 困难模式，0.8 = 简单模式

# OpenAI API设置
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_MAX_TOKENS = 200
OPENAI_TEMPERATURE = 0.8
```

## 测试 AI 功能

### 测试 API 连接

```bash
curl http://localhost:8000/test/ai
```

### 获取 AI 统计信息

```bash
curl http://localhost:8000/news/statistics
```

### 强制生成 AI 新闻

```bash
curl http://localhost:8000/news/force-ai
```

## 故障排除

### 1. API 密钥问题

如果看到 "警告: 未设置 OPENAI_API_KEY 环境变量"：

- 检查环境变量是否正确设置
- 确认 API 密钥有效且有足够余额
- 使用 `/config/api-key` 接口重新设置

### 2. AI 生成失败

系统会自动回退到预设新闻，但可以检查：

- 网络连接是否正常
- API 密钥是否过期
- 调用频率是否超限

### 3. 新闻效果异常

检查 `config.py` 中的 `EFFECT_MULTIPLIER` 设置。

## 扩展开发

### 添加新的新闻类型

在 `news_generator.py` 的 `news_types` 字典中添加：

```python
"your_news_type": {
    "description": "你的新闻类型描述",
    "typical_effects": {"money": (-100, 100), "happiness": (-10, 10), "co2": (-5, 5)},
    "context": "新闻背景描述"
}
```

### 自定义提示词

修改 `_get_news_prompt()` 方法来调整 AI 生成的新闻风格。

### 添加更多效果类型

在游戏状态模型中添加新的属性，然后在效果计算中处理。

## 成本考虑

- GPT-3.5-turbo 调用成本约为每 1k token $0.002
- 每条新闻大约消耗 100-200 tokens
- 建议根据游戏规模调整 `NEWS_GENERATION_PROBABILITY`

## 注意事项

1. **API 限制**: OpenAI 有调用频率限制，高频游戏建议降低 AI 使用概率
2. **网络依赖**: AI 功能需要稳定的网络连接
3. **内容质量**: AI 生成的内容可能需要人工审核
4. **语言一致性**: 确保提示词和游戏语言环境一致

## 支持和贡献

如有问题或建议，欢迎提交 issue 或 pull request。

---

**祝你的斯德哥尔摩保护者游戏开发顺利！** 🎮🌱
