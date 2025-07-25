FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install flask pillow numpy scipy opencv-python
EXPOSE 5000
CMD ["python", "app.py"]     