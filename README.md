# Production CDC & Event-Driven Architecture Platform

A fully modernized, production-ready data engineering platform demonstrating **Change Data Capture (CDC)**, **Event-Driven Cache Invalidation**, and **Command-Based Broadcasts** using PostgreSQL, Debezium, Kafka (KRaft), RabbitMQ, Redis, and FastAPI.

---

## 🛑 The Problem: Cache Staleness & Tight Coupling

In modern scalable applications, keeping a high-speed cache (like Redis) synchronized with a persistent source of truth (like PostgreSQL) is notoriously difficult. 

Traditional approaches rely on the application backend to manually update both the database and the cache simultaneously (Dual Writes). This creates several severe problems:
1. **Tight Coupling**: The API must know about and manage the cache directly.
2. **Race Conditions & Staleness**: If the API crashes between updating the database and updating the cache, the cache becomes permanently stale.
3. **Implicit Data Changes**: If a database administrator manually updates a row in PostgreSQL, the API doesn't know about it, leaving the cache out of sync.

## ✅ The Solution: Change Data Capture (CDC) & Command Signaling

This project solves the "Dual Write" problem using **Change Data Capture (CDC)** combined with Event-Streaming.

Instead of the API managing the cache:
* The API **only** writes to PostgreSQL. 
* **Debezium** continuously tails the PostgreSQL Write-Ahead Log (WAL).
* When a row changes (even if done manually by a DBA), Debezium captures the event and reliably pushes it to **Kafka**.
* A standalone, decoupled **Cache Invalidator Worker** consumes the Kafka topic and automatically purges the specific Redis key.

### Kafka vs. RabbitMQ: Separation of Concerns
This project intentionally uses both Kafka and RabbitMQ to demonstrate a critical architectural distinction:
* **Kafka (Data Synchronization)**: Used for *Events* ("What Happened in the past"). State replication and CDC.
* **RabbitMQ (System Signaling)**: Used for *Commands* ("What to Do right now"). Instantly broadcasting manual `PURGE_CACHE` commands to a fleet of listeners.

---

## 🏛 Architecture Overview

```mermaid
graph TD
    API[FastAPI Backend] -->|Write to Truth| DB[(PostgreSQL)]
    DB -->|WAL Logs| Debezium[Debezium CDC Connector]
    Debezium -->|Emits Data Events| Kafka[Apache Kafka \n KRaft Mode]
    
    Kafka -->|Consumes Event Topic| Invalidator[Cache Invalidator Worker]
    Invalidator -->|Deletes Stale Key| Redis[(Redis Cache)]
    
    API -.->|Reads (Cache First)| Redis
    
    Publisher[RabbitMQ Publisher \n CLI Script] -->|Broadcasts PURGE| RabbitMQ[RabbitMQ \n Fanout Exchange]
    RabbitMQ -->|Receives Command| Listener[RabbitMQ Listener Worker]
    Listener -->|Force Deletes Key| Redis
```

---

## 🚀 Key Modernization Features

This repository has been fully refactored to align with senior-level DevOps and Data Engineering standards:

1. **Microservice Isolation**: Complete segregation of duties. The FastApi backend, Kafka Cache Invalidator, and RabbitMQ Listener are packaged independently with their own lean dependency bounds (`requirements.txt` per service).
2. **Kafka KRaft Migration**: Apache Kafka has been modernized to run in **KRaft Mode (Kafka Raft)**. ZooKeeper dependency has been entirely removed, drastically reducing compute footprint and speeding up cluster boot times.
3. **Resiliency & Fault Tolerance**: Both python worker services feature recursive `pika` and `kafka-python` connection loops globally. If the infrastructure takes 15 seconds to spin up, the workers gracefully wait and reconnect instead of crash-looping.
4. **DevOps Hardening**:
   - Single monolithic Dockerfiles were shattered into optimized, multi-stage, purpose-built `.Dockerfile` images.
   - `docker-compose.yml` mapped with exact `depends_on: condition: service_healthy` directives, ensuring logical orchestration flow.
   - Hardcoded IPs and credentials extracted into a centralized `.env` configuration schema.

---

## 📂 Project Structure

```text
cdc-project/
├── .env.example                # Global configuration layout
├── docker-compose.yml          # Core orchestration
├── README.md
├── infrastructure/
│   ├── debezium/               # Debezium Connector mappings
│   └── docker/
│       ├── api.Dockerfile
│       ├── cache-invalidator.Dockerfile
│       └── rabbit-listener.Dockerfile
├── scripts/
│   └── rabbitmq_publisher.py   # Manual RabbitMQ broadcaster tool
└── services/
    ├── api/                    # FastAPI Backend Application
    │   ├── requirements.txt
    │   └── src/
    ├── cache-invalidator/      # Kafka CDC Event Consumer
    │   ├── requirements.txt
    │   └── src/
    └── rabbit-listener/        # RabbitMQ Command Consumer
        ├── requirements.txt
        └── src/
```

---

## 🛠 Getting Started

### 1. Configure the Environment
Clone the repository and inject the environment variables.
```bash
cp .env.example .env
```

### 2. Boot the Infrastructure
Start the entire data engineering pipeline via Docker Compose.
```bash
docker-compose up --build -d
```
*Note: The Python microservices will cleanly wait for PostgreSQL, Redis, Kafka, and RabbitMQ to pass their explicit container healthchecks before connecting.*

### 3. Verify the Endpoints
Hit the FastAPI service:
```bash
curl http://localhost:8000/users
```
You will see `CACHE MISS` in the `cdc_fastapi` logs followed by a `CACHE HIT` on subsequent requests.

### 4. Test the System Signaling (RabbitMQ)
Force clear the cache across the entire topology by broadcasting via the publisher script:
```bash
python scripts/rabbitmq_publisher.py
```
Watch the Rabbit Listener elegantly purge the cache:
```bash
docker logs cdc_rabbit_listener -f
```

### 5. Test the CDC Synchronization (Kafka)
Simulate a manual database intervention by entering the PostgreSQL container and mutating data manually:
```bash
docker exec -it cdc_postgres psql -U admin -d social_db
> INSERT INTO users (username, bio) VALUES ('kraft_user', 'I bypass the API!');
```
Watch the Cache Invalidator instantly pick up the WAL log mutation via Kafka and invalidate the Redis key:
```bash
docker logs cdc_cache_invalidator -f
```
