FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN chmod +x download_models.sh && ./download_models.sh
EXPOSE 8501
# CMD will be set after confirming the main app file 