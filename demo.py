"""
Bingo Card Agent - Live Demo
完整展示系統功能
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

from src.models import (
    UserProfile,
    EngagementState,
    BehavioralArchetype,
    TripHistory,
    BingoHistory,
    TransportMode,
    FeedbackEvent,
)
from src.memory import SQLiteMemoryStore
from src.graph import BingoAgentGraph, LLMBingoAgentGraph


def print_header(text):
    """打印標題"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_section(text):
    """打印小節"""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}\n")


async def demo_1_create_user():
    """Demo 1: 創建用戶並生成第一張卡片"""
    print_header("DEMO 1: 創建新用戶並生成第一張卡片")

    # 初始化
    memory = SQLiteMemoryStore(db_path="./demo.db")
    await memory.initialize()
    print("✅ 數據庫初始化完成")

    # 創建新用戶
    print("\n📝 創建新用戶檔案...")
    user = UserProfile(
        user_id="demo_user_001",
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
        trip_history=TripHistory(
            primary_modes=[TransportMode.DRIVING],
            trip_frequency=15,
            common_travel_times=["AM_Commuter", "PM_Commuter"],
            mode_distribution={TransportMode.DRIVING: 15}
        ),
        bingo_history=BingoHistory(
            cards_offered=0,
            cards_participated=0,
            cards_completed=0,
        )
    )
    await memory.save_user_profile(user)

    print(f"✅ 用戶創建成功！")
    print(f"   User ID: {user.user_id}")
    print(f"   狀態: {user.current_engagement_state}")
    print(f"   類型: {user.behavioral_archetype}")
    print(f"   主要交通方式: {', '.join([m.value for m in user.trip_history.primary_modes])}")

    # 使用標準 agent 生成卡片
    print("\n🎲 使用標準 Agent 生成卡片...")
    agent = BingoAgentGraph(memory)
    result = await agent.generate_card_for_user("demo_user_001")

    if result.card_generation_response and result.card_generation_response.success:
        card = result.card_generation_response.card
        print(f"\n✅ 卡片生成成功！")
        print(f"   卡片 ID: {card.card_id}")
        print(f"   維度: {card.dimension.value}")
        print(f"   難度配置: {card.tile_profile.value}")
        print(f"   持續時間: {card.duration_days} 天")
        print(f"   到期時間: {card.expires_at.strftime('%Y-%m-%d %H:%M')}")

        print(f"\n📋 卡片方塊 ({len(card.tiles)} 個):")
        for i, tile in enumerate(card.tiles, 1):
            mode_str = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[一般]"
            nudge = "🎯" if tile.is_nudge else "  "
            diff = "⭐" * int(tile.difficulty_score)
            print(f"   {i:2d}. {nudge} {tile.description:40s} {mode_str:10s} {diff}")

        print(f"\n💡 分析:")
        print(f"   - 這是新用戶，系統選擇了 '{card.tile_profile.value}' 配置")
        print(f"   - 大部分方塊都是熟悉的駕駛相關任務")
        print(f"   - 包含少量簡單任務來建立信心")
        print(f"   - 使用 3x3 小卡片，7天期限，降低難度")

    else:
        print(f"❌ 卡片生成失敗: {result.card_generation_response.reason if result.card_generation_response else '未知錯誤'}")

    return memory


