"""
MVP 架構測試

測試 Model、View、Presenter 各層的功能
"""

import unittest
from unittest.mock import MagicMock
from src.model import SummaryModel, AIService, SummaryData
from src.view import ISummaryView
from src.presenter import SummaryPresenter


class TestSummaryModel(unittest.TestCase):
    """測試 Model 層"""
    
    def setUp(self):
        self.model = SummaryModel()
    
    def test_add_summary(self):
        """測試添加摘要"""
        data = self.model.add_summary("這是原文", "這是摘要")
        self.assertEqual(data.original_text, "這是原文")
        self.assertEqual(data.summary, "這是摘要")
        self.assertIsNotNone(data.created_at)
    
    def test_get_all_summaries(self):
        """測試獲取所有摘要"""
        self.model.add_summary("原文1", "摘要1")
        self.model.add_summary("原文2", "摘要2")
        summaries = self.model.get_all_summaries()
        self.assertEqual(len(summaries), 2)
    
    def test_get_latest_summary(self):
        """測試獲取最新摘要"""
        self.model.add_summary("原文1", "摘要1")
        self.model.add_summary("原文2", "摘要2")
        latest = self.model.get_latest_summary()
        self.assertEqual(latest.original_text, "原文2")
    
    def test_get_latest_summary_empty(self):
        """測試空列表時獲取最新摘要"""
        latest = self.model.get_latest_summary()
        self.assertIsNone(latest)
    
    def test_clear_summaries(self):
        """測試清除摘要"""
        self.model.add_summary("原文", "摘要")
        self.model.clear_summaries()
        self.assertEqual(len(self.model.get_all_summaries()), 0)


class TestAIService(unittest.TestCase):
    """測試 AI 服務"""
    
    def test_generate_summary_empty(self):
        """測試空文本"""
        summary = AIService.generate_summary("")
        self.assertEqual(summary, "")
    
    def test_generate_summary_short(self):
        """測試短文本"""
        text = "這是一個短文本。"
        summary = AIService.generate_summary(text)
        self.assertIsNotNone(summary)
    
    def test_generate_summary_long(self):
        """測試長文本"""
        text = "第一句話。第二句話。第三句話。第四句話。第五句話。"
        summary = AIService.generate_summary(text)
        self.assertIsNotNone(summary)
        # 摘要應該比原文短
        self.assertLessEqual(len(summary), len(text))


class TestSummaryPresenter(unittest.TestCase):
    """測試 Presenter 層"""
    
    def setUp(self):
        # 創建 Mock View
        self.mock_view = MagicMock(spec=ISummaryView)
        self.presenter = SummaryPresenter(self.mock_view)
    
    def test_generate_summary_success(self):
        """測試成功生成摘要"""
        result = self.presenter.generate_summary("這是一個測試文本")
        self.assertTrue(result)
        self.mock_view.display_summary.assert_called_once()
    
    def test_generate_summary_empty(self):
        """測試空文本"""
        result = self.presenter.generate_summary("")
        self.assertFalse(result)
        self.mock_view.display_error.assert_called()
    
    def test_show_history(self):
        """測試顯示歷史"""
        self.presenter.show_history()
        self.mock_view.display_history.assert_called_once()
    
    def test_clear_history(self):
        """測試清除歷史"""
        self.presenter.generate_summary("測試文本")
        self.presenter.clear_history()
        self.assertEqual(self.presenter.get_summary_count(), 0)
        self.mock_view.display_message.assert_called()
    
    def test_get_summary_count(self):
        """測試獲取摘要數量"""
        self.assertEqual(self.presenter.get_summary_count(), 0)
        self.presenter.generate_summary("測試1")
        self.assertEqual(self.presenter.get_summary_count(), 1)
        self.presenter.generate_summary("測試2")
        self.assertEqual(self.presenter.get_summary_count(), 2)


if __name__ == '__main__':
    unittest.main()
