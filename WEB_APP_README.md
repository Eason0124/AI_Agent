# 🌐 Bingo Card AI Agent - 互動式 Web 應用

一個基於 FastAPI + LangGraph 的互動式 Web 界面，讓您可以直接與 AI Agent 對話並體驗完整的遊戲化流程。

---

## 🚀 快速開始

### 方法 1: 使用啟動腳本（推薦）

```bash
./start_web_app.sh
```

### 方法 2: 手動啟動

```bash
python web_app.py
```

---

## 📌 訪問網站

啟動後，在瀏覽器中打開：

- **本地訪問**: http://localhost:8000
- **網絡訪問**: http://0.0.0.0:8000
- **局域網訪問**: http://[你的IP地址]:8000

---

## 💬 使用說明

### 1. 開始遊戲

輸入「**開始**」來註冊為新用戶（自動分配 State_3 新手狀態）

### 2. 生成卡片

輸入「**生成卡片**」來獲取您的第一張 Bingo 卡片

### 3. 完成任務

輸入「**完成任務**」來標記任務完成（每次完成一個）

### 4. 查看狀態

輸入「**查看狀態**」來查看當前進度和獎勵

### 5. 其他指令

- 「**查看獎勵**」- 查看積分詳情
- 任意聊天 - Agent 會引導您

---

## 🎯 功能特色

### ✨ 實時互動
- 聊天式界面，自然對話
- Agent 思考過程可視化
- 實時進度追蹤

### 🎮 完整遊戲流程
- 用戶註冊與檔案創建
- 智能卡片生成（基於用戶狀態）
- 任務完成與進度追蹤
- 狀態升級系統（State 3 → State 4）
- 獎勵系統（+10/+100/+1000 積分）

### 📊 側邊欄功能
- 快速操作按鈕
- 當前狀態顯示
- 進度條可視化
- 使用說明
- 獎勵規則

### 🤖 AI Agent 特性
- 基於 LangGraph 的決策流程
- SQLite 持久化記憶
- 反饋學習系統
- 狀態轉換檢測

---

## 🎨 界面預覽

```
┌─────────────────────────────────────────────┐
│  🎮 Bingo Card AI Agent                    │
│  基於 LangGraph + 記憶 + 反饋學習          │
├─────────────────────────┬───────────────────┤
│                         │  💡 快速操作      │
│  聊天對話區             │  ┌───┬───┐        │
│                         │  │🚀 │🎲 │        │
│  👤 用戶: 開始          │  └───┴───┘        │
│                         │  ┌───┬───┐        │
│  🤖 Agent: 歡迎！       │  │✅ │📊 │        │
│  💭 檢測到新用戶...     │  └───┴───┘        │
│  ⚡ 已創建用戶檔案      │                    │
│                         │  🎯 當前狀態       │
│                         │  State 3 (新手)   │
│                         │  ▓▓▓▓▓░░░░░ 50%   │
│                         │                    │
│  [輸入框]        [發送] │  📖 使用說明       │
└─────────────────────────┴───────────────────┘
```

---

## 🛠️ 技術架構

### 後端 (FastAPI)
- **框架**: FastAPI (async)
- **AI Engine**: LangGraph + BingoAgentGraph
- **記憶**: SQLite (web_demo.db)
- **端點**:
  - `GET /` - Web 界面
  - `POST /api/chat` - 聊天 API
  - `GET /api/visualizations` - 圖表列表

### 前端 (HTML/JS)
- **界面**: 響應式聊天 UI
- **樣式**: CSS Grid + Flexbox
- **交互**: Vanilla JavaScript (Fetch API)
- **特效**: CSS 動畫 + 漸變背景

---

## 📁 相關文件

```
AI_Agent/
├── web_app.py              # FastAPI 後端服務器
├── static/
│   └── index.html          # 前端界面
├── start_web_app.sh        # 啟動腳本
├── web_app.log             # 運行日誌
├── web_demo.db             # Web 版數據庫
└── WEB_APP_README.md       # 本文檔
```

