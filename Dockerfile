FROM python:3.11

WORKDIR /app

# 安装PDM
RUN pip install pdm -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 复制PDM项目文件
COPY pyproject.toml pdm.lock* ./

# 使用PDM安装依赖，不创建虚拟环境
RUN pdm config python.use_venv false && \
    pdm install --prod --no-lock --no-editable

# 复制应用代码
COPY app/ ./app/
COPY main.py ./

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]