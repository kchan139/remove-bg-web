FROM python:3.12

COPY u2net.onnx /home/.u2net/u2net.onnx

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD [ "python", "app.py" ]