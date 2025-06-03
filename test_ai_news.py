#!/usr/bin/env python3
"""
AI新闻系统测试脚本
演示如何使用AI新闻生成功能
"""

from news_service import NewsService
from config import Config
import json

def test_ai_news_system():
    """测试AI新闻系统的各项功能"""
    
    print("=== 斯德哥尔摩保护者游戏 - AI新闻系统测试 ===\n")
    
    # 检查API密钥配置
    print("1. 检查配置...")
    if Config.validate_config():
        print("✅ OpenAI API密钥已配置")
    else:
        print("❌ 未设置OpenAI API密钥")
        print("   请设置环境变量: export OPENAI_API_KEY='your-key-here'")
        print("   或使用: Config.set_api_key('your-key-here')")
        return
    
    # 初始化新闻服务
    print("\n2. 初始化新闻服务...")
    news_service = NewsService()
    
    # 获取统计信息
    stats = news_service.get_news_statistics()
    print(f"   AI功能: {'启用' if stats['ai_enabled'] else '禁用'}")
    print(f"   预设新闻数量: {stats['preset_news_count']}")
    print(f"   AI使用概率: {stats['ai_probability']}%")
    
    # 测试AI连接
    print("\n3. 测试AI连接...")
    if news_service.test_ai_generation():
        print("✅ AI新闻生成测试通过")
    else:
        print("❌ AI新闻生成测试失败")
        return
    
    print("\n4. 生成不同类型的新闻...")
    
    # 测试不同类型的新闻
    news_types = [
        "natural_disaster",
        "city_construction", 
        "economy_growth",
        "sustainability_event",
        "entertainment_news"
    ]
    
    for news_type in news_types:
        print(f"\n--- {news_type} ---")
        try:
            # 强制使用AI生成特定类型新闻
            news = news_service.generate_news(news_type=news_type, force_ai=True)
            
            print(f"标题: {news.title}")
            print(f"描述: {news.description}")
            print(f"影响: {news.effects}")
            print(f"时间: {news.timestamp}")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
    
    print("\n5. 测试按严重程度生成新闻...")
    
    severities = ["low", "medium", "high"]
    for severity in severities:
        print(f"\n--- 严重程度: {severity} ---")
        try:
            news = news_service.generate_news_by_severity(severity)
            print(f"类型: {news.type}")
            print(f"标题: {news.title}")
            print(f"影响: {news.effects}")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
    
    print("\n6. 测试混合模式（AI + 预设）...")
    
    # 生成5条新闻，展示混合模式
    for i in range(5):
        print(f"\n--- 新闻 {i+1} ---")
        try:
            news = news_service.generate_news()
            is_ai = "AI生成" if news.title not in [n["title"] for n in news_service.preset_news] else "预设新闻"
            
            print(f"来源: {is_ai}")
            print(f"类型: {news.type}")
            print(f"标题: {news.title}")
            print(f"影响: {news.effects}")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n💡 使用建议:")
    print("1. 根据游戏频率调整 Config.NEWS_GENERATION_PROBABILITY")
    print("2. 使用 news_service.generate_news() 获取混合新闻")
    print("3. 使用 force_ai=True 参数强制AI生成")
    print("4. 检查 news.effects 来应用游戏状态变化")

def demo_integration():
    """演示如何在游戏中集成AI新闻"""
    
    print("\n=== 集成演示 ===")
    
    # 模拟游戏状态
    game_state = {
        "money": 1000,
        "happiness": 50,
        "co2": 50
    }
    
    print(f"初始状态: {game_state}")
    
    # 创建新闻服务
    news_service = NewsService()
    
    # 生成新闻并应用效果
    try:
        news = news_service.generate_news()
        
        print(f"\n📰 新闻: {news.title}")
        print(f"描述: {news.description}")
        print(f"影响: {news.effects}")
        
        # 应用效果到游戏状态
        for effect, value in news.effects.items():
            if effect in game_state:
                game_state[effect] += value
                # 确保数值在合理范围内
                if effect == "money":
                    game_state[effect] = max(0, game_state[effect])
                else:  # happiness, co2
                    game_state[effect] = max(0, min(100, game_state[effect]))
        
        print(f"\n更新后状态: {game_state}")
        
    except Exception as e:
        print(f"❌ 新闻生成失败: {e}")

if __name__ == "__main__":
    # 运行测试
    test_ai_news_system()
    
    # 演示集成
    demo_integration() 