# API尾随斜杠问题修复

## 问题描述

用户在登录后访问"模型配置"等页面时，出现"权限不足"的403错误。

## 根本原因

FastAPI路由定义的端点都有尾随斜杠（如 `/api/v1/models/`），但前端API调用没有尾随斜杠（如 `/api/v1/models`）。

这导致以下问题流程：
1. 前端发送请求：`GET /api/v1/models` (无斜杠)
2. FastAPI返回 `307 Temporary Redirect` 到 `/api/v1/models/` (有斜杠)
3. 浏览器自动跟随重定向
4. **重定向时Authorization header丢失**
5. 后端收到无token的请求，返回 403 Forbidden

## 解决方案

修改前端所有API调用，添加尾随斜杠以匹配后端路由定义。

### 修改的文件

1. **frontend/src/api/models.ts** - 模型配置API
2. **frontend/src/api/knowledge-base.ts** - 知识库API
3. **frontend/src/api/documents.ts** - 文档管理API
4. **frontend/src/api/query.ts** - 查询API
5. **frontend/src/api/graph.ts** - 图谱API

### 示例修改

**修改前：**
```typescript
export const modelsApi = {
  list(params?: any) {
    return request.get('/models', { params })  // 无斜杠
  },
}
```

**修改后：**
```typescript
export const modelsApi = {
  list(params?: any) {
    return request.get('/models/', { params })  // 有斜杠
  },
}
```

## 验证

修改后，所有API请求应该直接命中正确的路由，不再产生307重定向，Authorization header保持完整。

后端日志应该显示：
```
INFO: 127.0.0.1:xxxxx - "GET /api/v1/models/ HTTP/1.1" 200 OK
```

而不是：
```
INFO: 127.0.0.1:xxxxx - "GET /api/v1/models HTTP/1.1" 307 Temporary Redirect
INFO: 127.0.0.1:xxxxx - "GET /api/v1/models/ HTTP/1.1" 403 Forbidden
```

## 日期

2025-10-03
