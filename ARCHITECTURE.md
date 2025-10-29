# Bingo Card Engagement Agent - 架構說明

## 系統概述

這是一個基於 LangGraph 構建的智能 AI Agent，專門設計用於優化 Bingo 卡片遊戲化功能的用戶參與度。系統的核心特點是能夠**根據用戶反饋和歷史記憶動態調整決策**。

## 核心設計理念

### 1. 記憶驅動的決策 (Memory-Driven Decision Making)

系統通過持久化存儲用戶的所有互動歷史，形成"記憶"：

```
用戶互動 → 存儲記憶 → 分析模式 → 優化決策 → 更好的體驗
```

**記憶存儲包括：**
- 用戶檔案（狀態、行為原型）
- 卡片歷史（生成、完成情況）
- 反饋事件（所有用戶行為）
- Agent 行為（所有決策記錄）

### 2. 反饋學習循環 (Feedback Learning Loop)

系統實現了完整的反饋學習循環：

```python
# 1. 用戶行為產生反饋
user_completes_card → FeedbackEvent(event_type="card_completed", reward=+100)

# 2. 記錄並計算獎勵
learner.record_feedback(feedback)  # 保存到數據庫

# 3. 更新統計和模式
learner.update_statistics()  # 計算完成率、參與率等

# 4. 優化下次決策
best_profile = learner.get_best_profile_for_user()  # 基於歷史表現
optimal_dimension = learner.get_optimal_card_dimension()

# 5. 生成優化的卡片
card = generator.generate_card(profile=best_profile, dimension=optimal_dimension)
```

### 3. LangGraph 狀態機 (State Machine)

使用 LangGraph 構建的狀態機確保決策流程的可追溯性和可擴展性：

```
┌──────────────┐
│ Entry Point  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     載入用戶檔案、卡片歷史、
│ Load State   │ ←── 反饋歷史、行為歷史
└──────┬───────┘
       │
       ▼
┌──────────────┐     根據 action_type 路由：
│   Router     │ ←── "generate_card", "check_reminder", "process_feedback"
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│  Generate   │   │   Check     │
│   Card      │   │  Reminder   │
└──────┬──────┘   └──────┬──────┘
       │                 │
       │    ┌────────────┘
       │    │
       ▼    ▼
   ┌──────────────┐
   │   Process    │
   │  Feedback    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Save Actions │ ←── 持久化所有決策
   └──────┬───────┘
          │
          ▼
        [END]
```

## 關鍵組件詳解

### 1. 數據模型層 (src/models/)

#### BingoAgentState
這是 LangGraph 工作流中在節點間傳遞的核心狀態對象：

```python
class BingoAgentState(BaseModel):
    # 輸入
    user_id: str
    action_type: str  # "generate_card", "check_reminder", "process_feedback"

    # 用戶上下文
    user_profile: Optional[UserProfile]  # 用戶檔案
    current_card: Optional[BingoCard]    # 當前卡片

    # 決策輸出
    card_generation_response: Optional[CardGenerationResponse]
    reminder_decision: Optional[ReminderDecision]

    # 記憶與學習
    historical_actions: List[AgentAction]  # 歷史行為
    recent_feedback: List[FeedbackEvent]   # 最近反饋

    # 控制標誌
    should_generate_card: bool
    should_send_reminder: bool
    needs_user_state_update: bool
```

**設計要點：**
- 狀態包含完整的上下文信息
- 決策輸出直接存儲在狀態中
- 支援控制流標誌用於條件路由

#### UserProfile
用戶檔案模型，支援狀態轉換：

```python
State 3 (Pre-Active)  →  State 4 (Active)  →  State 5 (Engaged)
      ↓                        ↓                      ↓
  新用戶/不活躍          常規活躍用戶            高參與度用戶
  目標：完成第一張卡     目標：建立習慣        目標：保持參與
  策略：Easy Wins       策略：Gentle Nudge    策略：Challenge
```

### 2. 記憶存儲層 (src/memory/)

#### MemoryStore 抽象接口
定義了所有記憶操作的標準接口：

```python
class MemoryStore(ABC):
    @abstractmethod
    async def save_user_profile(profile: UserProfile) -> bool
    async def get_user_profile(user_id: str) -> Optional[UserProfile]
    async def save_bingo_card(card: BingoCard) -> bool
    async def get_active_card(user_id: str) -> Optional[BingoCard]
    async def save_feedback(feedback: FeedbackEvent) -> bool
    async def get_feedback_history(...) -> List[FeedbackEvent]
    # ... 更多方法
```

**設計優勢：**
- 抽象接口使存儲層可替換（SQLite → PostgreSQL → Redis）
- 異步操作提高性能
- 支援查詢優化和索引

