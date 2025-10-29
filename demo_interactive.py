"""
互動式演示 - 展示 AI Agent 與用戶的完整對話過程
模擬真實的用戶互動場景
"""
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
from src.graph import LLMBingoAgentGraph
from src.utils import FeedbackLearner


def print_divider(char="=", length=80):
    print("\n" + char * length)


def print_section(title, emoji="📌"):
    print_divider()
    print(f"{emoji} {title}")
    print_divider()


def print_message(speaker, message, indent=2):
    """打印對話消息"""
    prefix = " " * indent
    if speaker == "用戶":
        print(f"\n{prefix}👤 {speaker}: {message}")
    elif speaker == "Agent":
        print(f"\n{prefix}🤖 {speaker}: {message}")
    elif speaker == "系統":
        print(f"\n{prefix}⚙️  {speaker}: {message}")
    else:
        print(f"\n{prefix}{speaker}: {message}")


def print_thinking(thought, indent=4):
    """打印Agent的思考過程"""
    prefix = " " * indent
    print(f"{prefix}💭 [Agent 思考]: {thought}")


def print_action(action, indent=4):
    """打印Agent的行動"""
    prefix = " " * indent
    print(f"{prefix}⚡ [Agent 行動]: {action}")


async def simulate_user_journey():
    """模擬完整的用戶旅程"""

    print("\n" + "🎭 " + "=" * 76 + " 🎭")
    print("  AI AGENT 與用戶互動過程演示")
    print("  模擬真實用戶從新手到活躍用戶的完整旅程")
    print("🎭 " + "=" * 76 + " 🎭")

    # 清理並初始化
    if os.path.exists("./demo_interactive.db"):
        os.remove("./demo_interactive.db")

    memory = SQLiteMemoryStore(db_path="./demo_interactive.db")
    await memory.initialize()

    agent = LLMBingoAgentGraph(memory)
    learner = FeedbackLearner(memory)

    # =========================================================================
    # 場景 1: 新用戶首次接觸
    # =========================================================================
    print_section("場景 1: 新用戶 Alice 首次打開 App", "🎬")

    print_message("系統", "檢測到新用戶登入...")

    # 創建新用戶
    alice = UserProfile(
        user_id="alice_123",
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
        trip_history=TripHistory(
            primary_modes=[TransportMode.DRIVING],
            trip_frequency=15,
            common_travel_times=["AM_Commuter"],
        ),
        bingo_history=BingoHistory()
    )
    await memory.save_user_profile(alice)

    print_message("用戶", "嗨！我是新用戶，想了解一下這個Bingo遊戲是怎麼玩的？")

    print_thinking("用戶狀態: State_3_Pre_Active（新手）")
    print_thinking("行為類型: Driver_Heavy（主要開車通勤）")
    print_thinking("策略: 生成簡單的入門卡片，降低參與門檻")

    print_action("為用戶生成第一張 Bingo 卡片...")

    result = await agent.generate_card_for_user("alice_123")
    card = result.card_generation_response.card

    print_message("Agent", f"歡迎 Alice！我為你準備了一張簡單的 Bingo 卡片 🎉")
    print_message("Agent", f"這是一張 {card.dimension.value} 的卡片，只需完成 {len(card.tiles)} 個簡單任務就能獲得獎勵！")

    print("\n    📋 卡片任務:")
    for i, tile in enumerate(card.tiles, 1):
        mode = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[通用]"
        nudge_mark = "🎯 " if tile.is_nudge else ""
        print(f"       {i}. {nudge_mark}{tile.description:40s} {mode}")

    print_message("Agent", f"完成這張卡片可獲得 100 積分！現在就開始吧 💪")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 2: 用戶開始互動
    # =========================================================================
    print_section("場景 2: Alice 開始完成任務", "🎮")

    print_message("用戶", "好的！我剛剛完成了一趟開車出行，這個算嗎？")

    print_thinking("檢測到用戶完成了一個 driving 相關的方塊")
    print_thinking("這是用戶的第一次互動，給予正面反饋很重要")

    # 標記第一個方塊完成
    card.tiles[0].completed = True
    card.tiles[0].completed_at = datetime.now()
    card.started = True
    card.started_at = datetime.now()
    await memory.save_bingo_card(card)

    # 記錄反饋事件
    start_event = FeedbackEvent(
        user_id="alice_123",
        card_id=card.card_id,
        event_type="card_started",
        reward_score=10.0,
        metadata={"first_interaction": True}
    )
    await memory.save_feedback(start_event)

    print_action("更新卡片進度...")
    print_action("記錄反饋事件: card_started (+10分)")

    print_message("Agent", "太棒了！✨ 你完成了第一個任務！")
    print_message("Agent", f"當前進度: 1/{len(card.tiles)} (獲得 +10 積分)")
    print_message("Agent", "繼續加油，完成整張卡片可額外獲得 100 積分獎勵！🎁")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 3: 用戶持續參與
    # =========================================================================
    print_section("場景 3: Alice 持續完成更多任務", "🔥")

    print_message("用戶", "我今天又完成了幾趟出行，更新一下進度吧！")

    print_thinking("用戶展現出持續參與的意願")
    print_thinking("逐步完成任務，建立使用習慣")

    # 完成更多方塊
    completed_count = 0
    for i in range(1, 5):  # 再完成4個方塊
        card.tiles[i].completed = True
        card.tiles[i].completed_at = datetime.now()
        completed_count += 1

    await memory.save_bingo_card(card)

    print_action(f"更新進度: 完成了 {completed_count} 個新任務")

    progress = sum(1 for t in card.tiles if t.completed)
    progress_pct = (progress / len(card.tiles)) * 100

    print_message("Agent", f"哇！你已經完成了 {progress}/{len(card.tiles)} 個任務！")
    print_message("Agent", f"進度: {progress_pct:.0f}% ({'▓' * int(progress_pct/10)}{'░' * (10-int(progress_pct/10))})")
    print_message("Agent", f"還差 {len(card.tiles) - progress} 個就能獲得大獎了！💎")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 4: 用戶完成卡片
    # =========================================================================
    print_section("場景 4: Alice 完成整張卡片！", "🎊")

    print_message("用戶", "太好了！我把最後幾個任務也完成了！")

    print_thinking("用戶即將完成整張卡片")
    print_thinking("這是關鍵時刻，需要給予豐厚獎勵並推動狀態升級")

    # 完成所有剩餘方塊
    for i in range(5, len(card.tiles)):
        card.tiles[i].completed = True
        card.tiles[i].completed_at = datetime.now()

    card.completed = True
    card.completed_at = datetime.now()
    await memory.save_bingo_card(card)

    # 記錄完成事件
    complete_event = FeedbackEvent(
        user_id="alice_123",
        card_id=card.card_id,
        event_type="card_completed",
        reward_score=100.0,
        metadata={"completion_time_hours": 2}
    )
    await memory.save_feedback(complete_event)

    print_action("標記卡片為已完成")
    print_action("觸發完成獎勵: +100 積分")

    print_message("Agent", "🎉🎉🎉 恭喜你完成了第一張 Bingo 卡片！")
    print_message("Agent", "獲得獎勵: +100 積分 💰")
    print_message("Agent", "你做得非常棒！")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 5: 用戶狀態升級
    # =========================================================================
    print_section("場景 5: 用戶狀態升級", "⬆️")

    print_thinking("檢測到用戶完成了第一張卡片")
    print_thinking("觸發狀態轉換: State_3_Pre_Active → State_4_Active")
    print_thinking("給予狀態升級獎勵，激勵持續參與")

    # 更新用戶狀態
    alice.current_engagement_state = EngagementState.STATE_4_ACTIVE
    alice.bingo_history.cards_completed = 1
    alice.bingo_history.cards_participated = 1
    await memory.save_user_profile(alice)

    # 記錄狀態轉換事件
    transition_event = FeedbackEvent(
        user_id="alice_123",
        event_type="user_state_transition",
        reward_score=1000.0,
        metadata={
            "from_state": "State_3_Pre_Active",
            "to_state": "State_4_Active"
        }
    )
    await memory.save_feedback(transition_event)

    print_action("更新用戶狀態: State_3 → State_4")
    print_action("觸發升級獎勵: +1000 積分")

    print_message("Agent", "✨ 重大突破！你已經從新手升級為活躍用戶！")
    print_message("Agent", "狀態升級獎勵: +1000 積分 🏆")
    print_message("Agent", "現在你可以挑戰更有趣的卡片了！")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 6: 為活躍用戶生成新卡片
    # =========================================================================
    print_section("場景 6: 為活躍用戶生成個性化卡片", "🎨")

    print_message("用戶", "太棒了！給我來張更有挑戰性的卡片吧！")

    print_thinking("用戶現在是 State_4_Active")
    print_thinking("可以提供更複雜、更個性化的卡片")
    print_thinking("嘗試使用 LLM 生成更有趣的任務描述")

    print_action("分析用戶偏好和歷史數據...")
    print_action("生成個性化卡片...")

    result2 = await agent.generate_card_for_user("alice_123")

    if result2.card_generation_response.success and result2.card_generation_response.card:
        card2 = result2.card_generation_response.card

        print_message("Agent", "根據你的出行習慣，我為你準備了一張特別的卡片！")
        print_message("Agent", f"這次是 {card2.dimension.value} 維度，更有挑戰性哦 🚀")

        print("\n    📋 新卡片任務:")
        for i, tile in enumerate(card2.tiles, 1):
            mode = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[通用]"
            nudge_mark = "🎯 " if tile.is_nudge else ""
            print(f"       {i}. {nudge_mark}{tile.description:40s} {mode}")
    else:
        print_message("Agent", "正在為你準備新的挑戰！")
        print_message("Agent", "系統正在學習你的偏好，下次會為你生成更個性化的卡片！✨")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 7: 智能提醒系統
    # =========================================================================
    print_section("場景 7: 第二天 - 智能提醒", "⏰")

    print_message("系統", "[第二天早上 9:00]")

    print_thinking("檢測到用戶有未完成的卡片")
    print_thinking("用戶是 AM_Commuter，早上活躍度高")
    print_thinking("發送個性化提醒")

    print_action("評估提醒時機...")
    print_action("生成個性化提醒消息...")

    # 模擬提醒評估
    from src.models.reminder import ReminderAction
    reminder_result = await agent.check_reminder_for_user("alice_123")

    if reminder_result.reminder_decision and reminder_result.reminder_decision.action == ReminderAction.SEND_REMINDER:
        print_message("Agent", "早安 Alice！☀️")
        if reminder_result.reminder_decision.message_text:
            print_message("Agent", reminder_result.reminder_decision.message_text)
        print_message("Agent", "今天通勤時別忘了完成幾個任務哦 🚗")
    else:
        print_message("系統", "系統決定暫不發送提醒（用戶剛完成卡片，避免打擾）")

    await asyncio.sleep(2)

    # =========================================================================
    # 場景 8: 系統學習與優化
    # =========================================================================
    print_section("場景 8: 系統持續學習", "🧠")

    print_thinking("分析用戶行為模式...")
    print_thinking("優化未來的卡片生成和提醒策略...")

    print_action("運行學習算法...")

    # 獲取學習洞察
    insights = await learner.get_user_insights("alice_123")
    current_profile = await memory.get_user_profile("alice_123")
    churn_risk = await learner.detect_churn_risk(current_profile)

    print("\n    📊 系統學習到的用戶洞察:")
    print(f"       • 參與狀態: {insights.get('engagement_state', 'Unknown')}")
    print(f"       • 總獎勵: {insights.get('total_reward', 0)} 積分")
    print(f"       • 完成率: {insights.get('completion_rate', 0)*100:.0f}%")
    print(f"       • 流失風險: {churn_risk:.2f} ({'✅ 低風險' if churn_risk < 0.3 else '⚠️ 需關注'})")

    print("\n    💡 優化建議:")
    if churn_risk < 0.3:
        print("       • 用戶參與度高，可以提供更有挑戰性的卡片")
        print("       • 繼續保持當前的提醒頻率")
        print("       • 考慮引入多模式出行的 nudge tiles")
    else:
        print("       • 需要更多鼓勵和簡單任務")
        print("       • 增加提醒頻率")
        print("       • 提供更多即時獎勵")

    await asyncio.sleep(2)

    # =========================================================================
    # 總結
    # =========================================================================
    print_section("互動總結", "📈")

    # 統計數據
    total_rewards = insights.get('total_reward', 0)
    user_profile = current_profile  # 重用之前獲取的profile

    print("\n    🎯 Alice 的成長旅程:")
    print(f"       起點: State_3_Pre_Active (新手)")
    state_value = user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value
    print(f"       現在: {state_value} (活躍用戶)")
    print(f"       完成卡片: {user_profile.bingo_history.cards_completed} 張")
    print(f"       總獎勵: {total_rewards} 積分")
    print(f"       參與時長: 2 天")

    print("\n    🤖 Agent 的智能表現:")
    print("       ✅ 根據用戶狀態生成適配的卡片")
    print("       ✅ 實時追蹤進度並給予反饋")
    print("       ✅ 智能判斷狀態升級時機")
    print("       ✅ 個性化提醒優化參與度")
    print("       ✅ 持續學習優化策略")

    print("\n    🔄 反饋循環:")
    print("       用戶行為 → Agent 分析 → 策略調整 → 個性化體驗 → 提升參與度")

    print_divider("=", 80)
    print("✨ 演示完成！這就是 AI Agent 與用戶互動的完整過程")
    print_divider("=", 80)

    return {
        "user_profile": user_profile,
        "total_rewards": total_rewards,
        "insights": insights,
        "churn_risk": churn_risk
    }


if __name__ == "__main__":
    asyncio.run(simulate_user_journey())
