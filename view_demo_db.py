"""
查看 demo.db 數據庫內容
"""
import asyncio
import aiosqlite
from datetime import datetime
import json


async def show_database():
    """顯示數據庫內容"""
    db_path = "./demo.db"

    print("=" * 70)
    print("  DEMO.DB 數據庫內容查看")
    print("=" * 70)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # =================================================================
        # 1. 用戶檔案表
        # =================================================================
        print("\n" + "─" * 70)
        print("📋 USER_PROFILES (用戶檔案表)")
        print("─" * 70)

        async with db.execute("SELECT * FROM user_profiles") as cursor:
            users = await cursor.fetchall()
            if users:
                for user in users:
                    print(f"\n用戶 ID: {user['user_id']}")
                    print(f"  參與狀態: {user['engagement_state']}")
                    print(f"  行為類型: {user['behavioral_archetype']}")

                    trip_history = json.loads(user['trip_history'])
                    print(f"  主要交通方式: {trip_history.get('primary_modes', [])}")
                    print(f"  出行頻率: {trip_history.get('trip_frequency', 0)} 次/月")

                    bingo_history = json.loads(user['bingo_history'])
                    print(f"  卡片統計:")
                    print(f"    - 提供: {bingo_history.get('cards_offered', 0)}")
                    print(f"    - 參與: {bingo_history.get('cards_participated', 0)}")
                    print(f"    - 完成: {bingo_history.get('cards_completed', 0)}")

                    print(f"  創建時間: {user['created_at']}")
            else:
                print("  (無數據)")

        # =================================================================
        # 2. Bingo 卡片表
        # =================================================================
        print("\n" + "─" * 70)
        print("🎲 BINGO_CARDS (Bingo 卡片表)")
        print("─" * 70)

        async with db.execute("SELECT * FROM bingo_cards ORDER BY created_at") as cursor:
            cards = await cursor.fetchall()
            if cards:
                for i, card in enumerate(cards, 1):
                    print(f"\n卡片 #{i}: {card['card_id']}")
                    print(f"  用戶: {card['user_id']}")
                    print(f"  配置: {card['tile_profile']}")
                    print(f"  維度: {card['dimension']}")
                    print(f"  持續時間: {card['duration_days']} 天")
                    print(f"  狀態: {'✅ 已完成' if card['completed'] else ('🎮 進行中' if card['started'] else '📦 待開始')}")

                    tiles = json.loads(card['tiles'])
                    completed_tiles = sum(1 for t in tiles if t.get('completed', False))
                    print(f"  進度: {completed_tiles}/{len(tiles)} 方塊")

                    print(f"  方塊內容:")
                    for j, tile in enumerate(tiles[:3], 1):  # 只顯示前3個
                        status = "✓" if tile.get('completed', False) else " "
                        mode = f"[{tile.get('transport_mode', 'general')}]"
                        print(f"    [{status}] {j}. {tile['description']} {mode}")
                    if len(tiles) > 3:
                        print(f"    ... 還有 {len(tiles) - 3} 個方塊")

                    print(f"  創建: {card['created_at']}")
                    print(f"  到期: {card['expires_at']}")
            else:
                print("  (無數據)")

        # =================================================================
        # 3. 反饋事件表
        # =================================================================
        print("\n" + "─" * 70)
        print("💬 FEEDBACK_EVENTS (反饋事件表)")
        print("─" * 70)

        async with db.execute(
            "SELECT * FROM feedback_events ORDER BY timestamp DESC LIMIT 10"
        ) as cursor:
            events = await cursor.fetchall()
            if events:
                print(f"\n最近 {len(events)} 個事件:")
                for event in events:
                    emoji_map = {
                        "card_started": "🎮",
                        "card_completed": "🎉",
                        "user_state_transition": "🎊",
                        "tile_completed": "✓",
                    }
                    emoji = emoji_map.get(event['event_type'], "📝")

                    print(f"\n  {emoji} {event['event_type']}")
                    print(f"     用戶: {event['user_id']}")
                    if event['card_id']:
                        print(f"     卡片: {event['card_id']}")
                    print(f"     獎勵: +{event['reward_score']:.0f} 分")
                    print(f"     時間: {event['timestamp']}")

                    if event['metadata']:
                        metadata = json.loads(event['metadata'])
                        if metadata:
                            print(f"     詳情: {metadata}")
            else:
                print("  (無數據)")

        # =================================================================
        # 4. Agent 行為表
        # =================================================================
        print("\n" + "─" * 70)
        print("🤖 AGENT_ACTIONS (Agent 決策記錄)")
        print("─" * 70)

        async with db.execute(
            "SELECT * FROM agent_actions ORDER BY timestamp DESC LIMIT 10"
        ) as cursor:
            actions = await cursor.fetchall()
            if actions:
                print(f"\n最近 {len(actions)} 個決策:")
                for action in actions:
                    status = "✅" if action['success'] else "❌"
                    print(f"\n  {status} {action['action_type']}")
                    print(f"     用戶: {action['user_id']}")
                    print(f"     時間: {action['timestamp']}")

                    if action['details']:
                        details = json.loads(action['details'])
                        if details:
                            for key, value in list(details.items())[:3]:
                                print(f"     - {key}: {value}")
            else:
                print("  (無數據)")

        # =================================================================
        # 5. 統計摘要
        # =================================================================
        print("\n" + "─" * 70)
        print("📊 數據庫統計摘要")
        print("─" * 70)

        # 用戶數
        async with db.execute("SELECT COUNT(*) FROM user_profiles") as cursor:
            user_count = (await cursor.fetchone())[0]

        # 卡片數
        async with db.execute("SELECT COUNT(*) FROM bingo_cards") as cursor:
            card_count = (await cursor.fetchone())[0]

        # 完成的卡片數
        async with db.execute(
            "SELECT COUNT(*) FROM bingo_cards WHERE completed = 1"
        ) as cursor:
            completed_cards = (await cursor.fetchone())[0]

        # 反饋事件數
        async with db.execute("SELECT COUNT(*) FROM feedback_events") as cursor:
            event_count = (await cursor.fetchone())[0]

        # 總獎勵
        async with db.execute(
            "SELECT SUM(reward_score) FROM feedback_events"
        ) as cursor:
            total_reward = (await cursor.fetchone())[0] or 0

        # Agent 決策數
        async with db.execute("SELECT COUNT(*) FROM agent_actions") as cursor:
            action_count = (await cursor.fetchone())[0]

        print(f"\n  👥 總用戶數: {user_count}")
        print(f"  🎲 總卡片數: {card_count}")
        print(f"  ✅ 完成卡片: {completed_cards}")
        print(f"  💬 反饋事件: {event_count}")
        print(f"  🏆 總獎勵分數: {total_reward:.0f}")
        print(f"  🤖 Agent 決策: {action_count}")

        if card_count > 0:
            completion_rate = (completed_cards / card_count) * 100
            print(f"\n  📈 完成率: {completion_rate:.1f}%")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(show_database())
