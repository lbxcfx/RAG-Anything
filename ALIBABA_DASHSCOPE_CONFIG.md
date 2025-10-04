# 阿里云通义千问（DashScope）配置指南

## 概述

RAG-Anything现已支持阿里云通义千问大模型（DashScope API）。DashScope提供OpenAI兼容的API接口，可以无缝集成到现有系统中。

## 支持的模型

### 语言模型 (LLM)
- `qwen-turbo` - 通义千问超大规模语言模型，支持中英文
- `qwen-plus` - 通义千问增强版，效果更优
- `qwen-max` - 通义千问旗舰版，最强性能
- `qwen-long` - 长文本处理专用模型

### 视觉模型 (VLM)
- `qwen-vl-plus` - 通义千问视觉理解模型
- `qwen-vl-max` - 通义千问视觉理解旗舰版

### 向量模型 (Embedding)
- `text-embedding-v1` - 通用文本向量化模型
- `text-embedding-v2` - 增强版文本向量化模型

更多模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models

## 配置步骤

### 1. 获取API Key

访问阿里云模型服务平台获取API Key：
- 北京地域：https://dashscope.console.aliyun.com/apiKey
- 新加坡地域：https://dashscope-intl.console.aliyun.com/apiKey

**注意**：北京地域和新加坡地域的API Key不同，需要分别申请。

### 2. 环境变量配置

在 `.env` 文件中添加：

```bash
# 阿里云DashScope API配置
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 选择地域（可选，默认为北京地域）
# 北京地域（默认）
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 新加坡地域（如果使用新加坡地域，取消注释下面这行）
# DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

### 3. 前端界面配置

1. 登录RAG-Anything平台
2. 进入"模型配置"页面
3. 点击"添加模型"
4. 填写配置信息：

#### LLM模型配置示例

```
配置名称: 通义千问Plus
模型类型: LLM
提供商: alibaba-dashscope
模型名称: qwen-plus
API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
API Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
参数配置:
{
  "temperature": 0.7,
  "top_p": 0.8,
  "max_tokens": 2000
}
```

#### VLM模型配置示例

```
配置名称: 通义千问VL
模型类型: VLM
提供商: alibaba-dashscope
模型名称: qwen-vl-plus
API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
API Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
参数配置:
{
  "temperature": 0.5,
  "max_tokens": 1500
}
```

#### Embedding模型配置示例

```
配置名称: 通义文本向量V2
模型类型: EMBEDDING
提供商: alibaba-dashscope
模型名称: text-embedding-v2
API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
API Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
参数配置:
{
  "embedding_dim": 1536
}
```

## Python代码示例

### 基本调用示例

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': '你是谁？'}
    ]
)
print(completion.choices[0].message.content)
```

### 在RAG-Anything中的使用

系统会自动使用配置的模型信息，无需额外代码。RAG服务会根据用户选择的模型配置自动调用相应的API。

```python
# 在 rag_service.py 中会自动处理
def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
    return openai_complete_if_cache(
        model_config.get("model_name"),      # 如: qwen-plus
        prompt,
        system_prompt=system_prompt,
        api_key=model_config.get("api_key"),  # DASHSCOPE_API_KEY
        base_url=model_config.get("api_base_url"),  # dashscope base url
        **model_config.get("parameters", {}),
    )
```

## 地域选择

### 北京地域
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 适用于中国大陆用户
- 网络延迟低

### 新加坡地域
- Base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- 适用于海外用户
- 需要单独申请API Key

## 常见问题

### Q1: API Key在哪里获取？
A: 访问 https://help.aliyun.com/zh/model-studio/get-api-key 获取详细步骤。

### Q2: 支持哪些参数？
A: 支持OpenAI兼容的参数：
- `temperature`: 控制随机性 (0.0-2.0)
- `top_p`: 核采样参数 (0.0-1.0)
- `max_tokens`: 最大生成token数
- `stream`: 是否流式输出

### Q3: 如何切换模型？
A: 在知识库配置中选择不同的模型配置即可，系统会自动使用对应的API调用。

### Q4: 费用如何计算？
A: 按token计费，具体价格见：https://help.aliyun.com/zh/model-studio/getting-started/billing

### Q5: 遇到"API Key无效"错误？
A: 检查：
1. API Key是否正确
2. 地域是否匹配（北京/新加坡）
3. API Key是否已激活

## 参考链接

- 阿里云模型服务官网: https://www.aliyun.com/product/dashscope
- API文档: https://help.aliyun.com/zh/model-studio/developer-reference/api-overview
- 模型列表: https://help.aliyun.com/zh/model-studio/getting-started/models
- 定价说明: https://help.aliyun.com/zh/model-studio/getting-started/billing

## 更新日志

- 2025-10-03: 初始版本，添加阿里云DashScope支持
