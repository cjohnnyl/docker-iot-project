FROM python:3.10-slim
WORKDIR /app
COPY producer.py .
COPY wait-for-kafka.sh .
RUN pip install --no-cache-dir kafka-python faker
RUN chmod +x wait-for-kafka.sh
CMD ["./wait-for-kafka.sh", "kafka:9092", "python", "producer.py"]
