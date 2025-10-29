"""
視覺化 AI Agent 與用戶的互動流程
生成流程圖、序列圖和狀態轉換圖
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def create_sequence_diagram():
    """創建序列圖 - 展示用戶與Agent的對話流程"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 20)
    ax.axis('off')

    # 標題
    ax.text(5, 19, 'AI Agent 與用戶互動序列圖',
            ha='center', fontsize=16, fontweight='bold')

    # 三個參與者
    actors = [
        ('用戶 Alice', 2, '👤'),
        ('AI Agent', 5, '🤖'),
        ('系統/數據庫', 8, '💾')
    ]

    # 繪製參與者
    for name, x, emoji in actors:
        # 頂部框
        rect = FancyBboxPatch((x-0.8, 17.5), 1.6, 0.8,
                              boxstyle="round,pad=0.1",
                              edgecolor='black', facecolor='lightblue', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, 17.9, emoji + ' ' + name, ha='center', va='center', fontsize=10)

        # 生命線
        ax.plot([x, x], [17.5, 0.5], 'k--', linewidth=1, alpha=0.5)

    # 互動消息
    interactions = [
        # (from_x, to_x, y, message, style)
        (2, 5, 16.5, '1. 打開 App，首次登入', 'solid'),
        (5, 8, 16, '查詢用戶檔案', 'dashed'),
        (8, 5, 15.5, '返回: State_3 新手', 'dashed'),
        (5, 2, 15, '2. 歡迎！為你生成入門卡片', 'solid'),

        (2, 5, 14, '3. 完成了第一個任務！', 'solid'),
        (5, 8, 13.5, '更新卡片進度 (+10分)', 'dashed'),
        (8, 5, 13, '保存成功', 'dashed'),
        (5, 2, 12.5, '4. 太棒了！繼續加油', 'solid'),

        (2, 5, 11.5, '5. 完成更多任務', 'solid'),
        (5, 8, 11, '批量更新進度', 'dashed'),
        (5, 2, 10.5, '6. 進度60%，快完成了！', 'solid'),

        (2, 5, 9.5, '7. 完成最後的任務！', 'solid'),
        (5, 8, 9, '標記卡片完成 (+100分)', 'dashed'),
        (5, 8, 8.5, '檢測狀態轉換', 'dashed'),
        (8, 5, 8, '觸發: State_3→State_4', 'dashed'),
        (5, 2, 7.5, '8. 恭喜升級！+1100積分', 'solid'),

        (2, 5, 6.5, '9. 給我更有挑戰的卡片', 'solid'),
        (5, 8, 6, '分析用戶偏好', 'dashed'),
        (5, 8, 5.5, '調用 LLM 生成', 'dashed'),
        (8, 5, 5, '返回個性化卡片', 'dashed'),
        (5, 2, 4.5, '10. 這是你的專屬卡片', 'solid'),

        (8, 5, 3.5, '[次日] 提醒評估', 'dashed'),
        (5, 2, 3, '11. 早安！別忘了今天的任務', 'solid'),

        (5, 8, 2, '持續學習用戶偏好', 'dashed'),
        (8, 5, 1.5, '優化策略', 'dashed'),
    ]

    # 繪製消息箭頭
    for from_x, to_x, y, msg, style in interactions:
        arrow_style = '->' if style == 'solid' else '->'
        line_style = '-' if style == 'solid' else '--'
        color = 'blue' if from_x == 2 else ('green' if from_x == 5 else 'purple')

        arrow = FancyArrowPatch((from_x, y), (to_x, y),
                               arrowstyle=arrow_style,
                               color=color,
                               linestyle=line_style,
                               linewidth=1.5,
                               mutation_scale=15)
        ax.add_patch(arrow)

        # 消息文本
        text_x = (from_x + to_x) / 2
        text_y = y + 0.15
        ax.text(text_x, text_y, msg, ha='center', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig('interaction_sequence.png', dpi=300, bbox_inches='tight')
    print("✅ 序列圖已保存: interaction_sequence.png")
    plt.close()


def create_state_transition_diagram():
    """創建狀態轉換圖"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # 標題
    ax.text(6, 7.5, '用戶參與狀態轉換流程',
            ha='center', fontsize=16, fontweight='bold')

    # 狀態定義
    states = [
        ('State 1\n未註冊', 1.5, 4, 'lightgray'),
        ('State 2\n已註冊', 3.5, 4, 'lightgray'),
        ('State 3\n新手\nPre-Active', 5.5, 4, 'lightblue'),
        ('State 4\n活躍\nActive', 7.5, 4, 'lightgreen'),
        ('State 5\n深度參與\nEngaged', 10, 4, 'gold'),
    ]

    # 繪製狀態節點
    for label, x, y, color in states:
        circle = Circle((x, y), 0.6, color=color, ec='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')

    # 狀態轉換箭頭
    transitions = [
        (2.1, 4, 2.9, 4, '註冊', 0.3),
        (4.1, 4, 4.9, 4, '首次使用', 0.3),
        (6.1, 4, 6.9, 4, '完成首張\n卡片', 0.3),
        (8.1, 4, 9.4, 4, '持續參與\n多張卡片', 0.3),
    ]

    for x1, y1, x2, y2, label, offset in transitions:
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                               arrowstyle='->',
                               color='red',
                               linewidth=2.5,
                               mutation_scale=20)
        ax.add_patch(arrow)
        ax.text((x1+x2)/2, y1+offset, label, ha='center', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    # Alice 的旅程標記
    ax.text(5.5, 5.5, '👤 Alice\n起點', ha='center', fontsize=10, color='blue')

    # 繪製 Alice 的進度箭頭
    alice_progress = FancyArrowPatch((5.5, 5.2), (7.5, 5.2),
                                    arrowstyle='->',
                                    color='blue',
                                    linewidth=3,
                                    mutation_scale=20,
                                    linestyle='--')
    ax.add_patch(alice_progress)
    ax.text(6.5, 5.5, '✅ 已完成', ha='center', fontsize=9, color='blue',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.9))

    # 觸發條件說明
    ax.text(6, 1.5, '狀態轉換觸發條件:', ha='left', fontsize=11, fontweight='bold')
    trigger_text = """
    • State 2 → State 3: 完成註冊，首次進入 App
    • State 3 → State 4: 完成第一張 Bingo 卡片 (+1000分獎勵)
    • State 4 → State 5: 連續參與多張卡片，高完成率

    💡 Alice 在 Demo 中: State 3 → State 4
    """
    ax.text(6, 0.8, trigger_text, ha='left', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    plt.savefig('state_transition.png', dpi=300, bbox_inches='tight')
    print("✅ 狀態轉換圖已保存: state_transition.png")
    plt.close()


def create_timeline_diagram():
    """創建時間線圖 - 展示用戶旅程"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 6))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # 標題
    ax.text(8, 5.5, 'Alice 的用戶旅程時間線',
            ha='center', fontsize=16, fontweight='bold')

    # 時間線主線
    ax.plot([1, 15], [3, 3], 'k-', linewidth=3)

    # 關鍵事件
    events = [
        (1.5, '首次登入', '👤', 'lightblue', '檢測新用戶\nState_3'),
        (3, '收到卡片', '🎲', 'lightgreen', '生成簡單卡片\n3x3 維度'),
        (4.5, '首個任務', '✅', 'yellow', '完成第1個tile\n+10分'),
        (6.5, '持續參與', '🔥', 'orange', '完成5個tiles\n進度60%'),
        (9, '完成卡片', '🎉', 'gold', '卡片全部完成\n+100分'),
        (10.5, '狀態升級', '⬆️', 'lightcoral', 'State_3→State_4\n+1000分'),
        (12.5, '新挑戰', '🚀', 'lightgreen', '生成進階卡片\nLLM個性化'),
        (14.5, '智能提醒', '⏰', 'lightblue', '次日早晨\n個性化提醒'),
    ]

    # 繪製事件點
    for x, label, emoji, color, detail in events:
        # 事件點
        circle = Circle((x, 3), 0.25, color=color, ec='black', linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, 3, emoji, ha='center', va='center', fontsize=12, zorder=4)

        # 事件標籤
        y_label = 4.2 if events.index((x, label, emoji, color, detail)) % 2 == 0 else 1.8
        ax.plot([x, x], [3.25, y_label-0.3], 'k--', linewidth=1, alpha=0.5)
        ax.text(x, y_label, label, ha='center', fontweight='bold', fontsize=10)
        ax.text(x, y_label-0.5, detail, ha='center', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.6))

    # 時間標記
    time_labels = ['T0\n第1天', 'T1\n2小時後', 'T2\n第2天']
    time_positions = [1.5, 9, 14.5]
    for pos, time_label in zip(time_positions, time_labels):
        ax.text(pos, 2.3, time_label, ha='center', fontsize=9, style='italic')

    # 添加階段標記
    stages = [
        (2.25, '🌱 探索階段', 1, 4),
        (7.75, '🎯 參與階段', 4.5, 9.5),
        (13.5, '🚀 成長階段', 10, 15),
    ]
    for x, stage_name, x_start, x_end in stages:
        ax.plot([x_start, x_end], [2.7, 2.7], linewidth=6, alpha=0.3,
                color='green' if '成長' in stage_name else 'blue')
        ax.text(x, 2.5, stage_name, ha='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig('user_journey_timeline.png', dpi=300, bbox_inches='tight')
    print("✅ 時間線圖已保存: user_journey_timeline.png")
    plt.close()


def create_agent_decision_flow():
    """創建 Agent 決策流程圖"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 標題
    ax.text(7, 9.5, 'AI Agent 決策流程圖',
            ha='center', fontsize=16, fontweight='bold')

    # 流程節點
    def draw_box(x, y, w, h, text, color):
        rect = FancyBboxPatch((x-w/2, y-h/2), w, h,
                             boxstyle="round,pad=0.1",
                             edgecolor='black', facecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')

    def draw_diamond(x, y, w, h, text, color):
        points = np.array([[x, y+h/2], [x+w/2, y], [x, y-h/2], [x-w/2, y]])
        polygon = mpatches.Polygon(points, closed=True,
                                  edgecolor='black', facecolor=color, linewidth=2)
        ax.add_patch(polygon)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold')

    # 開始
    draw_box(7, 8.5, 1.5, 0.5, '開始\n用戶請求', 'lightgreen')

    # 加載用戶狀態
    arrow1 = FancyArrowPatch((7, 8.2), (7, 7.7), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow1)
    draw_box(7, 7.3, 2, 0.6, '1. 加載用戶檔案\n(State Loader)', 'lightblue')

    # 決策點1: 請求類型
    arrow2 = FancyArrowPatch((7, 7), (7, 6.3), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow2)
    draw_diamond(7, 5.8, 2, 0.8, '請求類型？', 'yellow')

    # 左分支: 生成卡片
    arrow_left = FancyArrowPatch((6.3, 5.8), (3, 5.8), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow_left)
    ax.text(4.5, 6, '生成卡片', fontsize=8)
    draw_box(3, 5, 2, 0.6, '2a. 卡片生成器\n(Card Generator)', 'lightcoral')

    arrow_left2 = FancyArrowPatch((3, 4.7), (3, 4.2), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow_left2)
    draw_diamond(3, 3.7, 1.8, 0.8, '有LLM？', 'yellow')

    # LLM 路徑
    arrow_llm = FancyArrowPatch((2.2, 3.7), (1, 3.7), arrowstyle='->', linewidth=1.5)
    ax.add_patch(arrow_llm)
    ax.text(1.5, 3.9, '是', fontsize=7)
    draw_box(1, 2.8, 1.5, 0.5, 'LLM生成\n個性化', 'lightgreen')

    # 規則路徑
    arrow_rule = FancyArrowPatch((3.9, 3.7), (5, 3.7), arrowstyle='->', linewidth=1.5)
    ax.add_patch(arrow_rule)
    ax.text(4.5, 3.9, '否', fontsize=7)
    draw_box(5, 2.8, 1.5, 0.5, '規則生成\n標準化', 'lightgray')

    # 右分支: 提醒評估
    arrow_right = FancyArrowPatch((7.7, 5.8), (11, 5.8), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow_right)
    ax.text(9.5, 6, '提醒評估', fontsize=8)
    draw_box(11, 5, 2, 0.6, '2b. 提醒節點\n(Reminder Node)', 'lightcoral')

    arrow_right2 = FancyArrowPatch((11, 4.7), (11, 4.2), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow_right2)
    draw_diamond(11, 3.7, 1.8, 0.8, '應該提醒？', 'yellow')

    # 發送提醒
    arrow_remind = FancyArrowPatch((10.2, 3.7), (9, 3.7), arrowstyle='->', linewidth=1.5)
    ax.add_patch(arrow_remind)
    ax.text(9.5, 3.9, '是', fontsize=7)
    draw_box(9, 2.8, 1.5, 0.5, '發送提醒', 'lightgreen')

    # 跳過提醒
    arrow_skip = FancyArrowPatch((11.8, 3.7), (13, 3.7), arrowstyle='->', linewidth=1.5)
    ax.add_patch(arrow_skip)
    ax.text(12.5, 3.9, '否', fontsize=7)
    draw_box(13, 2.8, 1.5, 0.5, '跳過', 'lightgray')

    # 匯總到反饋處理
    arrow_merge1 = FancyArrowPatch((3, 2.5), (7, 1.8), arrowstyle='->', linewidth=1.5)
    ax.add_patch(arrow_merge1)
    arrow_merge2 = FancyArrowPatch((11, 2.5), (7, 1.8), arrowstyle='->', linewidth=1.5)
    ax.add_patch(arrow_merge2)

    draw_box(7, 1.3, 2.5, 0.6, '3. 反饋處理器\n(Feedback Processor)', 'lightyellow')

    # 最後保存
    arrow_final = FancyArrowPatch((7, 1), (7, 0.5), arrowstyle='->', linewidth=2)
    ax.add_patch(arrow_final)
    draw_box(7, 0.3, 1.8, 0.4, '4. 保存到數據庫\n學習優化', 'lightgreen')

    # 添加說明
    ax.text(0.5, 9.5, '🔄 反饋循環', fontsize=10, fontweight='bold')
    feedback_arrow = FancyArrowPatch((1.5, 9.3), (1.5, 8.5), arrowstyle='->',
                                    linewidth=2, linestyle='--', color='green')
    ax.add_patch(feedback_arrow)
    feedback_arrow2 = FancyArrowPatch((1.5, 8.5), (5.5, 8.5), arrowstyle='->',
                                     linewidth=2, linestyle='--', color='green')
    ax.add_patch(feedback_arrow2)
    ax.text(3.5, 8.7, '持續學習', fontsize=8, color='green', style='italic')

    plt.tight_layout()
    plt.savefig('agent_decision_flow.png', dpi=300, bbox_inches='tight')
    print("✅ Agent 決策流程圖已保存: agent_decision_flow.png")
    plt.close()


def create_all_diagrams():
    """生成所有視覺化圖表"""
    print("\n" + "="*60)
    print("  開始生成 AI Agent 互動流程視覺化圖表")
    print("="*60 + "\n")

    print("📊 生成中...")

    create_sequence_diagram()
    create_state_transition_diagram()
    create_timeline_diagram()
    create_agent_decision_flow()

    print("\n" + "="*60)
    print("  ✅ 所有圖表生成完成！")
    print("="*60)
    print("\n生成的圖表:")
    print("  1. interaction_sequence.png - 互動序列圖")
    print("  2. state_transition.png - 狀態轉換圖")
    print("  3. user_journey_timeline.png - 用戶旅程時間線")
    print("  4. agent_decision_flow.png - Agent 決策流程")
    print("\n使用 'open *.png' 或圖片查看器打開查看\n")


if __name__ == "__main__":
    create_all_diagrams()
