#!/usr/bin/env python3
"""
MCP AI 摘要生成器 - MVP 架構範例

這是一個學習 MVP (Model-View-Presenter) 架構的範例項目。
透過簡單的 AI 摘要生成功能，展示 MVP 架構的基本概念。

使用方法:
    python main.py

MVP 架構說明:
    - Model (model.py): 資料模型和業務邏輯
    - View (view.py): 用戶介面
    - Presenter (presenter.py): 控制器，連接 Model 和 View
"""

from src.view import ConsoleSummaryView
from src.presenter import SummaryPresenter


def main():
    """主程式入口"""
    # 創建 View
    view = ConsoleSummaryView()
    
    # 創建 Presenter（自動創建 Model）
    presenter = SummaryPresenter(view)
    
    print("\n🚀 歡迎使用 MCP AI 摘要生成器！")
    print("這是一個 MVP 架構的學習範例。\n")
    
    while True:
        view.display_menu()
        choice = view.get_menu_choice()
        
        if choice == "1":
            presenter.generate_summary()
        elif choice == "2":
            presenter.show_history()
        elif choice == "3":
            presenter.clear_history()
        elif choice == "4":
            print("\n👋 感謝使用，再見！\n")
            break
        else:
            view.display_error("無效的選項，請重新選擇")


if __name__ == "__main__":
    main()
