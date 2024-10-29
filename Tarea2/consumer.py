def consume_messages(self):
    for message in consumer:
        order_update = json.loads(message.value.decode('utf-8'))
        order_id = order_update['order_id']
        new_state = order_update['state']
        print(f"Mensaje recibido de Kafka: {order_update}")
        self.update_order_state(order_id)  # Actualiza el estado del pedido
