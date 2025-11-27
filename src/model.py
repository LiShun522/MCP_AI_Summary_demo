"""
Model 層 - 資料模型和業務邏輯

在 MVP 架構中，Model 負責：
1. 資料的存儲和管理
2. 業務邏輯的實現
3. 資料驗證
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class SummaryData:
    """AI 摘要資料模型"""
    original_text: str
    summary: str
    created_at: datetime
    word_count: int
    compression_ratio: float


class SummaryModel:
    """摘要資料管理模型"""
    
    def __init__(self):
        self._summaries: List[SummaryData] = []
    
    def add_summary(self, original_text: str, summary: str) -> SummaryData:
        """添加新的摘要記錄"""
        original_words = len(original_text.split())
        summary_words = len(summary.split())
        
        compression_ratio = 1.0
        if original_words > 0:
            compression_ratio = summary_words / original_words
        
        data = SummaryData(
            original_text=original_text,
            summary=summary,
            created_at=datetime.now(),
            word_count=summary_words,
            compression_ratio=compression_ratio
        )
        self._summaries.append(data)
        return data
    
    def get_all_summaries(self) -> List[SummaryData]:
        """獲取所有摘要記錄"""
        return self._summaries.copy()
    
    def get_latest_summary(self) -> Optional[SummaryData]:
        """獲取最新的摘要"""
        if self._summaries:
            return self._summaries[-1]
        return None
    
    def clear_summaries(self) -> None:
        """清除所有摘要記錄"""
        self._summaries.clear()


class AIService:
    """模擬 AI 服務 - 生成文本摘要"""
    
    @staticmethod
    def generate_summary(text: str) -> str:
        """
        生成文本摘要
        
        這是一個簡化的摘要生成算法，用於演示目的。
        在實際應用中，這裡會調用真正的 AI API（如 OpenAI、Claude 等）
        """
        if not text or not text.strip():
            return ""
        
        sentences = text.replace('。', '.').replace('！', '.').replace('？', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return text.strip()
        
        # 簡單策略：取前兩句和最後一句作為摘要
        key_sentences = sentences[:2]
        if len(sentences) > 2:
            key_sentences.append(sentences[-1])
        
        summary = '. '.join(key_sentences)
        if not summary.endswith('.'):
            summary += '.'
        
        return summary