#### SQLiteMemoryStore 實現
當前使用 SQLite 實現，包含四個核心表：

```sql
user_profiles       -- 用戶檔案
bingo_cards         -- 卡片歷史
feedback_events     -- 反饋事件
agent_actions       -- Agent 決策記錄
```

### 3. 反饋學習系統 (src/utils/feedback_learner.py)

#### FeedbackLearner 核心功能

**1) 獎勵計算**
```python
reward_map = {
    "card_completed": 100.0,
    "target_nudge_tile_completed": 50.0,
    "card_started": 10.0,
    "card_ignored": -1.0,
    "user_state_transition": 1000.0,
}
```

**2) 最佳配置推薦**
```python
async def get_best_profile_for_user(user_profile):
    # 分析歷史表現
    card_history = await memory.get_card_history(user_id)

    # 計算各配置的成功率
    profile_stats = calculate_completion_rates()

    # 返回最佳配置
    return best_performing_profile
```

**3) 流失風險檢測**
```python
async def detect_churn_risk(user_profile):
    # 檢查最近14天活動
    if no_recent_activity:
        return 0.9  # 高風險

    # 檢查活動下降趨勢
    if declining_activity:
        return 0.7

    # 檢查連續未完成
    if multiple_incomplete_cards:
        return 0.8

    return 0.2  # 低風險
```

### 4. Agent 節點層 (src/agents/)

#### StateLoader (狀態載入節點)
```python
async def load_user_state_node(state: BingoAgentState):
    # 1. 載入用戶檔案
    state.user_profile = await memory.get_user_profile(state.user_id)

    # 2. 載入當前卡片
    state.current_card = await memory.get_active_card(state.user_id)

    # 3. 載入最近反饋（用於上下文）
    state.recent_feedback = await memory.get_feedback_history(state.user_id)

    # 4. 載入歷史行為
    state.historical_actions = await memory.get_action_history(state.user_id)

    return state
```

#### CardGenerator (卡片生成節點)
```python
async def generate_card_node(state: BingoAgentState):
    # 1. 檢查是否應該生成
    should_generate, reason = await should_generate_card(state)

    # 2. 使用學習器確定最佳配置
    tile_profile = await learner.get_best_profile_for_user(state.user_profile)
    dimension = await learner.get_optimal_card_dimension(state.user_profile)

    # 3. 生成方塊
    tiles = await generate_tiles(tile_profile, dimension, state)

    # 4. 創建並保存卡片
    card = BingoCard(...)
    await memory.save_bingo_card(card)

    # 5. 更新狀態
    state.card_generation_response = CardGenerationResponse(card=card, ...)

    return state
```

#### ReminderNode (提醒評估節點)
```python
async def evaluate_reminder_node(state: BingoAgentState):
    # 1. 獲取當前卡片
    active_card = await memory.get_active_card(state.user_id)

    # 2. 檢查學習器建議
    should_send = await learner.should_send_reminder(state.user_profile, active_card)

    # 3. 應用提醒策略
    if card.is_stalled and progress == 0:
        decision = send_reminder("Stalled")
    elif progress > 70% and time_remaining < 72h:
        decision = send_reminder("Encouragement")
    elif progress < 50% and time_remaining < 24h:
        decision = send_reminder("Urgency")
    else:
        decision = do_nothing()

    state.reminder_decision = decision
    return state
```

#### FeedbackProcessor (反饋處理節點)
```python
async def process_feedback_node(state: BingoAgentState):
    # 1. 處理每個反饋事件
    for feedback in state.recent_feedback:
        # 計算獎勵
        await learner.record_feedback(feedback)

        # 更新 Bingo 歷史
        await update_bingo_history(state.user_id, feedback)

        # 檢測狀態轉換
        transitioned = await detect_state_transition(state.user_id, feedback)

    # 2. 獲取洞察
    insights = await learner.get_user_insights(state.user_id)
    churn_risk = await learner.detect_churn_risk(state.user_profile)

    state.add_action(AgentAction(
        action_type="feedback_processed",
        details={"churn_risk": churn_risk, ...}
    ))

    return state
```

### 5. LangGraph 工作流 (src/graph/bingo_agent_graph.py)

