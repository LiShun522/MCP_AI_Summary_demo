"""
MCP AI Summary Demo - 資料遮罩模組
===================================
提供敏感資料遮罩功能，保護個資安全
適用於企業內部部署情境
"""

import re
from typing import Any
from .config import settings


class DataMasker:
    """資料遮罩處理器
    
    負責將敏感欄位的值進行遮罩處理，
    確保在 AI 處理過程中不會洩漏個人資訊
    """
    
    def __init__(self, masked_fields: list[str] | None = None):
        """初始化遮罩處理器
        
        Args:
            masked_fields: 需要遮罩的欄位名稱列表
        """
        self.masked_fields = masked_fields or settings.masked_fields_list
        self.enabled = settings.enable_data_masking
        
        # 預定義的正則表達式模式
        self.patterns = {
            "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", self._mask_email),
            "phone": (r"\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4}", self._mask_phone),
            "credit_card": (r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", self._mask_credit_card),
            "ssn": (r"\d{3}[-\s]?\d{2}[-\s]?\d{4}", self._mask_ssn),
        }
    
    def _mask_email(self, value: str) -> str:
        """遮罩電子郵件地址"""
        if "@" in value:
            local, domain = value.rsplit("@", 1)
            if len(local) > 2:
                masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
            else:
                masked_local = "*" * len(local)
            return f"{masked_local}@{domain}"
        return value
    
    def _mask_phone(self, value: str) -> str:
        """遮罩電話號碼"""
        digits = re.sub(r"[-\s]", "", value)
        if len(digits) >= 4:
            return digits[:2] + "*" * (len(digits) - 4) + digits[-2:]
        return "*" * len(digits)
    
    def _mask_credit_card(self, value: str) -> str:
        """遮罩信用卡號"""
        digits = re.sub(r"[-\s]", "", value)
        if len(digits) >= 4:
            return "*" * (len(digits) - 4) + digits[-4:]
        return "*" * len(digits)
    
    def _mask_ssn(self, value: str) -> str:
        """遮罩社會安全號碼"""
        return "***-**-" + re.sub(r"[-\s]", "", value)[-4:]
    
    def _mask_generic(self, value: str) -> str:
        """通用遮罩函式"""
        if len(value) <= 2:
            return "*" * len(value)
        return value[0] + "*" * (len(value) - 2) + value[-1]
    
    def mask_value(self, field_name: str, value: Any) -> Any:
        """根據欄位名稱遮罩值
        
        Args:
            field_name: 欄位名稱
            value: 原始值
            
        Returns:
            遮罩後的值（如果需要遮罩）或原始值
        """
        if not self.enabled or value is None:
            return value
        
        field_lower = field_name.lower()
        
        # 檢查是否需要遮罩
        should_mask = any(
            masked in field_lower 
            for masked in self.masked_fields
        )
        
        if not should_mask:
            return value
        
        # 轉換為字串處理
        str_value = str(value)
        
        # 嘗試使用特定模式遮罩
        for pattern_name, (pattern, mask_func) in self.patterns.items():
            if pattern_name in field_lower:
                if re.match(pattern, str_value):
                    return mask_func(str_value)
        
        # 使用通用遮罩
        return self._mask_generic(str_value)
    
    def mask_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """遮罩字典中的敏感欄位
        
        Args:
            data: 原始字典資料
            
        Returns:
            遮罩後的字典
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.mask_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.mask_dict(item) if isinstance(item, dict) else self.mask_value(key, item)
                    for item in value
                ]
            else:
                result[key] = self.mask_value(key, value)
        return result
    
    def mask_list(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """遮罩列表中的所有字典資料
        
        Args:
            data: 原始列表資料
            
        Returns:
            遮罩後的列表
        """
        return [self.mask_dict(item) for item in data]


# 全域遮罩器實例
data_masker = DataMasker()
