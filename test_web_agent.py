"""
命令行測試 Web Agent API
如果無法打開瀏覽器，可以用這個腳本與 Agent 互動
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
user_id = "cli_user"

def chat(message):
    """發送消息給 Agent"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "user_id": user_id,
                "message": message
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # 顯示回應
            print("\n" + "="*60)
            print("🤖 Agent 回應:")
            print("="*60)
            print(data.get("message", ""))

            if data.get("thinking"):
                print(f"\n💭 思考: {data['thinking']}")

            if data.get("action"):
                print(f"⚡ 行動: {data['action']}")

            if data.get("user_state"):
                print(f"\n📊 當前狀態: {data['user_state']}")

            if data.get("progress"):
                prog = data['progress']
                print(f"📈 進度: {prog['completed']}/{prog['total']} ({prog['percentage']:.0f}%)")

            print("="*60 + "\n")
            return True
        else:
            print(f"❌ 錯誤: HTTP {response.status_code}")
            print(response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器。請確認服務器正在運行：")
        print("   python web_app.py")
        return False
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False


def main():
    """主程序"""
    print("\n" + "🎮 " + "="*58 + " 🎮")
    print("  Bingo Card AI Agent - 命令行互動測試")
    print("🎮 " + "="*58 + " 🎮\n")

    print("📌 可用指令：")
    print("   • 開始 - 註冊新用戶")
    print("   • 生成卡片 - 獲取 Bingo 卡片")
    print("   • 完成任務 - 完成一個任務")
    print("   • 查看狀態 - 查看進度")
    print("   • 查看獎勵 - 查看積分")
    print("   • exit/quit - 退出")
    print()

    # 如果有命令行參數，直接執行
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print(f"👤 您: {message}")
        chat(message)
        return

    # 互動模式
    while True:
        try:
            user_input = input("👤 您: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n👋 再見！\n")
                break

            chat(user_input)

        except KeyboardInterrupt:
            print("\n\n👋 再見！\n")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