#### 工作流構建
```python
def _build_graph(self):
    workflow = StateGraph(BingoAgentState)

    # 添加節點
    workflow.add_node("load_state", self.state_loader.load_user_state_node)
    workflow.add_node("generate_card", self.card_generator.generate_card_node)
    workflow.add_node("evaluate_reminder", self.reminder_node.evaluate_reminder_node)
    workflow.add_node("process_feedback", self.feedback_processor.process_feedback_node)
    workflow.add_node("save_actions", self._save_actions_node)

    # 設置入口
    workflow.set_entry_point("load_state")

    # 添加條件路由
    workflow.add_conditional_edges(
        "load_state",
        self._route_action,  # 路由函數
        {
            "generate_card": "generate_card",
            "check_reminder": "evaluate_reminder",
            "process_feedback": "process_feedback",
            "end": "save_actions",
        }
    )

    # 所有行為節點 → save_actions
    workflow.add_edge("generate_card", "save_actions")
    workflow.add_edge("evaluate_reminder", "save_actions")
    workflow.add_edge("process_feedback", "save_actions")

    # save_actions → END
    workflow.add_edge("save_actions", END)

    return workflow.compile()
```

#### 路由邏輯
```python
def _route_action(state: BingoAgentState) -> str:
    """根據 action_type 決定執行哪個節點"""
    if state.errors:
        return "end"

    action_type = state.action_type.lower()

    if "generate" in action_type or "card" in action_type:
        return "generate_card"
    elif "remind" in action_type or "check" in action_type:
        return "check_reminder"
    elif "feedback" in action_type or "process" in action_type:
        return "process_feedback"
    else:
        return "end"
```

## 決策流程示例

### 場景 1: 為新用戶生成卡片

```
1. [Entry] user_id="user_001", action_type="generate_card"

2. [Load State]
   - 載入 UserProfile: State_3_Pre_Active, Driver_Heavy
   - 無當前卡片
   - 載入反饋歷史：空（新用戶）

3. [Router] → "generate_card"

4. [Generate Card]
   a. 檢查資格：✓ 新用戶，無歷史卡片
   b. 學習器推薦：
      - tile_profile = Easy_Wins (State 3 策略)
      - dimension = 3x3
   c. 生成方塊：
      - 80% 主要模式（駕駛）方塊
      - 20% 簡單任務方塊
   d. 創建卡片：
      - card_id = "card_abc123"
      - duration = 7 天
      - tiles = 9 個方塊
   e. 保存到數據庫
   f. 更新狀態：card_generation_response.success = True

5. [Save Actions]
   - 保存 AgentAction(action_type="card_generated", ...)

6. [END]
   - 返回最終狀態給調用者
```

### 場景 2: 處理用戶完成卡片的反饋

```
1. [Entry] user_id="user_001", action_type="process_feedback"
   - recent_feedback = [FeedbackEvent(event_type="card_completed", ...)]

2. [Load State]
   - 載入 UserProfile: State_3_Pre_Active
   - 載入反饋歷史

3. [Router] → "process_feedback"

4. [Process Feedback]
   a. 記錄反饋：
      - 計算獎勵：+100 (card_completed)
      - 可能額外獎勵：+20 (early_completion) + 50 (first_completion)
      - 總獎勵：+170
   b. 更新 Bingo 歷史：
      - cards_completed: 0 → 1
      - completion_rate: 0 → 1.0
   c. 檢測狀態轉換：
      - 觸發條件：State 3 + card_completed
      - 執行轉換：State_3 → State_4
      - 記錄轉換事件：+1000 獎勵
   d. 更新狀態：needs_user_state_update = True

5. [Save Actions]
   - 保存 AgentAction(action_type="state_transition_detected", ...)

6. [END]
```

### 場景 3: 檢查是否發送提醒

```
1. [Entry] user_id="user_002", action_type="check_reminder"

2. [Load State]
   - 載入 UserProfile: State_4_Active
   - 載入當前卡片：
     * progress = 75%
     * time_remaining = 48 hours
     * is_stalled = False

3. [Router] → "evaluate_reminder"

4. [Evaluate Reminder]
   a. 檢查學習器建議：
      - 用戶歷史響應率：60%（中等）
      - 建議：✓ 可以發送
   b. 應用提醒策略：
      - 規則匹配：progress > 70% AND time_remaining < 72h
      - 選擇模板：Encouragement
   c. 生成消息：
      "You're almost there! Just a few more tiles..."
   d. 創建決策：
      action = Send_Reminder
      template = Encouragement
      message_text = "..."

5. [Save Actions]
   - 保存 AgentAction(action_type="reminder_sent", ...)

6. [END]
```

## 記憶如何影響決策

### 1. 卡片配置優化

**無記憶的決策（傳統方法）：**
```python
# 總是使用固定策略
if state == State_3:
    return Easy_Wins
elif state == State_4:
    return Gentle_Nudge
```

**有記憶的決策（本系統）：**
```python
# 基於歷史表現動態調整
card_history = memory.get_card_history(user_id)

# 計算每種配置的成功率
for card in card_history:
    success_rate[card.tile_profile] = card.completed / attempts

# 選擇最佳配置
best_profile = max(success_rate, key=success_rate.get)

# 如果無歷史，使用默認策略
if not card_history:
    return default_strategy_by_state(state)

return best_profile
```

