"""
MCP AI Summary Demo - 主要 MCP Server
======================================
實作 MCP 協議，提供 Tools、Resources 和 Prompts
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import settings
from .data_source import data_source
from .prompts import prompt_library
from .ollama_client import ollama_client, summary_generator

# 設定日誌
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==========================================
# MCP Server 初始化
# ==========================================

# 建立 MCP Server 實例
# FastMCP 會自動從函式的 docstring 生成工具描述
mcp = FastMCP("ai-summary-server")


# ==========================================
# MCP Resources - 提供資料存取
# ==========================================

@mcp.resource("data://employees")
async def get_employees_resource() -> str:
    """
    員工資料資源
    
    提供資料庫中所有員工的資訊（敏感欄位已遮罩）
    """
    employees = await data_source.query_database("employees")
    return json.dumps(employees, ensure_ascii=False, indent=2)


@mcp.resource("data://projects")
async def get_projects_resource() -> str:
    """
    專案資料資源
    
    提供所有專案的資訊
    """
    projects = await data_source.query_database("projects")
    return json.dumps(projects, ensure_ascii=False, indent=2)


@mcp.resource("schema://employees")
async def get_employees_schema() -> str:
    """
    員工資料表結構
    
    描述 employees 資料表的欄位定義
    """
    schema = await data_source.get_table_schema("employees")
    return json.dumps(schema, ensure_ascii=False, indent=2)


@mcp.resource("schema://projects")
async def get_projects_schema() -> str:
    """
    專案資料表結構
    
    描述 projects 資料表的欄位定義
    """
    schema = await data_source.get_table_schema("projects")
    return json.dumps(schema, ensure_ascii=False, indent=2)


@mcp.resource("templates://list")
async def get_prompt_templates() -> str:
    """
    Prompt 模板列表
    
    列出所有可用的 prompt 模板及其描述
    """
    templates = prompt_library.list_templates()
    return json.dumps(templates, ensure_ascii=False, indent=2)


# ==========================================
# MCP Tools - 提供可執行的功能
# ==========================================

@mcp.tool()
async def query_employees(
    department: str | None = None,
    limit: int = 50
) -> str:
    """查詢員工資料
    
    從資料庫查詢員工資訊，可依部門篩選。
    敏感資料（email、電話等）會自動遮罩。
    
    Args:
        department: 部門名稱（可選），例如 "研發部"、"人資部"
        limit: 最大回傳筆數，預設 50
    """
    conditions = {"department": department} if department else None
    employees = await data_source.query_database("employees", conditions, limit)
    return json.dumps(employees, ensure_ascii=False, indent=2)


@mcp.tool()
async def query_projects(
    status: str | None = None,
    limit: int = 50
) -> str:
    """查詢專案資料
    
    從資料庫查詢專案資訊，可依狀態篩選。
    
    Args:
        status: 專案狀態（可選），例如 "進行中"、"已完成"、"規劃中"
        limit: 最大回傳筆數
    """
    conditions = {"status": status} if status else None
    projects = await data_source.query_database("projects", conditions, limit)
    return json.dumps(projects, ensure_ascii=False, indent=2)


@mcp.tool()
async def fetch_api_data(
    endpoint: str,
    limit: int | None = None
) -> str:
    """從外部 API 取得資料
    
    從 JSONPlaceholder API（或設定的其他 API）取得資料。
    可用的端點: users, posts, comments, todos, albums, photos
    
    Args:
        endpoint: API 端點，例如 "users", "posts/1", "users/1/posts"
        limit: 限制回傳筆數（僅適用於列表資料）
    """
    data = await data_source.fetch_from_api(endpoint)
    
    # 如果是列表且有限制
    if isinstance(data, list) and limit:
        data = data[:limit]
    
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def generate_summary(
    template_name: str,
    data: str,
    extra_vars: str | None = None
) -> str:
    """使用模板生成 AI 摘要
    
    選擇預定義的 prompt 模板，帶入資料後透過 Ollama 生成摘要。
    
    可用模板:
    - data_summary: 通用資料摘要
    - employee_analysis: 員工資料分析
    - project_status: 專案狀態報告
    - api_data_summary: API 資料摘要
    - qa_with_context: 基於資料回答問題
    - custom_summary: 自訂指令摘要
    
    Args:
        template_name: 模板名稱
        data: JSON 格式的資料字串
        extra_vars: 額外變數的 JSON 字串（依模板需求提供）
    """
    try:
        # 解析資料
        parsed_data = json.loads(data)
        
        # 準備變數
        variables = {"data": parsed_data}
        
        # 解析額外變數
        if extra_vars:
            extra = json.loads(extra_vars)
            variables.update(extra)
        
        # 針對特定模板添加預設變數
        if template_name == "project_status":
            variables.setdefault("current_date", datetime.now().strftime("%Y-%m-%d"))
            variables.setdefault("projects", parsed_data)
        elif template_name == "employee_analysis":
            variables.setdefault("employees", parsed_data)
            variables.setdefault("department", "全公司")
        
        # 渲染 prompt
        prompt = prompt_library.render(template_name, **variables)
        
        # 生成摘要
        summary = await summary_generator.generate_summary(prompt)
        
        return summary
        
    except json.JSONDecodeError as e:
        return f"錯誤：資料格式不正確，請提供有效的 JSON 字串。詳細：{e}"
    except ValueError as e:
        return f"錯誤：{e}"
    except Exception as e:
        logger.error(f"生成摘要時發生錯誤: {e}")
        return f"錯誤：生成摘要失敗，請確認 Ollama 服務是否正常運作。詳細：{e}"


@mcp.tool()
async def check_ollama_status() -> str:
    """檢查 Ollama 服務狀態
    
    檢查本地 Ollama 服務是否正常運作，並列出可用的模型。
    """
    is_healthy = await ollama_client.check_health()
    
    if not is_healthy:
        return json.dumps({
            "status": "error",
            "message": f"無法連接到 Ollama 服務（{settings.ollama_base_url}）",
            "suggestion": "請確認 Ollama 已啟動，可執行 'ollama serve' 啟動服務"
        }, ensure_ascii=False, indent=2)
    
    models = await ollama_client.list_models()
    current_model = settings.ollama_model
    model_available = current_model in models
    
    return json.dumps({
        "status": "ok",
        "base_url": settings.ollama_base_url,
        "configured_model": current_model,
        "model_available": model_available,
        "available_models": models,
        "suggestion": None if model_available else f"請執行 'ollama pull {current_model}' 下載模型"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_prompt_templates() -> str:
    """列出所有可用的 Prompt 模板
    
    顯示所有預定義的 prompt 模板、描述及所需變數。
    """
    templates = prompt_library.list_templates()
    return json.dumps(templates, ensure_ascii=False, indent=2)


@mcp.tool()
async def answer_question(
    question: str,
    data_source_type: str = "employees",
    filters: str | None = None
) -> str:
    """基於資料回答問題
    
    查詢指定資料來源，並使用 AI 回答使用者的問題。
    
    Args:
        question: 使用者的問題
        data_source_type: 資料來源類型 ("employees" 或 "projects")
        filters: 過濾條件的 JSON 字串（可選）
    """
    try:
        # 取得資料
        conditions = json.loads(filters) if filters else None
        
        if data_source_type == "employees":
            data = await data_source.query_database("employees", conditions)
        elif data_source_type == "projects":
            data = await data_source.query_database("projects", conditions)
        else:
            return f"錯誤：不支援的資料來源類型 '{data_source_type}'"
        
        # 使用問答模板
        prompt = prompt_library.render(
            "qa_with_context",
            context_data=data,
            question=question
        )
        
        # 生成回答
        answer = await summary_generator.generate_summary(prompt)
        
        return answer
        
    except Exception as e:
        logger.error(f"回答問題時發生錯誤: {e}")
        return f"錯誤：無法回答問題。{e}"


# ==========================================
# MCP Prompts - 提供預定義的 Prompt
# ==========================================

@mcp.prompt()
async def summarize_employees(department: str | None = None) -> str:
    """生成員工資料摘要的 Prompt
    
    Args:
        department: 部門名稱（可選）
    """
    conditions = {"department": department} if department else None
    employees = await data_source.query_database("employees", conditions)
    
    return prompt_library.render(
        "employee_analysis",
        department=department or "全公司",
        employees=employees
    )


@mcp.prompt()
async def summarize_projects(status: str | None = None) -> str:
    """生成專案狀態報告的 Prompt
    
    Args:
        status: 專案狀態（可選）
    """
    conditions = {"status": status} if status else None
    projects = await data_source.query_database("projects", conditions)
    
    return prompt_library.render(
        "project_status",
        projects=projects,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )


# ==========================================
# Server 啟動
# ==========================================

async def init_server():
    """初始化伺服器"""
    await data_source.init_database()
    logger.info("MCP AI Summary Server 初始化完成")


def main():
    """主程式進入點"""
    # 執行初始化
    asyncio.run(init_server())
    
    # 啟動 MCP Server
    # 使用 stdio transport 與 MCP 客戶端通訊
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
