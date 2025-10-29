#!/bin/bash
# Bingo Card AI Agent Web App 啟動腳本

echo "🚀 啟動 Bingo Card AI Agent Web 應用..."
echo ""

# 檢查並停止現有進程
if pgrep -f "web_app.py" > /dev/null; then
    echo "⚠️  發現現有進程，正在停止..."
    pkill -f "web_app.py"
    sleep 2
fi

# 啟動新進程
echo "✨ 啟動 Web 服務器..."
nohup python web_app.py > web_app.log 2>&1 &

# 等待啟動
sleep 3

# 檢查是否成功啟動
if pgrep -f "web_app.py" > /dev/null; then
    echo ""
    echo "✅ Web 應用已成功啟動！"
    echo ""
    echo "📌 訪問方式："
    echo "   本地訪問: http://localhost:8000"
    echo "   網絡訪問: http://0.0.0.0:8000"
    echo ""
    echo "📋 查看日誌: tail -f web_app.log"
    echo "🛑 停止服務: pkill -f web_app.py"
    echo ""
else
    echo ""
    echo "❌ 啟動失敗，請檢查日誌："
    echo "   tail -50 web_app.log"
    echo ""
fi
