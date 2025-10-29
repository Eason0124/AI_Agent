"""
FastAPI Web Application for Bingo Card AI Agent
提供互動式網頁介面與 AI Agent 對話
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime

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
from src.graph import BingoAgentGraph

app = FastAPI(title="Bingo Card AI Agent", version="1.0.0")

# 全局變量
memory_store = None
agent = None
current_user_id = "web_user"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    user_id: str
    message: str
    action_type: Optional[str] = "chat"


class AgentResponse(BaseModel):
    """Agent 回應模型"""
    message: str
    thinking: Optional[str] = None
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    user_state: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """啟動時初始化"""
    global memory_store, agent
    memory_store = SQLiteMemoryStore(db_path="./web_demo.db")
    await memory_store.initialize()
    agent = BingoAgentGraph(memory_store)
    print("✅ AI Agent Web App 已啟動！")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主頁 HTML"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat", response_model=AgentResponse)
async def chat_with_agent(message: ChatMessage):
    """與 Agent 對話"""
    try:
        user_id = message.user_id
        user_message = message.message.lower()

        # 檢查用戶是否存在
        user_profile = await memory_store.get_user_profile(user_id)

        # 根據用戶消息判斷意圖
        if not user_profile:
            # 創建新用戶
            if "開始" in user_message or "註冊" in user_message or "hello" in user_message:
                return await create_new_user(user_id)
            else:
                return AgentResponse(
                    message="您好！我是 Bingo Card AI Agent。請先說「開始」來註冊。",
                    thinking="檢測到新用戶，需要先註冊",
                )

        # 已有用戶的各種操作
        if "卡片" in user_message or "bingo" in user_message:
            return await generate_card_for_user(user_id)
        elif "完成" in user_message or "finish" in user_message:
            return await complete_task_for_user(user_id, user_message)
        elif "狀態" in user_message or "status" in user_message:
            return await get_user_status(user_id)
        elif "獎勵" in user_message or "reward" in user_message:
            return await get_rewards(user_id)
        else:
            return AgentResponse(
                message="您可以說：\n• 「生成卡片」- 獲得新的 Bingo 卡片\n• 「完成任務」- 標記任務完成\n• 「查看狀態」- 查看您的進度\n• 「查看獎勵」- 查看積分獎勵",
                thinking="分析用戶意圖...",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_new_user(user_id: str) -> AgentResponse:
    """創建新用戶"""
    user = UserProfile(
        user_id=user_id,
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
        trip_history=TripHistory(
            primary_modes=[TransportMode.DRIVING],
            trip_frequency=15,
            common_travel_times=["AM_Commuter"],
        ),
        bingo_history=BingoHistory()
    )
    await memory_store.save_user_profile(user)

    return AgentResponse(
        message=f"歡迎 {user_id}！🎉\n\n您已成功註冊為新用戶。\n當前狀態：State 3 (新手)\n\n說「生成卡片」來獲得您的第一張 Bingo 卡片吧！",
        thinking="檢測到新用戶 → 創建 State_3 檔案 → 使用 Driver_Heavy 類型",
        action="已創建用戶檔案",
        user_state="State_3_Pre_Active",
        data={"archetype": "Driver_Heavy", "trip_frequency": 15}
    )


async def generate_card_for_user(user_id: str) -> AgentResponse:
    """為用戶生成卡片"""
    user_profile = await memory_store.get_user_profile(user_id)

    # 檢查是否有活躍卡片
    active_card = await memory_store.get_active_card(user_id)
    if active_card and not active_card.completed:
        tiles_completed = sum(1 for t in active_card.tiles if t.completed)
        progress_pct = (tiles_completed / len(active_card.tiles)) * 100

        return AgentResponse(
            message=f"您還有一張進行中的卡片！\n\n進度: {tiles_completed}/{len(active_card.tiles)} ({progress_pct:.0f}%)\n\n請先完成當前卡片，或說「查看狀態」查看詳情。",
            thinking="檢測到用戶有未完成的卡片",
            progress={
                "completed": tiles_completed,
                "total": len(active_card.tiles),
                "percentage": progress_pct
            }
        )

    # 生成新卡片
    result = await agent.generate_card_for_user(user_id)

    if result.card_generation_response.success:
        card = result.card_generation_response.card

        # 格式化卡片內容
        tiles_text = "\n".join([
            f"  {i+1}. {tile.description}"
            for i, tile in enumerate(card.tiles)
        ])

        return AgentResponse(
            message=f"✨ 為您生成了新的 Bingo 卡片！\n\n配置: {card.tile_profile.value}\n維度: {card.dimension.value}\n\n📋 任務列表:\n{tiles_text}\n\n完成所有任務可獲得 100 積分！",
            thinking=f"用戶狀態: {user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value} → 生成適配卡片",
            action="已生成新卡片",
            data={
                "card_id": card.card_id,
                "tiles_count": len(card.tiles),
                "profile": card.tile_profile.value if hasattr(card.tile_profile, 'value') else str(card.tile_profile)
            }
        )
    else:
        return AgentResponse(
            message=f"抱歉，生成卡片失敗：{result.card_generation_response.reason}",
            thinking="卡片生成失敗",
        )


async def complete_task_for_user(user_id: str, message: str) -> AgentResponse:
    """為用戶完成任務"""
    active_card = await memory_store.get_active_card(user_id)

    if not active_card:
        return AgentResponse(
            message="您還沒有活躍的卡片。請先說「生成卡片」。",
            thinking="沒有找到活躍卡片",
        )

    # 找到第一個未完成的方塊
    uncompleted_tiles = [t for t in active_card.tiles if not t.completed]

    if not uncompleted_tiles:
        return AgentResponse(
            message="恭喜！您已經完成了所有任務！🎉",
            thinking="所有任務已完成",
        )

    # 完成一個方塊
    tile_to_complete = uncompleted_tiles[0]
    tile_to_complete.completed = True
    tile_to_complete.completed_at = datetime.now()

    # 如果是第一個方塊，標記卡片為已開始
    if not active_card.started:
        active_card.started = True
        active_card.started_at = datetime.now()

        # 記錄開始事件
        start_event = FeedbackEvent(
            user_id=user_id,
            card_id=active_card.card_id,
            event_type="card_started",
            reward_score=10.0,
        )
        await memory_store.save_feedback(start_event)

    await memory_store.save_bingo_card(active_card)

    # 計算進度
    completed_count = sum(1 for t in active_card.tiles if t.completed)
    total_count = len(active_card.tiles)
    progress_pct = (completed_count / total_count) * 100

    # 檢查是否全部完成
    if completed_count == total_count:
        active_card.completed = True
        active_card.completed_at = datetime.now()
        await memory_store.save_bingo_card(active_card)

        # 記錄完成事件
        complete_event = FeedbackEvent(
            user_id=user_id,
            card_id=active_card.card_id,
            event_type="card_completed",
            reward_score=100.0,
        )
        await memory_store.save_feedback(complete_event)

        # 更新用戶狀態
        user_profile = await memory_store.get_user_profile(user_id)
        user_profile.bingo_history.cards_completed += 1

        # 檢查是否需要升級
        if user_profile.current_engagement_state == EngagementState.STATE_3_PRE_ACTIVE:
            user_profile.current_engagement_state = EngagementState.STATE_4_ACTIVE

            transition_event = FeedbackEvent(
                user_id=user_id,
                event_type="user_state_transition",
                reward_score=1000.0,
                metadata={
                    "from_state": "State_3_Pre_Active",
                    "to_state": "State_4_Active"
                }
            )
            await memory_store.save_feedback(transition_event)

            await memory_store.save_user_profile(user_profile)

            return AgentResponse(
                message=f"🎊 恭喜！您完成了整張卡片！\n\n✨ 重大突破！您已升級為活躍用戶！\n\n🏆 獲得獎勵:\n  • 卡片完成: +100 積分\n  • 狀態升級: +1000 積分\n  • 總計: +1110 積分\n\n現在您可以生成更有挑戰性的卡片了！",
                thinking="完成所有任務 → 觸發狀態升級 → State_3 → State_4",
                action="卡片完成 + 狀態升級",
                user_state="State_4_Active",
                data={
                    "total_rewards": 1110,
                    "state_upgrade": True
                }
            )
        else:
            await memory_store.save_user_profile(user_profile)

            return AgentResponse(
                message=f"🎉 恭喜！您完成了整張卡片！\n\n獲得獎勵: +100 積分\n\n說「生成卡片」來挑戰新的卡片吧！",
                thinking="完成所有任務 → 給予獎勵",
                action="卡片完成",
                data={"reward": 100}
            )

    # 未全部完成
    progress_bar = "▓" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))

    return AgentResponse(
        message=f"✅ 完成了一個任務！\n\n進度: {completed_count}/{total_count} ({progress_pct:.0f}%)\n{progress_bar}\n\n還差 {total_count - completed_count} 個任務就能獲得大獎了！💎\n\n繼續說「完成任務」來完成更多。",
        thinking=f"用戶完成了第 {completed_count} 個任務",
        action="任務完成",
        progress={
            "completed": completed_count,
            "total": total_count,
            "percentage": progress_pct
        }
    )


async def get_user_status(user_id: str) -> AgentResponse:
    """獲取用戶狀態"""
    user_profile = await memory_store.get_user_profile(user_id)
    active_card = await memory_store.get_active_card(user_id)

    # 獲取總獎勵
    from src.utils import FeedbackLearner
    learner = FeedbackLearner(memory_store)
    insights = await learner.get_user_insights(user_id)

    state_value = user_profile.current_engagement_state if isinstance(user_profile.current_engagement_state, str) else user_profile.current_engagement_state.value

    status_msg = f"📊 您的狀態\n\n"
    status_msg += f"參與狀態: {state_value}\n"
    status_msg += f"完成卡片: {user_profile.bingo_history.cards_completed} 張\n"
    status_msg += f"總獎勵: {insights.get('total_reward', 0)} 積分\n\n"

    if active_card and not active_card.completed:
        completed = sum(1 for t in active_card.tiles if t.completed)
        total = len(active_card.tiles)
        progress_pct = (completed / total) * 100

        status_msg += f"📋 當前卡片進度:\n"
        status_msg += f"  {completed}/{total} ({progress_pct:.0f}%)\n"
    else:
        status_msg += f"📋 當前沒有活躍卡片\n"
        status_msg += f"  說「生成卡片」來開始新挑戰！"

    return AgentResponse(
        message=status_msg,
        thinking="查詢用戶數據...",
        user_state=state_value,
        data=insights
    )


async def get_rewards(user_id: str) -> AgentResponse:
    """獲取獎勵信息"""
    from src.utils import FeedbackLearner
    learner = FeedbackLearner(memory_store)
    insights = await learner.get_user_insights(user_id)

    total_reward = insights.get('total_reward', 0)
    completion_rate = insights.get('completion_rate', 0) * 100

    msg = f"🏆 獎勵詳情\n\n"
    msg += f"總積分: {total_reward}\n"
    msg += f"完成率: {completion_rate:.0f}%\n\n"
    msg += f"獎勵規則:\n"
    msg += f"  • 開始卡片: +10 分\n"
    msg += f"  • 完成卡片: +100 分\n"
    msg += f"  • 狀態升級: +1000 分\n"

    return AgentResponse(
        message=msg,
        thinking="計算總獎勵...",
        data={"total_reward": total_reward, "completion_rate": completion_rate}
    )


@app.get("/api/visualizations")
async def get_visualizations():
    """獲取可視化圖片列表"""
    import os
    images = []
    image_files = [
        "interaction_sequence.png",
        "state_transition.png",
        "user_journey_timeline.png",
        "agent_decision_flow.png"
    ]

    for img in image_files:
        if os.path.exists(img):
            images.append({
                "name": img,
                "url": f"/images/{img}"
            })

    return {"images": images}


# 靜態文件服務
app.mount("/images", StaticFiles(directory="."), name="images")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
