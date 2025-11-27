"""
MCP AI Summary Demo - 資料來源模組
===================================
提供從資料庫和 API 取得 JSON 資料的功能
"""

import json
import logging
import aiosqlite
import httpx
from pathlib import Path
from typing import Any

from .config import settings
from .security import data_masker

logger = logging.getLogger(__name__)


class DataSourceManager:
    """資料來源管理器
    
    統一管理從不同來源（資料庫、API）取得資料的邏輯
    """
    
    def __init__(self):
        self.db_path = Path(settings.database_path)
        self.api_base_url = settings.api_base_url
    
    async def init_database(self) -> None:
        """初始化資料庫並建立範例資料表"""
        # 確保資料目錄存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # 建立員工資料表（範例）
            await db.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    department TEXT,
                    position TEXT,
                    salary REAL,
                    hire_date TEXT,
                    phone TEXT
                )
            """)
            
            # 建立專案資料表（範例）
            await db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    budget REAL,
                    manager_id INTEGER,
                    FOREIGN KEY (manager_id) REFERENCES employees(id)
                )
            """)
            
            # 檢查是否需要插入範例資料
            cursor = await db.execute("SELECT COUNT(*) FROM employees")
            count = (await cursor.fetchone())[0]
            
            if count == 0:
                await self._insert_sample_data(db)
            
            await db.commit()
            logger.info(f"資料庫初始化完成: {self.db_path}")
    
    async def _insert_sample_data(self, db: aiosqlite.Connection) -> None:
        """插入範例資料"""
        employees = [
            ("張小明", "zhang@company.com", "研發部", "資深工程師", 85000, "2020-03-15", "0912-345-678"),
            ("李美華", "li@company.com", "人資部", "經理", 95000, "2018-07-01", "0923-456-789"),
            ("王大偉", "wang@company.com", "業務部", "業務代表", 65000, "2022-01-10", "0934-567-890"),
            ("陳雅婷", "chen@company.com", "財務部", "會計師", 75000, "2019-11-20", "0945-678-901"),
            ("林志豪", "lin@company.com", "研發部", "技術主管", 120000, "2017-05-08", "0956-789-012"),
        ]
        
        await db.executemany(
            "INSERT INTO employees (name, email, department, position, salary, hire_date, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
            employees
        )
        
        projects = [
            ("智慧倉儲系統", "建立自動化倉儲管理平台", "進行中", "2024-01-15", "2024-12-31", 2000000, 5),
            ("客戶關係管理升級", "升級現有CRM系統至雲端版本", "已完成", "2023-06-01", "2024-03-30", 800000, 2),
            ("行動應用程式開發", "開發企業內部行動辦公App", "規劃中", "2025-01-01", "2025-06-30", 1500000, 1),
        ]
        
        await db.executemany(
            "INSERT INTO projects (name, description, status, start_date, end_date, budget, manager_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            projects
        )
        
        logger.info("範例資料插入完成")
    
    async def query_database(
        self, 
        table: str, 
        conditions: dict[str, Any] | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """從資料庫查詢資料
        
        Args:
            table: 資料表名稱
            conditions: 查詢條件 (欄位名稱: 值)
            limit: 最大回傳筆數
            
        Returns:
            查詢結果列表（已遮罩敏感資料）
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # 建構查詢語句
            query = f"SELECT * FROM {table}"
            params = []
            
            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += f" LIMIT {limit}"
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            # 轉換為字典列表
            results = [dict(row) for row in rows]
            
            # 套用資料遮罩
            return data_masker.mask_list(results)
    
    async def fetch_from_api(
        self, 
        endpoint: str, 
        params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """從外部 API 取得資料
        
        Args:
            endpoint: API 端點路徑
            params: 查詢參數
            
        Returns:
            API 回應資料（已遮罩敏感資料）
        """
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                # 套用資料遮罩
                if isinstance(data, list):
                    return data_masker.mask_list(data)
                elif isinstance(data, dict):
                    return data_masker.mask_dict(data)
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"API 請求失敗: {e}")
                raise
    
    async def get_table_schema(self, table: str) -> list[dict[str, str]]:
        """取得資料表結構
        
        Args:
            table: 資料表名稱
            
        Returns:
            欄位資訊列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            columns = await cursor.fetchall()
            
            return [
                {
                    "name": col[1],
                    "type": col[2],
                    "nullable": not col[3],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]


# 全域資料來源管理器
data_source = DataSourceManager()
