from elasticsearch import Elasticsearch
from datetime import datetime

# Conectar a Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

def fetch_metrics():
    # Consultar datos de Elasticsearch
    response = es.search(
        index='order_metrics',
        body={'size': 1000, 'query': {'match_all': {}}}
    )
    return response['hits']['hits']

def analyze_data(data):
    total_latency = 0
    total_orders = len(data)  # Total de pedidos
    latencies = []

    # Calcular latencia total y recolectar latencias individuales
    for entry in data:
        source = entry['_source']

        if 'latency' in source and isinstance(source['latency'], (float, int)):
            latencies.append(source['latency'])
            total_latency += source['latency']

    # Calcular métricas
    average_latency = total_latency / len(latencies) if latencies else 0
    throughput = total_orders / (len(latencies) if latencies else 1)  # Pedidos por unidad de latencia

    # Mostrar métricas
    print("=== Métricas de Procesamiento de Pedidos ===")
    print(f"Número total de pedidos procesados: {total_orders}")
    print(f"Latencia promedio: {average_latency:.2f} segundos")
    print(f"Throughput: {throughput:.2f} pedidos por unidad de latencia")
    print("=============================================")

if __name__ == '__main__':
    try:
        data = fetch_metrics()
        analyze_data(data)
    except Exception as e:
        print("Error al recuperar o analizar los datos:", e)