async def demo_2_user_completes_card(memory):
    """Demo 2: 用戶完成卡片並獲得反饋"""
    print_header("DEMO 2: 用戶完成卡片")

    agent = BingoAgentGraph(memory)

    # 獲取用戶的卡片
    card = await memory.get_active_card("demo_user_001")
    if not card:
        print("❌ 沒有找到活躍的卡片")
        return

    print(f"📊 當前卡片狀態:")
    print(f"   進度: {card.progress_percentage:.0f}%")
    print(f"   已完成: {len(card.tiles_completed)}/{len(card.tiles)} 個方塊")

    # 模擬用戶開始卡片
    print(f"\n🎮 用戶開始卡片...")
    feedback1 = FeedbackEvent(
        user_id="demo_user_001",
        card_id=card.card_id,
        event_type="card_started",
        metadata={"source": "mobile_app"}
    )
    await memory.save_feedback(feedback1)

    # 更新卡片狀態
    card.started = True
    card.started_at = datetime.now()
    await memory.save_bingo_card(card)

    print(f"✅ 卡片已開始")

    # 模擬完成一些方塊
    print(f"\n📝 用戶完成方塊...")
    tiles_to_complete = min(7, len(card.tiles))  # 完成大部分方塊
    for i in range(tiles_to_complete):
        card.tiles[i].completed = True
        card.tiles[i].completed_at = datetime.now()
        print(f"   ✓ 完成: {card.tiles[i].description}")

    await memory.save_bingo_card(card)

    # 模擬完成整張卡片
    print(f"\n🎉 用戶完成剩餘方塊...")
    for i in range(tiles_to_complete, len(card.tiles)):
        card.tiles[i].completed = True
        card.tiles[i].completed_at = datetime.now()

    card.completed = True
    card.completed_at = datetime.now()
    await memory.save_bingo_card(card)

    print(f"✅ 卡片完成！")

    # 記錄完成反饋
    feedback2 = FeedbackEvent(
        user_id="demo_user_001",
        card_id=card.card_id,
        event_type="card_completed",
        metadata={"completion_time_hours": 24, "first_completion": True},
        reward_score=100.0
    )
    await memory.save_feedback(feedback2)

    print(f"\n🏆 獎勵:")
    print(f"   +100 分（完成卡片）")
    print(f"   +20 分（快速完成獎勵）")
    print(f"   +50 分（首次完成獎勵）")
    print(f"   總計: +170 分")

    # 處理反饋
    print(f"\n🤖 Agent 處理反饋...")
    result = await agent.process_user_feedback("demo_user_001")

    # 檢查狀態轉換
    updated_user = await memory.get_user_profile("demo_user_001")
    print(f"\n📈 用戶狀態更新:")
    print(f"   新狀態: {updated_user.current_engagement_state}")
    print(f"   完成卡片數: {updated_user.bingo_history.cards_completed}")
    print(f"   參與率: {updated_user.bingo_history.participation_rate:.0%}")
    print(f"   完成率: {updated_user.bingo_history.completion_rate:.0%}")

    if updated_user.current_engagement_state == EngagementState.STATE_4_ACTIVE:
        print(f"\n🎊 恭喜！用戶已升級到 State 4 (Active)！")
        print(f"   - 下次會生成更有挑戰性的卡片")
        print(f"   - 開始推動用戶嘗試新的交通方式")


async def demo_3_generate_new_card_for_active_user(memory):
    """Demo 3: 為活躍用戶生成新卡片"""
    print_header("DEMO 3: 為活躍用戶生成新卡片")

    agent = BingoAgentGraph(memory)

    print("📊 用戶現在是 State 4 (Active) 用戶")
    print("   Agent 會調整策略...")

    # 等待一下（模擬時間流逝）
    await asyncio.sleep(0.5)

    print("\n🎲 生成新卡片...")
    result = await agent.generate_card_for_user("demo_user_001")

    if result.card_generation_response and result.card_generation_response.success:
        card = result.card_generation_response.card
        print(f"\n✅ 新卡片生成成功！")
        print(f"   卡片 ID: {card.card_id}")
        print(f"   難度配置: {card.tile_profile.value}")
        print(f"   維度: {card.dimension.value}")

        print(f"\n📋 新卡片方塊:")
        nudge_count = 0
        for i, tile in enumerate(card.tiles, 1):
            mode_str = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[一般]"
            if tile.is_nudge:
                nudge_count += 1
                print(f"   {i:2d}. 🎯 {tile.description:40s} {mode_str:10s} ⭐⭐⭐ (新挑戰!)")
            else:
                print(f"   {i:2d}.    {tile.description:40s} {mode_str:10s} ⭐⭐")

        print(f"\n💡 分析:")
        print(f"   - 配置變更: Easy Wins → {card.tile_profile.value}")
        print(f"   - 包含 {nudge_count} 個推動方塊（嘗試新交通方式）")
        print(f"   - 難度適度提升，鼓勵探索")
        print(f"   - 基於上次成功完成的經驗")
    else:
        print(f"⏸️  暫時無法生成新卡片")
        print(f"   原因: {result.card_generation_response.reason if result.card_generation_response else '用戶可能還有活躍卡片'}")


