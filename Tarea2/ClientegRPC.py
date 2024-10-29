import grpc
import orders_pb2
import orders_pb2_grpc

def get_order_data():
    print("Ingrese los detalles del pedido:")
    product_name = input("Nombre del producto: ")
    price = float(input("Precio: "))
    payment_gateway = input("Medio de pago: ")
    card_brand = input("Tipo de tarjeta: ")
    bank = input("Banco: ")
    region = input("Región de envío: ")
    address = input("Dirección de envío: ")
    email = input("Correo electrónico: ")
    return orders_pb2.Order(
        product_name=product_name,
        price=price,
        payment_gateway=payment_gateway,
        card_brand=card_brand,
        bank=bank,
        region=region,
        address=address,
        email=email,
    )

def run():
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = orders_pb2_grpc.OrderManagementStub(channel)

            order = get_order_data()
            response = stub.CreateOrder(order)

            if response.status != "Order Created":
                print(f"Error al crear el pedido: {response.status}")
            else:
                print(f"Respuesta del servidor: {response.status}, ID del pedido: {response.order_id}")
    except grpc.RpcError as e:
        print(f"Ocurrió un error en la comunicación con el servidor: {e.code()} - {e.details()}")

if __name__ == '__main__':
    run()


