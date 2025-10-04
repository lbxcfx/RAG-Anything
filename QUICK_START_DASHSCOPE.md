# 阿里云通义千问快速配置指南

## 一、前置准备

### 1. 获取API Key
访问：https://dashscope.console.aliyun.com/apiKey
- 注册/登录阿里云账号
- 开通DashScope服务
- 创建API Key

### 2. 安装OpenAI SDK
```bash
cd E:\RAG-Anything\backend
venv\Scripts\python.exe -m pip install openai
```

## 二、配置步骤

### 方法1: 环境变量配置（推荐）

编辑 `.env.dev` 文件：
```bash
# 阿里云DashScope API配置
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx  # 替换为你的API Key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 方法2: 前端界面配置

1. 启动服务
```bash
# 后端
cd E:\RAG-Anything\backend
venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd E:\RAG-Anything\frontend
npm run dev
```

2. 访问 http://localhost:3003

3. 登录后进入"模型配置"页面

4. 点击"添加模型"，填写：

**配置名称**: 通义千问Plus
**模型类型**: LLM
**提供商**: alibaba-dashscope
**模型名称**: qwen-plus
**API Key**: sk-xxxxxxxxxxxxxxxxxxxxxxxx
**API Base URL**: https://dashscope.aliyuncs.com/compatible-mode/v1
**参数配置**:
```json
{
  "temperature": 0.7,
  "top_p": 0.8,
  "max_tokens": 2000
}
```

## 三、测试验证

### 运行测试脚本
```bash
cd E:\RAG-Anything\backend

# Windows
set DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
venv\Scripts\python.exe test_dashscope.py

# Linux/Mac
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
python test_dashscope.py
```

### 手动测试
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
        {'role': 'user', 'content': '你好'}
    ]
)
print(completion.choices[0].message.content)
```

## 四、支持的模型

### LLM模型
- `qwen-turbo` - 快速响应，适合对话
- `qwen-plus` - 综合能力强，推荐使用
- `qwen-max` - 最强性能，复杂任务
- `qwen-long` - 长文本处理

### VLM模型（视觉理解）
- `qwen-vl-plus` - 图像理解
- `qwen-vl-max` - 高级图像理解

### Embedding模型
- `text-embedding-v1` - 基础版本
- `text-embedding-v2` - 增强版本

## 五、常见配置示例

### 1. 高创造性配置（适合创作）
```json
{
  "temperature": 1.2,
  "top_p": 0.95,
  "max_tokens": 4000
}
```

### 2. 精准配置（适合问答）
```json
{
  "temperature": 0.3,
  "top_p": 0.8,
  "max_tokens": 2000
}
```

### 3. 平衡配置（通用推荐）
```json
{
  "temperature": 0.7,
  "top_p": 0.85,
  "max_tokens": 2500
}
```

## 六、地域选择

### 北京地域（推荐国内用户）
```
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 新加坡地域（海外用户）
```
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```
**注意**: 新加坡地域需要单独申请API Key

## 七、故障排除

### 问题1: "Invalid API Key"
**解决**:
1. 检查API Key是否正确
2. 确认地域是否匹配（北京/新加坡）
3. 确认API Key是否已激活

### 问题2: 连接超时
**解决**:
1. 检查网络连接
2. 尝试切换地域
3. 检查防火墙设置

### 问题3: 模型不存在
**解决**:
1. 确认模型名称拼写正确
2. 参考模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
3. 某些模型可能需要单独申请权限

## 八、下一步

配置完成后，你可以：

1. **创建知识库**: 使用通义千问进行RAG问答
2. **文档解析**: 利用VLM模型理解图片和表格
3. **向量化**: 使用Embedding模型构建向量数据库

## 九、参考文档

- 配置文档: `ALIBABA_DASHSCOPE_CONFIG.md`
- API文档: https://help.aliyun.com/zh/model-studio/developer-reference/api-overview
- 模型列表: https://help.aliyun.com/zh/model-studio/getting-started/models
- 定价: https://help.aliyun.com/zh/model-studio/getting-started/billing

---

**更新时间**: 2025-10-03
**版本**: 1.0.0