async def demo_4_reminder_system(memory):
    """Demo 4: 提醒系統演示"""
    print_header("DEMO 4: 智能提醒系統")

    agent = BingoAgentGraph(memory)

    # 獲取當前卡片
    card = await memory.get_active_card("demo_user_001")
    if not card:
        print("ℹ️  用戶當前沒有活躍的卡片")
        return

    print(f"📊 當前卡片狀態:")
    print(f"   進度: {card.progress_percentage:.0f}%")
    print(f"   剩餘時間: {card.time_remaining_hours:.0f} 小時")
    print(f"   是否停滯: {'是' if card.is_stalled else '否'}")

    # 檢查提醒
    print(f"\n🤖 Agent 評估是否需要發送提醒...")
    result = await agent.check_reminder_for_user("demo_user_001")

    if result.reminder_decision:
        decision = result.reminder_decision
        print(f"\n💡 提醒決策:")
        print(f"   動作: {decision.action.value}")
        print(f"   原因: {decision.reason}")

        if decision.message_text:
            print(f"\n📱 提醒消息:")
            print(f"   ┌{'─'*50}┐")
            print(f"   │ {decision.message_text:48s} │")
            print(f"   └{'─'*50}┘")
            print(f"\n   模板: {decision.message_template.value if decision.message_template else 'N/A'}")


async def demo_5_llm_comparison(memory):
    """Demo 5: LLM vs 標準版本對比"""
    print_header("DEMO 5: LLM 增強版本對比 (可選)")

    # 檢查 API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  未配置 OPENAI_API_KEY，跳過 LLM 演示")
        return

    print(f"✅ 檢測到 OpenAI API Key")
    print(f"   嘗試使用 GPT-4o-mini 生成個性化內容...\n")

    # 創建新用戶用於對比
    test_user = UserProfile(
        user_id="llm_test_user",
        current_engagement_state=EngagementState.STATE_4_ACTIVE,
        behavioral_archetype=BehavioralArchetype.MULTIMODAL_ACTIVE,
        trip_history=TripHistory(
            primary_modes=[TransportMode.BIKING, TransportMode.WALKING],
            trip_frequency=25,
        ),
        bingo_history=BingoHistory(cards_completed=3)
    )
    await memory.save_user_profile(test_user)

    try:
        llm_agent = LLMBingoAgentGraph(memory)
        print("🤖 使用 LLM Agent 生成卡片...")

        result = await llm_agent.generate_card_for_user("llm_test_user")

        if result.card_generation_response and result.card_generation_response.success:
            card = result.card_generation_response.card
            print(f"\n✅ LLM 卡片生成成功！\n")

            print("📋 LLM 生成的方塊（個性化、有趣）:")
            for i, tile in enumerate(card.tiles[:5], 1):
                print(f"   {i}. {tile.description}")
            print(f"   ... 還有 {len(card.tiles) - 5} 個方塊")

            print(f"\n💡 LLM 優勢:")
            print(f"   - 描述更生動、有趣")
            print(f"   - 根據用戶類型個性化")
            print(f"   - 語言更自然、鼓勵性")

        else:
            print(f"\n⚠️  LLM 生成失敗，自動降級到規則生成")
            print(f"   原因: {result.card_generation_response.reason if result.card_generation_response else 'API 訪問問題'}")
            print(f"   系統依然正常運作！")

    except Exception as e:
        print(f"\n⚠️  LLM 功能暫時不可用: {str(e)[:50]}...")
        print(f"   這是正常的！系統會自動降級到規則生成")
        print(f"   用戶體驗不受影響")


