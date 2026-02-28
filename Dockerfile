FROM python:3.11-slim

WORKDIR /app

# 复制后端相关文件
COPY miniprogram_server.py .
COPY miniprogram_config.json .
COPY miniprogram_push.py .

# 数据目录（用于持久化用户数据）
RUN mkdir -p /app/data

EXPOSE 8080

CMD ["python", "miniprogram_server.py"]
