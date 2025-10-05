# 通义千问配置完成 ✅

## 🎯 问题诊断

### 原始问题
重度及特重度烧伤患者康复期照护干预方案的多维度构建 (1)_2.pdf 文档处理后，LLM没有提取实体和实体关系。

### 根本原因
1. **API密钥未配置** - 环境变量中未设置通义千问API Key
2. **Embedding模型配置错误** - 使用了OpenAI的`text-embedding-3-large`而非通义千问的`text-embedding-v3`
3. **Embedding维度不匹配** - OpenAI模型使用3072维，通义千问使用1024维
4. **不支持的API参数** - LightRAG传递了`hashing_kv`参数，通义千问不支持
5. **代码Bug** - `get_all_nodes()`和`get_all_edges()`返回类型处理错误

---

## ✅ 已完成的修复

### 1. 环境变量配置 (`.env`)
```bash
DASHSCOPE_API_KEY=sk-48e5e88388384e06938acb67198b655a
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DEFAULT_LLM_MODEL=qwen-turbo
DEFAULT_VLM_MODEL=qwen-vl-max
DEFAULT_EMBEDDING_MODEL=text-embedding-v3
DEFAULT_EMBEDDING_DIM=1024
```

### 2. 代码修复

#### A. `backend/app/core/config.py`
```python
# 修改默认值从OpenAI改为通义千问
DEFAULT_LLM_MODEL: str = "qwen-turbo"
DEFAULT_VLM_MODEL: str = "qwen-vl-max"
DEFAULT_EMBEDDING_MODEL: str = "text-embedding-v3"
DEFAULT_EMBEDDING_DIM: int = 1024  # 从3072改为1024
```

#### B. `backend/app/services/document_processor.py`
**修复1：过滤不支持的LLM参数**
```python
# 在llm_model_func中添加参数过滤
supported_params = ['temperature', 'top_p', 'max_tokens', 'frequency_penalty', 
                   'presence_penalty', 'stop', 'n', 'stream', 'logit_bias', 'user']
filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}
```

**修复2：处理list/dict返回类型**
```python
# 在_extract_graph_data中处理不同返回类型
if isinstance(nodes, dict):
    nodes_items = nodes.items()
elif isinstance(nodes, list):
    nodes_items = enumerate(nodes)
```

#### C. `backend/app/api/v1/endpoints/query.py`
```python
# 修改默认embedding维度
"parameters": {"embedding_dim": 1024, "max_token_size": 8192}
```

### 3. 数据清理
- 清除了旧的向量数据库文件（`vdb_*.json`）
- 清除了kb_3的缓存以避免维度冲突

---

## 🎉 验证结果

### 文档处理成功
- **文件**: 重度及特重度烧伤患者康复期照护干预方案的多维度构建 (1)_2.pdf
- **实体数量**: **51个**
- **关系数量**: **40个**
- **状态**: ✅ 已成功存入Neo4j

### 提取的实体示例
通过LLM成功提取了烧伤康复相关的概念、方法、组织、人员等实体，并建立了它们之间的关系。

---

## 📋 后续步骤

### 1. 重启后端服务 ⚠️
**必须重启后端服务以使配置生效！**

```bash
# 停止当前运行的后端服务
# 然后重新启动
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 处理新文档
重启服务后，可以上传新文档进行处理。系统现在会：
- ✅ 使用通义千问的LLM模型（qwen-turbo）
- ✅ 使用通义千问的VLM模型（qwen-vl-max）
- ✅ 使用通义千问的Embedding模型（text-embedding-v3，1024维）
- ✅ 正确提取实体和关系

### 3. 查看Neo4j中的知识图谱
```cypher
// 查看所有实体
MATCH (e:Entity {kb_id: 3}) RETURN e LIMIT 100

// 查看实体关系
MATCH (s:Entity {kb_id: 3})-[r]->(t:Entity {kb_id: 3}) 
RETURN s.name, type(r), t.name
LIMIT 50
```

---

## 🔧 故障排除

### 如果遇到维度不匹配错误
```bash
# 清除知识库的向量数据库
cd backend
Remove-Item storage/vectors/kb_X/vdb_*.json -Force
```

### 如果API调用失败
1. 检查`.env`文件中的`DASHSCOPE_API_KEY`是否正确
2. 确认API Key有足够的额度
3. 检查网络连接

### 如果实体数量为0
1. 检查日志中是否有LLM调用错误
2. 确认模型配置正确
3. 验证API Key是否有效

---

## 📊 系统配置摘要

| 配置项 | 值 |
|-------|-----|
| LLM模型 | qwen-turbo |
| VLM模型 | qwen-vl-max |
| Embedding模型 | text-embedding-v3 |
| Embedding维度 | 1024 |
| API提供商 | 阿里云通义千问 |
| 解析器 | MinerU (API模式) |

---

## 📝 注意事项

1. **不要混用不同维度的embedding模型** - 会导致向量数据库维度冲突
2. **清除缓存后需要重新处理文档** - 实体和关系会重新提取
3. **API额度** - 确保通义千问API有足够的调用额度
4. **环境变量优先级** - 代码中的默认值会被`.env`覆盖

---

## ✨ 配置完成时间
2025-10-05

配置人员：AI Assistant
文档版本：v1.0

