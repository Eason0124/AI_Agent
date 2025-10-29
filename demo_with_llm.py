"""
完整演示 - 包含 LLM 個性化內容生成
展示標準版本 vs LLM 版本的差異
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.models import (
    UserProfile,
    EngagementState,
    BehavioralArchetype,
    TripHistory,
    BingoHistory,
    TransportMode,
)
from src.memory import SQLiteMemoryStore
from src.graph import BingoAgentGraph, LLMBingoAgentGraph


def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


async def main():
    print("\n" + "🎮 " + "="*66 + " 🎮")
    print("  BINGO CARD AGENT - 完整演示 (包含 LLM)")
    print("  展示標準版本 vs GPT-4o-mini 個性化版本")
    print("🎮 " + "="*66 + " 🎮" + "\n")

    # 清理舊數據
    if os.path.exists("./demo.db"):
        os.remove("./demo.db")

    memory = SQLiteMemoryStore(db_path="./demo.db")
    await memory.initialize()

    # =================================================================
    # DEMO 1: 標準版本 - 規則生成
    # =================================================================
    print_header("DEMO 1: 標準版本（規則生成）")

    print("創建用戶：駕駛常客...")
    user1 = UserProfile(
        user_id="standard_user",
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
        trip_history=TripHistory(
            primary_modes=[TransportMode.DRIVING],
            trip_frequency=20,
            common_travel_times=["AM_Commuter"],
        ),
        bingo_history=BingoHistory()
    )
    await memory.save_user_profile(user1)

    print("\n🎲 使用標準 Agent 生成卡片...\n")
    standard_agent = BingoAgentGraph(memory)
    result1 = await standard_agent.generate_card_for_user("standard_user")

    card1 = result1.card_generation_response.card
    print(f"✅ 標準卡片生成成功")
    print(f"   配置: {card1.tile_profile.value}")
    print(f"   維度: {card1.dimension.value}\n")

    print("📋 標準版本的方塊（規則生成）:")
    for i, tile in enumerate(card1.tiles, 1):
        mode = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[通用]"
        print(f"   {i}. {tile.description:45s} {mode}")

    await asyncio.sleep(2)

    # =================================================================
    # DEMO 2: LLM 版本 - GPT-4o-mini 個性化生成
    # =================================================================
    print_header("DEMO 2: LLM 版本（GPT-4o-mini 個性化生成）")

    print("創建用戶：多模式活躍用戶...")
    user2 = UserProfile(
        user_id="llm_user",
        current_engagement_state=EngagementState.STATE_4_ACTIVE,
        behavioral_archetype=BehavioralArchetype.MULTIMODAL_ACTIVE,
        trip_history=TripHistory(
            primary_modes=[TransportMode.BIKING, TransportMode.WALKING],
            trip_frequency=25,
            common_travel_times=["Weekend_Traveler"],
        ),
        bingo_history=BingoHistory(
            cards_completed=3,
            cards_participated=3,
            cards_offered=3
        )
    )
    await memory.save_user_profile(user2)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  未檢測到 OPENAI_API_KEY")
        print("   請在 .env 文件中設置 API key")
        return

    print(f"\n✅ 檢測到 OpenAI API Key: {api_key[:20]}...")
    print("🤖 使用 GPT-4o-mini 生成個性化內容...\n")

    try:
        llm_agent = LLMBingoAgentGraph(memory)
        llm_info = llm_agent.get_llm_info()
        print(f"💡 LLM 配置:")
        print(f"   模型: {llm_info['model']}")
        print(f"   溫度: {llm_info['temperature']}\n")

        result2 = await llm_agent.generate_card_for_user("llm_user")

        if result2.card_generation_response.success:
            card2 = result2.card_generation_response.card
            print(f"✅ LLM 卡片生成成功")
            print(f"   配置: {card2.tile_profile.value}")
            print(f"   維度: {card2.dimension.value}\n")

            print("📋 LLM 版本的方塊（GPT-4o-mini 生成 - 更生動、個性化）:")
            for i, tile in enumerate(card2.tiles, 1):
                mode = f"[{tile.transport_mode.value}]" if tile.transport_mode else "[通用]"
                nudge = "🎯" if tile.is_nudge else "  "
                print(f"   {nudge} {i}. {tile.description:45s} {mode}")

            print("\n💡 LLM 生成的特點:")
            print("   ✓ 描述更生動、有趣")
            print("   ✓ 根據用戶類型個性化")
            print("   ✓ 語言更自然、鼓勵性")
            print("   ✓ 考慮用戶的出行習慣")

        else:
            print(f"⚠️  LLM 生成失敗: {result2.card_generation_response.reason}")
            print("   系統自動降級到規則生成")

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

    await asyncio.sleep(2)

    # =================================================================
    # DEMO 3: 對比總結
    # =================================================================
    print_header("DEMO 3: 標準 vs LLM 對比總結")

    print("📊 標準版本:")
    print("   優點: 可靠、快速、零成本")
    print("   特點: 規則化、一致性高")
    print("   適用: 新用戶、成本敏感場景\n")

    print("🤖 LLM 版本:")
    print("   優點: 個性化、有趣、提升參與度")
    print("   特點: 生動、自然、上下文感知")
    print("   適用: 活躍用戶、注重體驗場景\n")

    print("💡 最佳實踐:")
    print("   - State 3 用戶 → 標準版本（降低門檻）")
    print("   - State 4+ 用戶 → LLM 版本（提升體驗）")
    print("   - 成本可控，體驗優化\n")

    # =================================================================
    # DEMO 4: 查看數據庫
    # =================================================================
    print_header("DEMO 4: 查看數據庫內容")

    print("💾 運行以下命令查看完整數據:")
    print("   python view_demo_db.py\n")

    print("📊 或查詢特定數據:")
    print("   # 查看所有卡片")
    print("   SELECT card_id, user_id, tile_profile, dimension FROM bingo_cards;\n")
    print("   # 查看方塊內容")
    print("   SELECT card_id, tiles FROM bingo_cards;\n")

    # 顯示快速統計
    async with memory.memory.connect(memory.db_path) as db:
        async with db.execute("SELECT COUNT(*) FROM user_profiles") as cursor:
            user_count = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM bingo_cards") as cursor:
            card_count = (await cursor.fetchone())[0]

    print(f"📈 當前統計:")
    print(f"   用戶數: {user_count}")
    print(f"   卡片數: {card_count}\n")

    print_header("🎉 演示完成！")

    print("✅ 您已經看到:")
    print("   1. 標準版本的規則生成")
    print("   2. LLM 版本的個性化生成")
    print("   3. 兩者的差異和優勢")
    print("   4. 數據庫中的完整記錄\n")

    print("📚 接下來:")
    print("   • 查看 demo.db 數據庫詳情")
    print("   • 運行 view_demo_db.py 查看完整數據")
    print("   • 根據需求選擇合適的版本")
    print("   • 開始集成到您的應用！\n")


if __name__ == "__main__":
    asyncio.run(main())
