"""
MCP AI Summary Demo - Ollama 整合模組
=====================================
提供與本地 Ollama 服務的整合功能
"""

import logging
import httpx
from typing import AsyncGenerator

from .config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama API 客戶端
    
    用於與本地執行的 Ollama 服務通訊，
    支援文字生成和串流回應
    """
    
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None
    ):
        """初始化 Ollama 客戶端
        
        Args:
            base_url: Ollama API 基礎 URL
            model: 使用的模型名稱
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
    
    async def check_health(self) -> bool:
        """檢查 Ollama 服務是否可用
        
        Returns:
            服務是否正常運作
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama 健康檢查失敗: {e}")
            return False
    
    async def list_models(self) -> list[str]:
        """列出可用的模型
        
        Returns:
            模型名稱列表
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"取得模型列表失敗: {e}")
            return []
    
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """生成文字回應
        
        Args:
            prompt: 使用者提示
            system: 系統提示（可選）
            temperature: 生成溫度（0-1，越高越隨機）
            max_tokens: 最大生成 token 數
            
        Returns:
            生成的文字回應
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120.0  # LLM 生成可能需要較長時間
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.TimeoutException:
            logger.error("Ollama 請求逾時")
            raise RuntimeError("AI 生成請求逾時，請稍後再試")
        except httpx.HTTPError as e:
            logger.error(f"Ollama API 錯誤: {e}")
            raise RuntimeError(f"AI 服務錯誤: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        """串流生成文字回應
        
        Args:
            prompt: 使用者提示
            system: 系統提示（可選）
            temperature: 生成溫度
            max_tokens: 最大生成 token 數
            
        Yields:
            生成的文字片段
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120.0
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
        except Exception as e:
            logger.error(f"串流生成錯誤: {e}")
            raise


class SummaryGenerator:
    """摘要生成器
    
    結合 prompt 模板和 Ollama 生成 AI 摘要
    """
    
    def __init__(self, ollama_client: OllamaClient | None = None):
        """初始化摘要生成器
        
        Args:
            ollama_client: Ollama 客戶端實例
        """
        self.client = ollama_client or OllamaClient()
        
        # 系統提示，定義 AI 的角色和行為
        self.system_prompt = """你是一個專業的商業分析助理。你的任務是：
1. 根據提供的資料生成清晰、結構化的中文摘要
2. 保持專業客觀的語氣
3. 突出重要的數據和洞察
4. 對於被遮罩的敏感資料（顯示為 * 符號），不要嘗試推測或恢復
5. 如果資料不足，誠實說明而不是猜測
6. 使用繁體中文回應"""
    
    async def generate_summary(
        self,
        prompt: str,
        temperature: float = 0.5
    ) -> str:
        """生成摘要
        
        Args:
            prompt: 完整的 prompt（已包含資料）
            temperature: 生成溫度（摘要任務建議使用較低溫度）
            
        Returns:
            生成的摘要文字
        """
        return await self.client.generate(
            prompt=prompt,
            system=self.system_prompt,
            temperature=temperature
        )
    
    async def generate_summary_stream(
        self,
        prompt: str,
        temperature: float = 0.5
    ) -> AsyncGenerator[str, None]:
        """串流生成摘要
        
        Args:
            prompt: 完整的 prompt
            temperature: 生成溫度
            
        Yields:
            摘要文字片段
        """
        async for chunk in self.client.generate_stream(
            prompt=prompt,
            system=self.system_prompt,
            temperature=temperature
        ):
            yield chunk


# 全域實例
ollama_client = OllamaClient()
summary_generator = SummaryGenerator(ollama_client)
