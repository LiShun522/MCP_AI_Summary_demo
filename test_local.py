"""
MCP AI Summary Demo - 本地測試腳本
==================================
不需要 MCP Client 即可測試所有功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加 src 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.data_source import data_source
from src.prompts import prompt_library
from src.ollama_client import ollama_client, summary_generator
from src.security import data_masker


async def test_database():
    """測試資料庫功能"""
    print("\n" + "=" * 50)
    print("📊 測試資料庫功能")
    print("=" * 50)
    
    # 初始化資料庫
    await data_source.init_database()
    print("✅ 資料庫初始化成功")
    
    # 查詢員工資料
    employees = await data_source.query_database("employees")
    print(f"\n📋 員工資料（已遮罩敏感欄位）:")
    print(json.dumps(employees, ensure_ascii=False, indent=2))
    
    # 查詢專案資料
    projects = await data_source.query_database("projects")
    print(f"\n📋 專案資料:")
    print(json.dumps(projects, ensure_ascii=False, indent=2))
    
    return employees, projects


async def test_api():
    """測試 API 功能"""
    print("\n" + "=" * 50)
    print("🌐 測試 API 功能")
    print("=" * 50)
    
    try:
        # 取得使用者資料
        users = await data_source.fetch_from_api("users", {"_limit": 3})
        print(f"\n📋 API 使用者資料（已遮罩）:")
        if isinstance(users, list):
            print(json.dumps(users[:3], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(users, ensure_ascii=False, indent=2))
        return users
    except Exception as e:
        print(f"❌ API 測試失敗: {e}")
        return None


async def test_prompts(employees, projects):
    """測試 Prompt 模板功能"""
    print("\n" + "=" * 50)
    print("📝 測試 Prompt 模板功能")
    print("=" * 50)
    
    # 列出所有模板
    templates = prompt_library.list_templates()
    print("\n📋 可用的 Prompt 模板:")
    for t in templates:
        print(f"  - {t['name']}: {t['description']}")
        print(f"    變數: {', '.join(t['variables'])}")
    
    # 測試員工分析模板
    print("\n📝 員工分析 Prompt 範例:")
    prompt = prompt_library.render(
        "employee_analysis",
        department="研發部",
        employees=[e for e in employees if e.get("department") == "研發部"]
    )
    print(prompt[:500] + "...")
    
    return prompt


async def test_ollama():
    """測試 Ollama 連接"""
    print("\n" + "=" * 50)
    print("🤖 測試 Ollama 連接")
    print("=" * 50)
    
    # 檢查健康狀態
    is_healthy = await ollama_client.check_health()
    print(f"\n🔗 Ollama 服務狀態: {'✅ 正常' if is_healthy else '❌ 無法連接'}")
    print(f"   URL: {settings.ollama_base_url}")
    print(f"   模型: {settings.ollama_model}")
    
    if is_healthy:
        models = await ollama_client.list_models()
        print(f"\n📋 可用模型:")
        for model in models:
            mark = "✅" if model == settings.ollama_model else "  "
            print(f"   {mark} {model}")
        
        if settings.ollama_model not in models:
            print(f"\n⚠️ 設定的模型 '{settings.ollama_model}' 尚未下載")
            print(f"   請執行: ollama pull {settings.ollama_model}")
            return False
        return True
    else:
        print("\n⚠️ 請確認 Ollama 已啟動")
        print("   啟動指令: ollama serve")
        return False


async def test_summary_generation(employees):
    """測試摘要生成"""
    print("\n" + "=" * 50)
    print("✨ 測試 AI 摘要生成")
    print("=" * 50)
    
    # 準備 prompt
    prompt = prompt_library.render(
        "data_summary",
        data=employees[:3]  # 只使用前 3 筆減少 token
    )
    
    print("\n📝 生成中...")
    try:
        summary = await summary_generator.generate_summary(prompt)
        print("\n📄 生成的摘要:")
        print("-" * 40)
        print(summary)
        print("-" * 40)
        return True
    except Exception as e:
        print(f"\n❌ 摘要生成失敗: {e}")
        return False


async def test_security():
    """測試資料遮罩功能"""
    print("\n" + "=" * 50)
    print("🔒 測試資料遮罩功能")
    print("=" * 50)
    
    test_data = {
        "name": "張小明",
        "email": "test@example.com",
        "phone": "0912-345-678",
        "credit_card": "1234-5678-9012-3456",
        "ssn": "123-45-6789",
        "department": "研發部"
    }
    
    print("\n📋 原始資料:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    masked = data_masker.mask_dict(test_data)
    print("\n📋 遮罩後資料:")
    print(json.dumps(masked, ensure_ascii=False, indent=2))


async def main():
    """主測試程式"""
    print("\n" + "=" * 60)
    print("🚀 MCP AI Summary Demo - 功能測試")
    print("=" * 60)
    
    # 測試資料遮罩
    await test_security()
    
    # 測試資料庫
    employees, projects = await test_database()
    
    # 測試 API
    await test_api()
    
    # 測試 Prompt 模板
    await test_prompts(employees, projects)
    
    # 測試 Ollama
    ollama_ok = await test_ollama()
    
    # 如果 Ollama 正常，測試摘要生成
    if ollama_ok:
        await test_summary_generation(employees)
    else:
        print("\n⏭️ 跳過摘要生成測試（Ollama 未就緒）")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
