#!/bin/bash

# RAG-Anything 开发环境启动脚本

echo "======================================"
echo "  RAG-Anything 开发环境启动脚本"
echo "======================================"

# 检查是否在正确的目录
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 启动前端开发服务器
echo ""
echo "正在启动前端开发服务器..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo "前端服务器已启动 (PID: $FRONTEND_PID)"
echo "访问地址: http://localhost:3000"
echo ""
echo "提示:"
echo "- 前端运行在 http://localhost:3000"
echo "- 后端API需要单独启动 (参考 README_SETUP.md)"
echo ""
echo "按 Ctrl+C 停止前端服务器"

# 等待前端进程
wait $FRONTEND_PID
