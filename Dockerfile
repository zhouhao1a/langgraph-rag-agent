# 基础镜像：官方 Python 3.11 精简版（3.11 换成你本地的 python --version 的版本）
FROM python:3.11-slim


# 容器内的工作目录
WORKDIR /app

# 先只拷依赖清单，装依赖（关键：利用 Docker 层缓存，下面讲）
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 再拷项目代码
COPY . .

# 声明端口（只是文档性质，实际对外映射靠 -p）
EXPOSE 8000

# 容器启动时执行的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]