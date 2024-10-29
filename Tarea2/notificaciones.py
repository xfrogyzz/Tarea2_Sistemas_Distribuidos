from confluent_kafka import Consumer, KafkaException
import smtplib
import json
from email.mime.text import MIMEText
import re

KAFKA_BROKER = 'localhost:9092' 
TOPIC = 'order_updates'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'sdtarea23@gmail.com'  
EMAIL_PASSWORD = 'dvar ukee pjkk wnxh' 

def is_valid_email(email):
    # Validar el formato del correo electrónico
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

def send_email(to_address, subject, message):
    if not is_valid_email(to_address):
        print(f'Correo electrónico no válido: {to_address}')
        return

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_address

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_address, msg.as_string())
            print(f'Correo enviado a {to_address} con asunto: {subject}')
    except Exception as e:
        print(f'Error enviando correo a {to_address}: {e}')

def run_consumer():
    # Configuración del consumidor de Confluent Kafka
    consumer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'email_notifier',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([TOPIC])
    
    print("Escuchando eventos de Kafka para notificaciones...")

    try:
        while True:
            msg = consumer.poll(1.0)  # Espera 1 segundo por mensajes nuevos
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    continue
                else:
                    print(f"Error de Kafka: {msg.error()}")
                    continue

            # Decodifica el mensaje y envía el correo
            event = json.loads(msg.value().decode('utf-8'))
            order_id = event['order_id']
            state = event['state']
            email = event['email']
            timestamp = event['timestamp']
            subject = f'Actualización de estado del pedido {order_id}'
            message = f'Su pedido con ID {order_id} ahora está en el estado: {state}.\nTimestamp: {timestamp}'
            
            # Solo enviamos el correo si el estado no es "Finalizado"
            if state != "Finalizado":
                send_email(email, subject, message)

    except KeyboardInterrupt:
        print("Interrupción del consumidor.")
    finally:
        consumer.close()

if __name__ == '__main__':
    run_consumer()
