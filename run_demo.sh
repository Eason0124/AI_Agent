#!/bin/bash
# 快速演示腳本

echo "🎮 開始 Bingo Card Agent 互動演示..."
echo ""

echo "1️⃣ 註冊新用戶..."
python test_web_agent.py "開始"
sleep 2

echo ""
echo "2️⃣ 生成 Bingo 卡片..."
python test_web_agent.py "生成卡片"
sleep 2

echo ""
echo "3️⃣ 完成第一個任務..."
python test_web_agent.py "完成任務"
sleep 2

echo ""
echo "4️⃣ 查看當前狀態..."
python test_web_agent.py "查看狀態"

echo ""
echo "✅ 演示完成！"
echo ""
echo "💡 您可以運行以下命令繼續互動："
echo "   python test_web_agent.py"
