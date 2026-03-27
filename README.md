# docker-software

A personal collection of ready-to-use Docker Compose setups for common backend services.

## 📦 Included Services

This repository contains default configurations for:

- PostgreSQL
- MySQL
- MongoDB
- Redis
- RabbitMQ
- Kafka

Each service has its own folder with a `docker-compose.yaml` file and minimal configuration for quick startup.

## 🚀 Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/docker-software.git
   cd docker-software
   ```

2. Navigate to the service you want:
    ```bash
    cd postgres
    ```

3. Start the container:
    ```bash
    docker compose up -d
    ```

4. Stop the container:
    ```
    docker compose down
    ```

## ⚙️ Purpose

This repo is meant to:
- Quickly spin up local development environments
- Avoid rewriting common Docker setups
- Keep configurations centralized and reusable

## 📝 Notes

- Configs are kept simple and minimal
- Modify `.env` or `docker-compose.yaml` as needed per project
- Not intended for production use without proper tuning