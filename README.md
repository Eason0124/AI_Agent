# Bingo Card Engagement Agent with LangGraph

一個基於 LangGraph 的 AI Agent，用於優化 Bingo 卡片遊戲化功能的用戶參與度和習慣養成。該系統能根據用戶反饋和歷史記憶來動態調整決策。

## 🎯 核心功能

### 1. 智能卡片生成
- 根據用戶狀態（Pre-Active, Active, Engaged）自動調整卡片難度
- 使用反饋學習優化卡片配置（Easy Wins, Gentle Nudge, Mode Explorer, Challenge）
- 動態調整卡片維度（3x3 或 5x5）和持續時間（7天或14天）

### 2. 記憶與學習系統
- SQLite 持久化存儲用戶檔案、卡片歷史和反饋事件
- 實時學習用戶行為模式
- 基於獎勵機制的反饋系統：
  - +100: 完成卡片
  - +50: 完成目標推動方塊
  - +10: 開始卡片
  - -1: 忽略卡片
  - +1000: 用戶狀態轉換

### 3. 智能提醒系統
- 根據卡片進度和時間自動決定是否發送提醒
- 四種提醒模板：鼓勵、緊急、狀態更新、停滯提醒
- 學習用戶對提醒的響應，避免通知疲勞

### 4. 用戶狀態管理
- 自動檢測並觸發用戶狀態轉換
- 追蹤參與率和完成率
- 流失風險預警

## 🏗️ 架構設計

### LangGraph 工作流

```
┌─────────────┐
│ Load State  │ ← 載入用戶檔案和上下文
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │ ← 根據 action_type 路由
└──────┬──────┘
       │
       ├─→ Generate Card    ← 生成新卡片
       ├─→ Check Reminder   ← 評估提醒
       ├─→ Process Feedback ← 處理反饋學習
       │
       ▼
┌─────────────┐
│ Save Actions│ ← 持久化所有決策
└──────┬──────┘
       │
       ▼
      END
```

### 模塊結構

```
src/
├── models/              # 數據模型
│   ├── user_state.py   # 用戶狀態、行為原型
│   ├── bingo_card.py   # 卡片模型
│   ├── reminder.py     # 提醒模型
│   └── agent_state.py  # LangGraph 狀態
│
├── memory/              # 記憶存儲層
│   ├── base.py         # 抽象接口
│   └── sqlite_store.py # SQLite 實現
│
├── agents/              # LangGraph 節點
│   ├── state_loader.py       # 狀態載入
│   ├── card_generator.py     # 卡片生成
│   ├── reminder_node.py      # 提醒評估
│   └── feedback_processor.py # 反饋處理
│
├── graph/               # LangGraph 工作流
│   └── bingo_agent_graph.py
│
└── utils/               # 工具模塊
    └── feedback_learner.py   # 反饋學習系統
```

## 🚀 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 配置環境變量

```bash
cp .env.example .env
# 編輯 .env 文件設置您的配置
```

### 基礎使用

```python
import asyncio
from src.models import UserProfile, EngagementState, BehavioralArchetype
from src.memory import SQLiteMemoryStore
from src.graph import BingoAgentGraph

async def main():
    # 初始化
    memory_store = SQLiteMemoryStore()
    await memory_store.initialize()
    agent = BingoAgentGraph(memory_store)

    # 創建用戶
    user_profile = UserProfile(
        user_id="user_001",
        current_engagement_state=EngagementState.STATE_3_PRE_ACTIVE,
        behavioral_archetype=BehavioralArchetype.DRIVER_HEAVY,
    )
    await memory_store.save_user_profile(user_profile)

    # 生成卡片
    result = await agent.generate_card_for_user("user_001")

    if result.card_generation_response.success:
        card = result.card_generation_response.card
        print(f"卡片已生成: {card.card_id}")
        print(f"維度: {card.dimension.value}")
        print(f"難度配置: {card.tile_profile.value}")

    # 處理反饋
    from src.models import FeedbackEvent
    feedback = FeedbackEvent(
        user_id="user_001",
        card_id=card.card_id,
        event_type="card_completed"
    )
    await memory_store.save_feedback(feedback)
    await agent.process_user_feedback("user_001")

    # 檢查提醒
    reminder_result = await agent.check_reminder_for_user("user_001")
    if reminder_result.reminder_decision.action.value == "Send_Reminder":
        print(f"提醒: {reminder_result.reminder_decision.message_text}")

asyncio.run(main())
```

### 運行示例

```bash
# 基礎使用示例
python examples/basic_usage.py

# API 集成示例
python examples/api_integration.py
```

## 📊 核心決策邏輯

### 卡片生成策略

| 用戶狀態 | 行為原型 | 卡片配置 | 理由 (BJ Fogg Model) |
|---------|---------|---------|---------------------|
| State 3 (Pre-Active) | Driver-Heavy | 3x3, 7天<br/>Profile: Easy Wins | 最大化能力，讓任務簡單 |
| State 4 (Active) | Driver-Heavy | 3x3, 7-14天<br/>Profile: Gentle Nudge | 提供推動，引入小挑戰 |
| State 4 (Active) | Occasional-Transit | 3x3, 7天<br/>Profile: Mode Explorer | 建立習慣，增加頻率 |
| State 5 (Engaged) | Multimodal-Active | 5x5, 14天<br/>Profile: Challenge | 維持動機，提供複雜挑戰 |

### 提醒策略

