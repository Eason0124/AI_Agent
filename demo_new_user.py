import requests
import sys

user_id = "demo_user_new"

def chat(msg):
    r = requests.post("http://localhost:8000/api/chat", 
                     json={"user_id": user_id, "message": msg})
    data = r.json()
    
    print("\n" + "="*60)
    print(f"👤 您: {msg}")
    print("="*60)
    print("🤖 Agent:", data['message'])
    if data.get('thinking'):
        print(f"💭 思考: {data['thinking']}")
    if data.get('action'):
        print(f"⚡ 行動: {data['action']}")
    if data.get('progress'):
        p = data['progress']
        print(f"📊 進度: {p['completed']}/{p['total']} ({p['percentage']:.0f}%)")
    print("="*60)

# 完整演示
print("\n🎮 全新用戶完整互動演示\n")

chat("開始")
chat("生成卡片")
for i in range(9):
    chat("完成任務")
chat("查看獎勵")

print("\n✅ 演示完成！")