async def demo_6_learning_insights(memory):
    """Demo 6: 學習洞察"""
    print_header("DEMO 6: 系統學習洞察")

    from src.utils import FeedbackLearner

    learner = FeedbackLearner(memory)

    print("🧠 分析用戶行為模式...\n")

    # 獲取洞察
    insights = await learner.get_user_insights("demo_user_001")

    if insights:
        print("📊 用戶洞察報告:")
        print(f"   狀態: {insights.get('engagement_state', 'N/A')}")
        print(f"   行為類型: {insights.get('behavioral_archetype', 'N/A')}")
        print(f"   總獎勵分數: {insights.get('total_reward', 0):.0f} 分")
        print(f"   完成卡片數: {insights.get('cards_completed', 0)}")
        print(f"   完成率: {insights.get('completion_rate', 0):.0%}")
        print(f"   參與率: {insights.get('participation_rate', 0):.0%}")

    # 檢測流失風險
    user = await memory.get_user_profile("demo_user_001")
    if user:
        churn_risk = await learner.detect_churn_risk(user)
        print(f"\n⚠️  流失風險評估:")
        print(f"   風險分數: {churn_risk:.2f}")
        if churn_risk < 0.3:
            print(f"   狀態: ✅ 低風險 - 用戶參與度良好")
        elif churn_risk < 0.7:
            print(f"   狀態: ⚠️  中等風險 - 需要關注")
        else:
            print(f"   狀態: 🚨 高風險 - 建議採取措施")

        print(f"\n💡 系統學習到:")
        print(f"   - 用戶偏好的卡片類型")
        print(f"   - 最佳的提醒時機")
        print(f"   - 合適的難度配置")
        print(f"   - 並在未來自動優化！")


async def main():
    """運行完整 Demo"""
    print("\n" + "🎮 " + "="*66 + " 🎮")
    print("  BINGO CARD ENGAGEMENT AGENT - 完整演示")
    print("  基於 LangGraph + 記憶 + 反饋學習")
    print("🎮 " + "="*66 + " 🎮" + "\n")

    try:
        # 清理舊數據庫
        import os
        if os.path.exists("./demo.db"):
            os.remove("./demo.db")
            print("🗑️  清理舊演示數據\n")

        # Demo 1: 創建用戶和生成卡片
        memory = await demo_1_create_user()

        input("\n按 Enter 繼續下一個演示...")

        # Demo 2: 完成卡片
        await demo_2_user_completes_card(memory)

        input("\n按 Enter 繼續下一個演示...")

        # Demo 3: 生成新卡片
        await demo_3_generate_new_card_for_active_user(memory)

        input("\n按 Enter 繼續下一個演示...")

        # Demo 4: 提醒系統
        await demo_4_reminder_system(memory)

        input("\n按 Enter 繼續下一個演示...")

        # Demo 5: LLM 對比（可選）
        await demo_5_llm_comparison(memory)

        input("\n按 Enter 繼續最後一個演示...")

        # Demo 6: 學習洞察
        await demo_6_learning_insights(memory)

        # 完成
        print_header("🎉 演示完成！")
        print("✅ 所有功能展示完畢\n")

        print("📚 接下來可以:")
        print("   1. 查看 demo.db 數據庫中的數據")
        print("   2. 運行 examples/basic_usage.py 了解更多")
        print("   3. 閱讀 README.md 和 ARCHITECTURE.md")
        print("   4. 集成到您的應用中！\n")

        print("💡 提示:")
        print("   - 標準版本: from src.graph import BingoAgentGraph")
        print("   - LLM 版本: from src.graph import LLMBingoAgentGraph")
        print("   - 兩者接口完全相同，可以無縫切換\n")

    except KeyboardInterrupt:
        print("\n\n⏸️  演示已中斷")
    except Exception as e:
        print(f"\n\n❌ 演示出錯: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
