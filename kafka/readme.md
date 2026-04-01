# Kafka

## POST register the connector

1. Register with no integer handling
    ```json
    {
        "name": "toll-transaction-connector",
        "config": {
            "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
            "tasks.max": "1",
            "database.hostname": "127.0.0.1",
            "database.port": "5433",
            "database.user": "postgres",
            "database.password": "postgres",
            "database.dbname": "postgres",
            "topic.prefix": "toll_sys",
            "table.include.list": "public.transaction",
            "plugin.name": "pgoutput",
            "slot.name": "debezium_toll_slot",
            "publication.autocreate.mode": "filtered",
            "key.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable": "false",
            "value.converter.schemas.enable": "false"
        }
    }
    ```

2. Register with Debezium to send the money as a plain, human-readable string (e.g., "10.50") instead of that Base64.
    ```json
    {
        "name": "toll-transaction-connector",
        "config": {
            "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
            "tasks.max": "1",
            "database.hostname": "127.0.0.1", 
            "database.port": "5432",
            "database.user": "postgres",
            "database.password": "postgres",
            "database.dbname": "postgres",
            "topic.prefix": "toll_sys",
            "table.include.list": "public.transaction",
            "plugin.name": "pgoutput",
            "decimal.handling.mode": "string", // handle numeric as plaintext
            "slot.name": "debezium_toll_slot",
            "publication.autocreate.mode": "filtered",
            "key.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable": "false",
            "value.converter.schemas.enable": "false"
        }
    }
    ```