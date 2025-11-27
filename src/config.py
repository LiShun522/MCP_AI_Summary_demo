"""
MCP AI Summary Demo - 設定管理模組
===================================
使用 pydantic 進行環境變數驗證與類型安全
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式設定類別
    
    所有敏感設定都從環境變數載入，確保不會硬編碼在程式碼中
    """
    
    # Ollama 設定
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API 基礎 URL"
    )
    ollama_model: str = Field(
        default="gemma3:4b",
        description="使用的 LLM 模型名稱"
    )
    
    # 資料庫設定
    database_path: str = Field(
        default="./data/demo.db",
        description="SQLite 資料庫路徑"
    )
    
    # API 設定
    api_base_url: str = Field(
        default="https://jsonplaceholder.typicode.com",
        description="外部 API 基礎 URL"
    )
    
    # 安全性設定
    enable_data_masking: bool = Field(
        default=True,
        description="是否啟用資料遮罩"
    )
    masked_fields: str = Field(
        default="email,phone,ssn,credit_card,password",
        description="需要遮罩的欄位名稱（逗號分隔）"
    )
    
    # 日誌設定
    log_level: str = Field(
        default="INFO",
        description="日誌等級"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    @property
    def masked_fields_list(self) -> list[str]:
        """將遮罩欄位字串轉換為列表"""
        return [f.strip().lower() for f in self.masked_fields.split(",")]
    
    @property
    def database_dir(self) -> Path:
        """取得資料庫目錄路徑"""
        return Path(self.database_path).parent


# 全域設定實例
settings = Settings()
