FROM python:3.9-slim

RUN \
  apt-get update -y && \
  apt-get install -qq libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1 && \
  rm -rf /var/lib/apt/lists/*

EXPOSE 3000

ENV PYTHONUNBUFFERED=1

ARG tflite_runtime=tflite_runtime-2.5.0.post1-cp39-cp39-linux_x86_64.whl

COPY requirements.txt ./wheels/$tflite_runtime ./

RUN pip install --no-cache-dir $tflite_runtime && \
	pip install --no-cache-dir -r requirements.txt && \
	rm -r requirements.txt  $tflite_runtime

RUN mkdir -p /image_tmp
RUN mkdir -p /log

WORKDIR /config
COPY ./config/ ./

WORKDIR /app
COPY ./code/ ./

CMD ["python", "./meter.py"]
