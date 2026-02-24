import urllib.request
import time
import json
import statistics

API_URL = "http://localhost:8000/users"

def measure_latency(iterations=100):
    latencies = []
    
    # First request to ensure cache is hot
    try:
        urllib.request.urlopen(API_URL).read()
    except Exception as e:
        print(f"Error accessing API: {e}")
        return

    # Measure cached response time
    print(f"Measuring {iterations} requests...")
    for _ in range(iterations):
        start_time = time.time()
        urllib.request.urlopen(API_URL).read()
        end_time = time.time()
        latencies.append((end_time - start_time) * 1000) # Convert to ms
        
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max_latency
    
    print("\n--- KPI: Cache Read Latency ---")
    print(f"Average: {avg_latency:.2f} ms")
    print(f"Min:     {min_latency:.2f} ms")
    print(f"Max:     {max_latency:.2f} ms")
    print(f"P95:     {p95_latency:.2f} ms")
    print(f"Estimated Throughput: {1000 / avg_latency if avg_latency > 0 else 0:.0f} req/sec (Single Thread)")

if __name__ == "__main__":
    measure_latency(100)
    
