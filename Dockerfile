# SwanLab-Server Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY .. .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Node.js依赖并构建前端
RUN npm install && npm run build

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV SWANLAB_LOG_DIR=/app/logs
ENV SWANLAB_DATA_DIR=/app/data

# 暴露端口
EXPOSE 5173

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5173/api/v1/cloud/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "swanboard.app:app", "--host", "0.0.0.0", "--port", "5173", "--log-level", "debug"]
