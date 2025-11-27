"""
MCP AI Summary Demo - Prompt 模板系統
=====================================
提供結構化的 prompt 模板，支援佔位符替換功能
"""

import re
import json
from typing import Any
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """Prompt 模板類別
    
    支援使用 {{variable}} 語法的佔位符
    """
    name: str
    description: str
    template: str
    variables: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """自動解析模板中的變數"""
        if not self.variables:
            # 使用正則表達式找出所有 {{variable}} 格式的佔位符
            pattern = r"\{\{(\w+)\}\}"
            self.variables = list(set(re.findall(pattern, self.template)))
    
    def render(self, **kwargs) -> str:
        """使用提供的變數值渲染模板
        
        Args:
            **kwargs: 變數名稱與值的對應
            
        Returns:
            渲染後的 prompt 字串
        """
        result = self.template
        for var_name, value in kwargs.items():
            # 如果值是字典或列表，轉換為格式化的 JSON 字串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def validate(self, **kwargs) -> tuple[bool, list[str]]:
        """驗證是否提供了所有必要的變數
        
        Args:
            **kwargs: 提供的變數
            
        Returns:
            (是否驗證通過, 缺少的變數列表)
        """
        missing = [var for var in self.variables if var not in kwargs]
        return len(missing) == 0, missing


class PromptLibrary:
    """Prompt 模板函式庫
    
    預定義的 prompt 模板集合，針對不同的摘要任務
    """
    
    def __init__(self):
        self.templates: dict[str, PromptTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self) -> None:
        """註冊預設的 prompt 模板"""
        
        # 資料摘要模板
        self.register(PromptTemplate(
            name="data_summary",
            description="將結構化資料轉換為自然語言摘要",
            template="""請根據以下 JSON 資料生成一份結構化的中文摘要報告。

## 資料內容
```json
{{data}}
```

## 摘要要求
1. 使用簡潔的中文描述資料內容
2. 突出重要的數據和趨勢
3. 如果有敏感資料已被遮罩（顯示為 * 符號），請忽略這些欄位的具體值
4. 保持專業的商業報告風格

請生成摘要："""
        ))
        
        # 員工資料分析模板
        self.register(PromptTemplate(
            name="employee_analysis",
            description="分析員工資料並生成人力資源報告",
            template="""作為人力資源分析師，請根據以下員工資料生成分析報告。

## 部門：{{department}}

## 員工資料
```json
{{employees}}
```

## 分析要求
1. 統計該部門的員工人數
2. 分析職位分佈
3. 識別資深員工（入職超過3年）
4. 提供團隊結構建議
5. 注意：任何被遮罩的個人資訊（email、電話等）請勿嘗試推測

請生成分析報告："""
        ))
        
        # 專案狀態報告模板
        self.register(PromptTemplate(
            name="project_status",
            description="生成專案狀態彙總報告",
            template="""請根據以下專案資料生成專案狀態報告。

## 專案清單
```json
{{projects}}
```

## 報告要求
1. 按專案狀態分類（進行中、已完成、規劃中）
2. 計算總預算與各專案預算佔比
3. 識別時程風險（接近或超過截止日期）
4. 提供專案管理建議

當前日期：{{current_date}}

請生成專案狀態報告："""
        ))
        
        # API 資料摘要模板
        self.register(PromptTemplate(
            name="api_data_summary",
            description="摘要外部 API 取得的資料",
            template="""請分析以下從 API 取得的資料並生成摘要。

## 資料來源：{{source}}
## 資料類型：{{data_type}}

## 原始資料
```json
{{data}}
```

## 分析重點
{{focus_areas}}

請根據分析重點生成摘要報告："""
        ))
        
        # 通用問答模板
        self.register(PromptTemplate(
            name="qa_with_context",
            description="基於資料回答使用者問題",
            template="""請根據以下資料回答使用者的問題。

## 可用資料
```json
{{context_data}}
```

## 使用者問題
{{question}}

## 回答要求
1. 僅根據提供的資料回答，不要假設或推測未提供的資訊
2. 如果資料不足以回答問題，請明確說明
3. 被遮罩的資料（顯示為 * 符號）代表敏感資訊，請勿嘗試推測
4. 使用簡潔清晰的中文回答

請回答："""
        ))
        
        # 自訂摘要模板
        self.register(PromptTemplate(
            name="custom_summary",
            description="使用自訂指令生成摘要",
            template="""{{custom_instructions}}

## 資料
```json
{{data}}
```

請根據上述指令處理資料："""
        ))
    
    def register(self, template: PromptTemplate) -> None:
        """註冊新的 prompt 模板
        
        Args:
            template: PromptTemplate 實例
        """
        self.templates[template.name] = template
    
    def get(self, name: str) -> PromptTemplate | None:
        """取得指定名稱的模板
        
        Args:
            name: 模板名稱
            
        Returns:
            PromptTemplate 實例或 None
        """
        return self.templates.get(name)
    
    def list_templates(self) -> list[dict[str, Any]]:
        """列出所有可用的模板
        
        Returns:
            模板資訊列表
        """
        return [
            {
                "name": t.name,
                "description": t.description,
                "variables": t.variables
            }
            for t in self.templates.values()
        ]
    
    def render(self, template_name: str, **kwargs) -> str:
        """渲染指定的模板
        
        Args:
            template_name: 模板名稱
            **kwargs: 模板變數
            
        Returns:
            渲染後的 prompt
            
        Raises:
            ValueError: 當模板不存在或缺少必要變數時
        """
        template = self.get(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        valid, missing = template.validate(**kwargs)
        if not valid:
            raise ValueError(f"缺少必要變數: {', '.join(missing)}")
        
        return template.render(**kwargs)


# 全域 prompt 函式庫實例
prompt_library = PromptLibrary()
