"""
Presenter 層 - 業務邏輯控制器

在 MVP 架構中，Presenter 負責：
1. 接收來自 View 的用戶操作
2. 調用 Model 處理業務邏輯
3. 更新 View 顯示結果
4. 作為 Model 和 View 之間的橋樑
"""

from src.model import SummaryModel, AIService
from src.view import ISummaryView


class SummaryPresenter:
    """摘要 Presenter - 控制業務流程"""
    
    def __init__(self, view: ISummaryView, model: SummaryModel = None, ai_service: AIService = None):
        """
        初始化 Presenter
        
        Args:
            view: 視圖實例
            model: 資料模型實例（可選，預設創建新實例）
            ai_service: AI 服務實例（可選，預設創建新實例）
        """
        self._view = view
        self._model = model or SummaryModel()
        self._ai_service = ai_service or AIService()
    
    def generate_summary(self, text: str = None) -> bool:
        """
        生成文本摘要
        
        Args:
            text: 要摘要的文本，如果為 None 則從 View 獲取
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 如果沒有提供文本，從 View 獲取
            if text is None:
                text = self._view.get_input_text()
            
            # 驗證輸入
            if not text or not text.strip():
                self._view.display_error("請輸入有效的文本")
                return False
            
            # 調用 AI 服務生成摘要
            summary = self._ai_service.generate_summary(text)
            
            if not summary:
                self._view.display_error("無法生成摘要")
                return False
            
            # 保存到 Model
            data = self._model.add_summary(text, summary)
            
            # 更新 View
            self._view.display_summary(data)
            
            return True
            
        except Exception as e:
            self._view.display_error(f"生成摘要時發生錯誤: {str(e)}")
            return False
    
    def show_history(self) -> None:
        """顯示摘要歷史"""
        summaries = self._model.get_all_summaries()
        self._view.display_history(summaries)
    
    def clear_history(self) -> None:
        """清除摘要歷史"""
        self._model.clear_summaries()
        self._view.display_message("歷史記錄已清除")
    
    def get_summary_count(self) -> int:
        """獲取摘要數量"""
        return len(self._model.get_all_summaries())
