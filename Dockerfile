# 使用官方 Python 基礎映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製需求檔案並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案所有檔案
COPY . .

# 指定 Flask 執行環境變數
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 開放 Flask 的預設埠口
EXPOSE 5000

# 啟動指令
CMD ["flask", "run"]
