from kafka import KafkaProducer
import json, time, random, datetime, os

broker = os.getenv("KAFKA_BROKER", "kafka:9092")
topic = os.getenv("TOPIC", "iot_sensors")

producer = KafkaProducer(
    bootstrap_servers=broker,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

while True:
    msg = {
        "sensor_id": f"s{random.randint(1,5)}",
        "estufa_id": "EUCALIPTO_01",
        "bed_id": random.randint(1,10),
        "clone_id": f"CL{random.randint(100,999)}",
        "soil_temp_c": round(random.uniform(22.0, 30.0), 2),
        "humidity": round(random.uniform(50.0, 80.0), 2),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    producer.send(topic, msg)
    print(f"[Producer] Sent: {msg}")
    time.sleep(3)
