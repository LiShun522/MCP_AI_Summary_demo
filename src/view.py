"""
View 層 - 用戶介面

在 MVP 架構中，View 負責：
1. 顯示資料給用戶
2. 接收用戶輸入
3. 將用戶操作傳遞給 Presenter
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.model import SummaryData


class ISummaryView(ABC):
    """摘要視圖介面 - 定義視圖的契約"""
    
    @abstractmethod
    def display_summary(self, data: SummaryData) -> None:
        """顯示摘要結果"""
        pass
    
    @abstractmethod
    def display_error(self, message: str) -> None:
        """顯示錯誤訊息"""
        pass
    
    @abstractmethod
    def display_message(self, message: str) -> None:
        """顯示一般訊息"""
        pass
    
    @abstractmethod
    def get_input_text(self) -> str:
        """獲取用戶輸入的文本"""
        pass
    
    @abstractmethod
    def display_history(self, summaries: List[SummaryData]) -> None:
        """顯示歷史記錄"""
        pass


class ConsoleSummaryView(ISummaryView):
    """命令行摘要視圖實現"""
    
    def display_summary(self, data: SummaryData) -> None:
        """顯示摘要結果"""
        print("\n" + "=" * 50)
        print("📝 AI 摘要結果")
        print("=" * 50)
        print(f"\n原文:\n{data.original_text[:200]}{'...' if len(data.original_text) > 200 else ''}")
        print(f"\n摘要:\n{data.summary}")
        print(f"\n📊 統計:")
        print(f"   - 摘要字數: {data.word_count}")
        print(f"   - 壓縮比率: {data.compression_ratio:.2%}")
        print(f"   - 生成時間: {data.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50 + "\n")
    
    def display_error(self, message: str) -> None:
        """顯示錯誤訊息"""
        print(f"\n❌ 錯誤: {message}\n")
    
    def display_message(self, message: str) -> None:
        """顯示一般訊息"""
        print(f"\n✅ {message}\n")
    
    def get_input_text(self) -> str:
        """獲取用戶輸入的文本"""
        print("\n請輸入要摘要的文本 (輸入空行結束):")
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break
        return '\n'.join(lines)
    
    def display_history(self, summaries: List[SummaryData]) -> None:
        """顯示歷史記錄"""
        if not summaries:
            print("\n📭 沒有歷史記錄\n")
            return
        
        print("\n" + "=" * 50)
        print("📚 摘要歷史記錄")
        print("=" * 50)
        
        for i, data in enumerate(summaries, 1):
            print(f"\n[{i}] {data.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    摘要: {data.summary[:100]}{'...' if len(data.summary) > 100 else ''}")
            print(f"    壓縮比率: {data.compression_ratio:.2%}")
        
        print("\n" + "=" * 50 + "\n")
    
    def display_menu(self) -> None:
        """顯示主選單"""
        print("\n" + "=" * 50)
        print("🤖 MCP AI 摘要生成器 - MVP 範例")
        print("=" * 50)
        print("\n請選擇操作:")
        print("  1. 生成新摘要")
        print("  2. 查看歷史記錄")
        print("  3. 清除歷史")
        print("  4. 退出")
        print()
    
    def get_menu_choice(self) -> str:
        """獲取用戶選單選擇"""
        try:
            return input("請輸入選項 (1-4): ").strip()
        except EOFError:
            return "4"
