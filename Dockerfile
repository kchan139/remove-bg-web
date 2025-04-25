FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /home/.u2net

RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*
    
RUN wget -O /home/.u2net/u2net.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD [ "python", "app.py" ]
# CMD [ "python", "-m", "pytest", "test/", "-v" ]