from confluent_kafka import Producer, Consumer, KafkaError
from datetime import datetime
import orders_pb2
import orders_pb2_grpc
from elasticsearch import Elasticsearch
from concurrent import futures
import grpc
import json
import time
import random
import threading

# Configuración del broker de Kafka
TOPIC = 'order_updates'

KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',  # Cambiado para usar solo un broker
    'security.protocol': 'PLAINTEXT',  # Usar PLAINTEXT para conexiones sin SSL
}

# Inicializar productor y consumidor
producer = Producer(KAFKA_CONFIG)
consumer = Consumer({
    **KAFKA_CONFIG,
    'group.id': 'order_group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe([TOPIC])

# Conectar a Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

class OrderStateMachine:
    STATES = ['Procesando', 'Preparación', 'Enviado', 'Entregado', 'Finalizado']

    def __init__(self, order_id):
        self.order_id = order_id
        self.state_index = 0
        self.is_finished = False  # Indicador de si el pedido ha finalizado
        self.start_time = time.time()  # Tiempo de inicio para calcular latencia

    def next_state(self):
        if self.state_index < len(self.STATES) - 1:
            self.state_index += 1
            if self.state_index == len(self.STATES) - 1:  # Si se llega al estado final
                self.is_finished = True
            return self.STATES[self.state_index]
        else:
            return self.STATES[-1]

    def get_current_state(self):
        return self.STATES[self.state_index]

    def has_finished(self):
        return self.is_finished

    def get_latency(self):
        # Calcular latencia en segundos
        return time.time() - self.start_time

class OrderManagementServicer(orders_pb2_grpc.OrderManagementServicer):
    def __init__(self):
        self.orders = {}
        self.start_consumer()

    def start_consumer(self):
        consumer_thread = threading.Thread(target=self.consume_messages)
        consumer_thread.start()

    def consume_messages(self):
        while True:
            message = consumer.poll(timeout=1.0)
            if message is None:
                continue
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Error en Kafka: {message.error()}")
                    break

            order_update = json.loads(message.value().decode('utf-8'))
            order_id = order_update['order_id']
            print(f"Mensaje recibido de Kafka: {order_update}")

            # Verifica que el pedido exista antes de actualizar su estado
            if order_id in self.orders:
                self.update_order_state(order_id)
            else:
                print(f"Pedido {order_id} no encontrado al procesar el mensaje de Kafka.")

    def CreateOrder(self, request, context):
        order_id = f"ORD{random.randint(1000, 9999)}"
        state_machine = OrderStateMachine(order_id)
        self.orders[order_id] = {'state_machine': state_machine, 'email': request.email}
        initial_state = state_machine.get_current_state()
        self.publish_kafka_message(order_id, initial_state, request.email)
        self.log_metrics(order_id, initial_state, "Pedido recibido")
        print(f"Pedido creado: {order_id} con estado: {initial_state}")  # Agregado para depuración
        return orders_pb2.OrderResponse(status="Order Created", order_id=order_id)

    def update_order_state(self, order_id):
        if order_id in self.orders:
            state_machine = self.orders[order_id]['state_machine']
            new_state = state_machine.next_state()
            email = self.orders[order_id]['email']
            latency = state_machine.get_latency()  # Obtener la latencia

            if not state_machine.has_finished():  # Solo publicamos si no ha terminado
                self.publish_kafka_message(order_id, new_state, email)
                self.log_metrics(order_id, new_state, f"Estado actualizado a {new_state}", latency)

            # Si el nuevo estado es 'Finalizado', removemos el pedido de la lista
            if new_state == "Finalizado":
                del self.orders[order_id]  # Elimina el pedido de la lista
                print(f"Pedido {order_id} ha sido finalizado y eliminado de la lista.")
            return new_state
        else:
            print(f"Error: Pedido {order_id} no encontrado al intentar actualizar el estado.")
            raise ValueError(f"Pedido {order_id} no encontrado")

    def publish_kafka_message(self, order_id, state, email):
        message = {
            "order_id": order_id,
            "state": state,
            "email": email,
            "timestamp": time.time()
        }
        producer.produce(TOPIC, json.dumps(message).encode('utf-8'))
        producer.flush()
        print(f"Publicado en Kafka: {message}")

    def log_metrics(self, order_id, state, description, latency=None):
        document = {
            "order_id": order_id,
            "state": state,
            "description": description,
            "timestamp": time.time(),
            "latency": latency,
            "throughput": len(self.orders)  # Puedes calcular el throughput según tu lógica
        }
        es.index(index="order_metrics", body=document)
        print(f"Registrado en ElasticSearch: {document}")

    def simulate_processing(self, order_id):
        try:
            while True:
                current_state = self.update_order_state(order_id)
                print(f"Estado actual del pedido {order_id}: {current_state}")
                # Detenemos la simulación si el estado es 'Finalizado'
                if current_state == "Finalizado":
                    print(f"Pedido {order_id} ha sido finalizado.")
                    break  # Termina el bucle al alcanzar el estado final
                time.sleep(random.uniform(1, 3))  # Simula el tiempo de procesamiento
        except ValueError as e:
            print(e)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orders_pb2_grpc.add_OrderManagementServicer_to_server(OrderManagementServicer(), server)
    server.add_insecure_port('127.0.0.1:50051')
    server.start()
    print("Servidor gRPC en ejecución (puerto 50051)")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
