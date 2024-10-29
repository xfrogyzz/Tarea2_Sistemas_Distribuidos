import json
import time

def publish_kafka_message(self, order_id, state, email):
    message = {
        "order_id": order_id,
        "state": state,
        "email": email,
        "timestamp": time.time()
    }
    
    # Asegúrate de que el productor esté correctamente inicializado
    producer.produce(TOPIC, json.dumps(message).encode('utf-8'))
    producer.flush()  # Asegúrate de que los mensajes se envíen inmediatamente
    print(f"Publicado en Kafka: {message}")