```python
# 規則 1: 停滯且無進度 (48小時無動作)
if progress == 0 and stalled:
    send_reminder(template="Stalled")

# 規則 2: 高進度但時間緊迫 (>70% 進度, <72小時剩餘)
elif progress > 70% and time_remaining < 72h:
    send_reminder(template="Encouragement")

# 規則 3: 低進度即將過期 (<50% 進度, <24小時剩餘)
elif progress < 50% and time_remaining < 24h:
    send_reminder(template="Urgency")

# 默認: 不發送 (避免通知疲勞)
else:
    do_nothing()
```

## 🔧 API 集成

### FastAPI 示例

```python
from fastapi import FastAPI
from src.graph import BingoAgentGraph
from src.memory import SQLiteMemoryStore

app = FastAPI()
agent_api = BingoAgentGraph(SQLiteMemoryStore())

@app.post("/cards/generate/{user_id}")
async def generate_card(user_id: str):
    result = await agent_api.generate_card_for_user(user_id)
    return {
        "success": result.card_generation_response.success,
        "card": result.card_generation_response.card
    }

@app.post("/feedback/submit")
async def submit_feedback(user_id: str, event_type: str, card_id: str):
    feedback = FeedbackEvent(
        user_id=user_id,
        card_id=card_id,
        event_type=event_type
    )
    await agent_api.memory.save_feedback(feedback)
    result = await agent_api.process_user_feedback(user_id)
    return {"success": True, "state_transition": result.needs_user_state_update}
```

## 📈 反饋與學習

### 反饋事件類型

- `card_started`: 用戶開始卡片
- `card_completed`: 用戶完成卡片
- `card_ignored`: 用戶忽略卡片
- `tile_completed`: 完成單個方塊
- `target_nudge_tile_completed`: 完成目標推動方塊
- `user_state_transition`: 用戶狀態轉換

### 學習機制

```python
from src.utils import FeedbackLearner

learner = FeedbackLearner(memory_store)

# 獲取最佳卡片配置
best_profile = await learner.get_best_profile_for_user(user_profile)

# 獲取用戶洞察
insights = await learner.get_user_insights(user_id)
# {
#   "engagement_state": "State_4_Active",
#   "total_reward": 1250.0,
#   "completion_rate": 0.75,
#   "participation_rate": 0.90,
#   "churn_risk": 0.2
# }

# 檢測流失風險
churn_risk = await learner.detect_churn_risk(user_profile)
if churn_risk > 0.7:
    # 採取挽留措施
    pass
```

## 🧪 測試

運行完整的示例套件：

```bash
python examples/basic_usage.py
```

這將演示：
1. 為新用戶生成卡片
2. 處理反饋和學習
3. 提醒邏輯
4. 學習洞察和流失檢測

## 🎓 核心概念

### 1. LangGraph 狀態管理

`BingoAgentState` 是在節點之間傳遞的核心狀態對象，包含：
- 用戶檔案和上下文
- 當前卡片狀態
- 決策輸出
- 歷史行為和反饋
- 控制流標誌

### 2. 記憶持久化

所有用戶數據、卡片歷史和反饋都持久化在 SQLite 數據庫中，支援：
- 用戶檔案查詢和更新
- 卡片歷史追蹤
- 反饋事件記錄
- 行為歷史查詢

### 3. 反饋學習循環

```
用戶行為 → 反饋事件 → 獎勵計算 → 更新統計 → 優化決策 → 新卡片/提醒
    ↑                                                           ↓
    └─────────────────── 持續改進 ───────────────────────────┘
```

## 🔮 擴展建議

### 1. 多用戶批量處理

```python
async def process_daily_batch(user_ids: List[str]):
    """每日批量處理所有用戶"""
    agent = BingoAgentGraph()

    for user_id in user_ids:
        # 檢查是否需要生成新卡片
        await agent.generate_card_for_user(user_id)

        # 檢查是否需要發送提醒
        await agent.check_reminder_for_user(user_id)
```

### 2. 集成 LLM 做更智能決策

```python
from langchain_openai import ChatOpenAI

class LLMEnhancedCardGenerator(CardGenerator):
    def __init__(self, memory_store, llm):
        super().__init__(memory_store)
        self.llm = llm

    async def generate_tile_descriptions(self, profile, user_state):
        """使用 LLM 生成個性化的方塊描述"""
        prompt = f"""
        為以下用戶生成有趣的 Bingo 卡片方塊：
        - 狀態: {user_state.user_profile.current_engagement_state}
        - 原型: {user_state.user_profile.behavioral_archetype}
        - 配置: {profile}

        生成 9 個有趣且個性化的任務描述。
        """
        response = await self.llm.ainvoke(prompt)
        # 解析並返回
        return response
```

### 3. 實時分析儀表板

使用 Streamlit 或 Dash 創建實時監控面板：
- 用戶參與度指標
- 完成率趨勢
- 流失風險用戶列表
- A/B 測試結果

### 4. A/B 測試框架

```python
class ABTestingAgent(BingoAgentGraph):
    async def generate_card_with_variant(self, user_id: str, variant: str):
        """為 A/B 測試生成不同變體的卡片"""
        # 根據變體調整策略
        if variant == "A":
            # 控制組：標準策略
            pass
        elif variant == "B":
            # 實驗組：新策略
            pass

        result = await self.generate_card_for_user(user_id)
        # 記錄變體信息
        return result
```

## 📝 最佳實踐

1. **定期備份數據庫**: 使用 SQLite 的備份功能
2. **監控性能**: 追蹤 agent 響應時間和決策質量
3. **逐步推出**: 從小部分用戶開始，逐步擴展
4. **A/B 測試**: 對新策略進行嚴格測試
5. **用戶隱私**: 確保符合數據保護法規

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

## 📧 聯繫

如有問題或建議，請提交 GitHub Issue。

---

**Built with LangGraph** 🦜🔗
