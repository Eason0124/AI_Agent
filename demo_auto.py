"""
Bingo Card Agent - 自動演示版本
完整展示系統功能（無需手動按 Enter）
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


async def run_all_demos():
    """運行所有演示"""
    print("\n" + "🎮 " + "="*66 + " 🎮")
    print("  BINGO CARD ENGAGEMENT AGENT - 完整自動演示")
    print("  基於 LangGraph + 記憶 + 反饋學習")
    print("🎮 " + "="*66 + " 🎮" + "\n")

    # 清理舊數據
    if os.path.exists("./demo.db"):
        os.remove("./demo.db")
        print("🗑️  清理舊演示數據\n")

    # 初始化
    memory = SQLiteMemoryStore(db_path="./demo.db")
    await memory.initialize()

    # =============================================================================
    # DEMO 1: 創建用戶並生成卡片
    # =============================================================================
    print_header("DEMO 1: 創建新用戶並生成第一張卡片")

    user = UserProfile(
        user_id="demo_user",
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
        trip_history=TripHistory(
            primary_modes=[TransportMode.DRIVING],
            trip_frequency=15,
            common_travel_times=["AM_Commuter"],
            mode_distribution={TransportMode.DRIVING: 15}
        ),
        bingo_history=BingoHistory()
    )
    await memory.save_user_profile(user)

    print(f"✅ 用戶創建: {user.user_id}")
    print(f"   狀態: {user.current_engagement_state}")
    print(f"   類型: {user.behavioral_archetype}")

    agent = BingoAgentGraph(memory)
    result = await agent.generate_card_for_user("demo_user")

    card = result.card_generation_response.card
    print(f"\n✅ 卡片生成成功")
    print(f"   配置: {card.tile_profile.value}")
    print(f"   維度: {card.dimension.value}")
    print(f"\n📋 卡片內容 ({len(card.tiles)} 個方塊):")
    for i, tile in enumerate(card.tiles, 1):
        mode = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[通用]"
        print(f"   {i}. {tile.description:35s} {mode}")

    await asyncio.sleep(1)

    # =============================================================================
    # DEMO 2: 用戶完成卡片
    # =============================================================================
    print_header("DEMO 2: 用戶完成卡片並獲得獎勵")

    print("🎮 用戶開始遊戲...")
    feedback1 = FeedbackEvent(
        user_id="demo_user",
        card_id=card.card_id,
        event_type="card_started"
    )
    await memory.save_feedback(feedback1)

    card.started = True
    card.started_at = datetime.now()

    print("\n📝 用戶逐步完成方塊...")
    for i, tile in enumerate(card.tiles):
        tile.completed = True
        tile.completed_at = datetime.now()
        print(f"   ✓ 完成方塊 {i+1}: {tile.description}")

    card.completed = True
    card.completed_at = datetime.now()
    await memory.save_bingo_card(card)

    print("\n🎉 卡片完成！")

    feedback2 = FeedbackEvent(
        user_id="demo_user",
        card_id=card.card_id,
        event_type="card_completed",
        reward_score=100.0
    )
    await memory.save_feedback(feedback2)

    print(f"\n🏆 獎勵: +100 分")

    # 處理反饋
    await agent.process_user_feedback("demo_user")

    updated_user = await memory.get_user_profile("demo_user")
    print(f"\n📈 用戶狀態更新:")
    print(f"   新狀態: {updated_user.current_engagement_state}")
    print(f"   完成卡片: {updated_user.bingo_history.cards_completed}")

    if updated_user.current_engagement_state == EngagementState.STATE_4_ACTIVE:
        print(f"\n🎊 恭喜！用戶升級到 State 4 (Active)！")

    await asyncio.sleep(1)

    # =============================================================================
    # DEMO 3: 為活躍用戶生成新卡片
    # =============================================================================
    print_header("DEMO 3: 為活躍用戶生成新卡片")

    print("💡 用戶現在是 State 4，系統會調整策略...")

    result2 = await agent.generate_card_for_user("demo_user")

    if result2.card_generation_response.success:
        card2 = result2.card_generation_response.card
        print(f"\n✅ 新卡片生成")
        print(f"   配置: {card2.tile_profile.value}")

        nudge_count = sum(1 for t in card2.tiles if t.is_nudge)
        print(f"\n📋 新卡片特點:")
        print(f"   - 包含 {nudge_count} 個推動方塊（嘗試新交通方式）")
        print(f"   - 難度提升，鼓勵探索")

        print(f"\n   方塊示例:")
        for i, tile in enumerate(card2.tiles[:5], 1):
            nudge = "🎯" if tile.is_nudge else "  "
            print(f"   {nudge} {tile.description}")
        print(f"   ... 還有 {len(card2.tiles) - 5} 個方塊")

    await asyncio.sleep(1)

    # =============================================================================
    # DEMO 4: 提醒系統
    # =============================================================================
    print_header("DEMO 4: 智能提醒系統")

    active_card = await memory.get_active_card("demo_user")
    if active_card:
        print(f"📊 當前卡片狀態:")
        print(f"   進度: {active_card.progress_percentage:.0f}%")
        print(f"   剩餘: {active_card.time_remaining_hours:.0f} 小時")

        result3 = await agent.check_reminder_for_user("demo_user")
        decision = result3.reminder_decision

        print(f"\n💡 提醒決策:")
        print(f"   動作: {decision.action.value}")
        print(f"   原因: {decision.reason}")

        if decision.message_text:
            print(f"\n📱 提醒消息:")
            print(f"   '{decision.message_text}'")

    await asyncio.sleep(1)

    # =============================================================================
    # DEMO 5: 學習洞察
    # =============================================================================
    print_header("DEMO 5: 系統學習洞察")

    from src.utils import FeedbackLearner
    learner = FeedbackLearner(memory)

    insights = await learner.get_user_insights("demo_user")
    print("📊 用戶洞察:")
    print(f"   總獎勵: {insights.get('total_reward', 0):.0f} 分")
    print(f"   完成率: {insights.get('completion_rate', 0):.0%}")
    print(f"   參與率: {insights.get('participation_rate', 0):.0%}")

    user = await memory.get_user_profile("demo_user")
    churn_risk = await learner.detect_churn_risk(user)
    print(f"\n⚠️  流失風險: {churn_risk:.2f}")
    if churn_risk < 0.3:
        print(f"   狀態: ✅ 低風險")
    else:
        print(f"   狀態: ⚠️  需要關注")

    print(f"\n💡 系統會持續學習:")
    print(f"   - 用戶偏好的卡片類型")
    print(f"   - 最佳提醒時機")
    print(f"   - 合適的難度")

    # =============================================================================
    # DEMO 6: LLM 功能（如果可用）
    # =============================================================================
    print_header("DEMO 6: LLM 增強功能（可選）")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ 檢測到 OpenAI API Key")
        print("   嘗試使用 GPT-4o-mini...\n")

        try:
            llm_user = UserProfile(
                user_id="llm_user",
                current_engagement_state=EngagementState.STATE_4_ACTIVE,
                behavioral_archetype=BehavioralArchetype.MULTIMODAL_ACTIVE,
                trip_history=TripHistory(
                    primary_modes=[TransportMode.BIKING, TransportMode.WALKING]
                ),
                bingo_history=BingoHistory()
            )
            await memory.save_user_profile(llm_user)

            llm_agent = LLMBingoAgentGraph(memory)
            llm_result = await llm_agent.generate_card_for_user("llm_user")

            if llm_result.card_generation_response.success:
                llm_card = llm_result.card_generation_response.card
                print("✅ LLM 生成成功！\n")
                print("📋 LLM 生成的方塊（更個性化）:")
                for i, tile in enumerate(llm_card.tiles[:5], 1):
                    print(f"   {i}. {tile.description}")
                print("\n💡 LLM 的描述更生動、有趣、個性化")
            else:
                print("⚠️  LLM 暫時不可用，使用規則生成")
                print("   系統依然正常運作！")

        except Exception as e:
            print(f"⚠️  LLM 功能暫時不可用")
            print(f"   原因: {str(e)[:50]}...")
            print(f"   這是正常的！系統會自動降級")
    else:
        print("ℹ️  未配置 OpenAI API Key")
        print("   LLM 功能可選，不影響核心功能")

    # =============================================================================
    # 完成
    # =============================================================================
    print_header("🎉 演示完成！")

    print("✅ 展示了所有核心功能:\n")
    print("   1. ✅ 創建用戶和生成卡片")
    print("   2. ✅ 用戶完成卡片和獎勵系統")
    print("   3. ✅ 狀態轉換（State 3 → State 4）")
    print("   4. ✅ 智能提醒系統")
    print("   5. ✅ 學習洞察和流失預警")
    print("   6. ✅ LLM 增強功能（可選）\n")

    print("📚 接下來可以:")
    print("   • 查看 demo.db 數據庫")
    print("   • 運行 examples/basic_usage.py")
    print("   • 閱讀 README.md 文檔")
    print("   • 集成到您的應用！\n")

    print("💡 使用方式:")
    print("   標準版: from src.graph import BingoAgentGraph")
    print("   LLM版:  from src.graph import LLMBingoAgentGraph\n")


if __name__ == "__main__":
    asyncio.run(run_all_demos())