### 2. 提醒頻率優化

**記憶驅動的提醒決策：**
```python
# 追蹤用戶對提醒的響應
reminder_responses = memory.get_feedback_history(
    user_id,
    filter=lambda f: f.metadata.get("after_reminder")
)

# 計算提醒效果
positive_responses = count_positive(reminder_responses)
effectiveness = positive_responses / len(reminder_responses)

# 如果效果低，減少提醒頻率
if effectiveness < 0.3:
    return False  # 不發送

return True  # 繼續發送
```

### 3. 流失預警

**基於記憶的流失檢測：**
```python
# 分析活動模式
recent_14d = get_feedback(user_id, last_14_days)
recent_7d = get_feedback(user_id, last_7_days)
prev_7d = get_feedback(user_id, days_8_to_14)

# 檢測活動下降
activity_ratio = len(recent_7d) / len(prev_7d)
if activity_ratio < 0.5:
    churn_risk = 0.7  # 活動明顯下降

# 檢測連續未完成
recent_cards = memory.get_card_history(user_id, limit=3)
if all(not card.completed for card in recent_cards):
    churn_risk = 0.8  # 多次未完成

return churn_risk
```

## 可擴展性設計

### 1. 替換存儲層

```python
# 當前使用 SQLite
memory_store = SQLiteMemoryStore()

# 可輕鬆替換為 PostgreSQL
from src.memory import PostgreSQLMemoryStore
memory_store = PostgreSQLMemoryStore(connection_string)

# 或 Redis
from src.memory import RedisMemoryStore
memory_store = RedisMemoryStore(redis_url)

# Agent 代碼無需修改
agent = BingoAgentGraph(memory_store)
```

### 2. 添加新的決策節點

```python
# 1. 創建新節點
class PersonalizationNode:
    async def personalize_content_node(self, state: BingoAgentState):
        # 個性化邏輯
        return state

# 2. 添加到工作流
workflow.add_node("personalize", self.personalizer.personalize_content_node)

# 3. 添加路由
workflow.add_edge("load_state", "personalize")
workflow.add_edge("personalize", "generate_card")
```

### 3. 集成 LLM

```python
from langchain_openai import ChatOpenAI

class LLMEnhancedAgent(BingoAgentGraph):
    def __init__(self, memory_store, llm=None):
        super().__init__(memory_store)
        self.llm = llm or ChatOpenAI()

    async def generate_personalized_tiles(self, user_profile, tile_profile):
        prompt = f"""
        根據用戶檔案生成個性化的 Bingo 方塊：
        - 狀態：{user_profile.current_engagement_state}
        - 原型：{user_profile.behavioral_archetype}
        - 配置：{tile_profile}

        生成9個有趣且符合用戶習慣的任務。
        """

        response = await self.llm.ainvoke(prompt)
        tiles = self.parse_llm_response(response)

        return tiles
```

## 性能考量

### 1. 異步操作
所有 I/O 操作都使用 `async/await`，避免阻塞：

```python
# ✓ 並行查詢
user_profile, active_card, feedback = await asyncio.gather(
    memory.get_user_profile(user_id),
    memory.get_active_card(user_id),
    memory.get_feedback_history(user_id)
)

# ✗ 順序查詢（慢）
user_profile = await memory.get_user_profile(user_id)
active_card = await memory.get_active_card(user_id)
feedback = await memory.get_feedback_history(user_id)
```

### 2. 批量處理
支援批量處理多個用戶：

```python
async def process_daily_batch(user_ids: List[str]):
    tasks = []
    for user_id in user_ids:
        tasks.append(agent.generate_card_for_user(user_id))
        tasks.append(agent.check_reminder_for_user(user_id))

    results = await asyncio.gather(*tasks)
    return results
```

### 3. 緩存策略
可在記憶層添加緩存：

```python
class CachedMemoryStore(SQLiteMemoryStore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    async def get_user_profile(self, user_id):
        if user_id in self.cache:
            return self.cache[user_id]

        profile = await super().get_user_profile(user_id)
        self.cache[user_id] = profile
        return profile
```

## 總結

這個系統展示了如何使用 LangGraph 構建一個**記憶驅動、反饋學習**的 AI Agent：

1. **LangGraph** 提供了清晰的狀態管理和工作流編排
2. **記憶存儲** 確保所有決策都基於完整的歷史上下文
3. **反饋學習** 讓系統不斷優化，提高用戶參與度
4. **模塊化設計** 使系統易於擴展和維護

核心理念：**記憶 + 反饋 + 學習 = 智能決策**