---

## 🔧 管理命令

### 查看日誌
```bash
tail -f web_app.log
```

### 停止服務
```bash
pkill -f web_app.py
```

### 檢查進程
```bash
ps aux | grep web_app.py
```

### 清理數據庫
```bash
rm web_demo.db
```

---

## 🎮 完整遊戲流程示例

### 1️⃣ 註冊新用戶
```
👤: 開始
🤖: 歡迎！您已成功註冊。
    當前狀態：State 3 (新手)
    💭 檢測到新用戶 → 創建 State_3 檔案
    ⚡ 已創建用戶檔案
```

### 2️⃣ 生成首張卡片
```
👤: 生成卡片
🤖: 為您生成了新的 Bingo 卡片！
    配置: Profile_Easy_Wins
    維度: 3x3
    📋 任務列表:
      1. Complete 1 driving trip
      2. Complete 1 driving trip
      ...
    💭 用戶狀態: State_3 → 生成適配卡片
    ⚡ 已生成新卡片
```

### 3️⃣ 完成任務
```
👤: 完成任務
🤖: 完成了一個任務！
    進度: 1/9 (11%)
    ▓░░░░░░░░░
    💭 用戶完成了第 1 個任務
    ⚡ 任務完成
```

### 4️⃣ 完成卡片 + 狀態升級
```
👤: 完成任務 (x8 次)
🤖: 🎊 恭喜！您完成了整張卡片！
    ✨ 重大突破！您已升級為活躍用戶！
    🏆 獲得獎勵:
      • 卡片完成: +100 積分
      • 狀態升級: +1000 積分
      • 總計: +1110 積分
    💭 完成所有任務 → 觸發狀態升級 → State_3 → State_4
    ⚡ 卡片完成 + 狀態升級
```

---

## 🎯 獎勵系統

| 事件 | 積分 | 觸發條件 |
|------|------|----------|
| 開始卡片 | +10 | 完成第一個任務 |
| 完成卡片 | +100 | 完成所有任務 |
| 狀態升級 | +1000 | State 3 → State 4 |

---

## ⬆️ 狀態升級路徑

```
State 1 (未註冊)
    ↓ 註冊
State 2 (已註冊)
    ↓ 首次使用
State 3 (新手) ← 您從這裡開始
    ↓ 完成首張卡片 (+1000分)
State 4 (活躍) ← Web Demo 可達到
    ↓ 持續參與多張卡片
State 5 (深度參與)
```

---

## 🐛 故障排除

### 問題 1: 無法訪問網站
**解決方案**:
```bash
# 檢查服務器是否運行
ps aux | grep web_app.py

# 重新啟動
./start_web_app.sh
```

### 問題 2: 端口被占用
**解決方案**:
```bash
# 查看占用 8000 端口的進程
lsof -i :8000

# 修改 web_app.py 中的端口號
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 問題 3: Agent 回應錯誤
**解決方案**:
```bash
# 查看詳細日誌
tail -100 web_app.log

# 清理並重啟
rm web_demo.db
./start_web_app.sh
```

---

## 🚀 進階使用

### 同時運行多個用戶
每個瀏覽器會自動生成唯一的 user_id，可以在不同瀏覽器/標籤頁中模擬多用戶。

### 查看數據庫
```bash
sqlite3 web_demo.db
.tables
.schema user_profiles
SELECT * FROM user_profiles;
```

### API 測試
```bash
# 發送聊天消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "開始"}'
```

---

## 📞 更多信息

- 查看完整 Agent 實現: `demo_interactive.py`
- 查看視覺化流程圖: `visualize_interaction.py`
- 查看數據庫內容: `view_demo_db.py`

---

## ✨ 享受與 AI Agent 的互動！

祝您玩得開心！🎮🎉
