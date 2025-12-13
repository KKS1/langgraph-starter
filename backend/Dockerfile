FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 18000
CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "18000", "--reload"]
