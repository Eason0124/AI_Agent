#!/usr/bin/env python3
"""
互動式 AI Agent 界面 - 命令行版本
提供類似網頁的互動體驗
"""
import requests
import sys
import os

BASE_URL = "http://localhost:8000"
user_id = "interactive_user"

# ANSI 顏色代碼
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║            🎮  BINGO CARD AI AGENT 互動界面  🎮               ║")
    print("║                                                                ║")
    print("║              基於 LangGraph + 記憶 + 反饋學習                 ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

def print_menu():
    print(f"\n{Colors.BOLD}{Colors.YELLOW}━━━━━━━━━━━━━━━━ 快速選單 ━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"{Colors.GREEN}")
    print("  [1] 🚀 開始 - 註冊新用戶")
    print("  [2] 🎲 生成卡片 - 獲取 Bingo 卡片")
    print("  [3] ✅ 完成任務 - 完成一個任務")
    print("  [4] 📊 查看狀態 - 查看當前進度")
    print("  [5] 🏆 查看獎勵 - 查看積分獎勵")
    print("  [6] 💬 自由輸入 - 輸入任何內容")
    print("  [0] 👋 退出")
    print(f"{Colors.END}")
    print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}\n")

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
            print(f"\n{Colors.BOLD}{Colors.BLUE}{'═'*60}{Colors.END}")
            print(f"{Colors.BOLD}{Colors.CYAN}🤖 Agent 回應:{Colors.END}")
            print(f"{Colors.BOLD}{Colors.BLUE}{'═'*60}{Colors.END}")

            # 主要消息
            print(f"{Colors.GREEN}{data.get('message', '')}{Colors.END}")

            # 思考過程
            if data.get('thinking'):
                print(f"\n{Colors.YELLOW}💭 [Agent 思考]: {data['thinking']}{Colors.END}")

            # 行動
            if data.get('action'):
                print(f"{Colors.CYAN}⚡ [Agent 行動]: {data['action']}{Colors.END}")

            # 當前狀態
            if data.get('user_state'):
                state_map = {
                    'State_3_Pre_Active': '🌱 State 3 (新手)',
                    'State_4_Active': '🔥 State 4 (活躍)',
                    'State_5_Engaged': '⭐ State 5 (深度參與)'
                }
                state_display = state_map.get(data['user_state'], data['user_state'])
                print(f"\n{Colors.BOLD}📊 當前狀態: {state_display}{Colors.END}")

            # 進度條
            if data.get('progress'):
                prog = data['progress']
                percentage = prog['percentage']
                filled = int(percentage / 10)
                bar = '▓' * filled + '░' * (10 - filled)
                print(f"{Colors.BOLD}📈 進度: {prog['completed']}/{prog['total']} ({percentage:.0f}%){Colors.END}")
                print(f"   {Colors.GREEN}{bar}{Colors.END}")

            print(f"{Colors.BOLD}{Colors.BLUE}{'═'*60}{Colors.END}\n")
            return True
        else:
            print(f"{Colors.RED}❌ 錯誤: HTTP {response.status_code}{Colors.END}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}")
        print("❌ 無法連接到服務器。")
        print("請確認服務器正在運行：python web_app.py")
        print(f"{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ 錯誤: {e}{Colors.END}")
        return False

def main():
    """主程序"""
    clear_screen()
    print_header()

    print(f"{Colors.CYAN}")
    print("歡迎使用 AI Agent 互動界面！")
    print("您可以通過選單或直接輸入來與 Agent 對話。")
    print(f"{Colors.END}")

    while True:
        print_menu()

        choice = input(f"{Colors.BOLD}請選擇 (0-6) 或直接輸入訊息: {Colors.END}").strip()

        if not choice:
            continue

        # 處理選單選擇
        if choice == '0':
            print(f"\n{Colors.CYAN}👋 感謝使用！再見！{Colors.END}\n")
            break
        elif choice == '1':
            message = "開始"
        elif choice == '2':
            message = "生成卡片"
        elif choice == '3':
            message = "完成任務"
        elif choice == '4':
            message = "查看狀態"
        elif choice == '5':
            message = "查看獎勵"
        elif choice == '6':
            message = input(f"{Colors.CYAN}💬 請輸入您的訊息: {Colors.END}").strip()
            if not message:
                continue
        else:
            # 直接使用輸入的內容作為消息
            message = choice

        # 顯示用戶輸入
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*60}{Colors.END}")
        print(f"{Colors.BOLD}👤 您: {message}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'─'*60}{Colors.END}")

        # 發送消息
        chat(message)

        # 等待用戶按 Enter 繼續
        input(f"\n{Colors.CYAN}按 Enter 繼續...{Colors.END}")
        clear_screen()
        print_header()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}👋 再見！{Colors.END}\n")
        sys.exit(0)
