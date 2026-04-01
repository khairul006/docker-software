-- Create a table with a Primary Key (Crucial for CDC)
CREATE TABLE transaction (
    id SERIAL PRIMARY KEY,
    exit_plaza VARCHAR(255) NOT NULL,
    entry_plaza VARCHAR(255) NULL,
    money_value NUMERIC(8, 2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Four Types of Replica Identity
-- DEFAULT: Only records the Primary Key values of the old row. Best for performance when you only need to know which row changed.
-- FULL: Records the Entire Row (all column values) for the old version. Use this if you need to compare "Before" vs "After" data in Kafka.
-- NOTHING: Records No Data about the old row. Avoid this for CDC, as Debezium won't be able to process DELETE events.
-- INDEX: Records the values of a Specific Unique Index you choose. Use this only if the table has no Primary Key but has a unique, non-null index.
ALTER TABLE transaction REPLICA IDENTITY FULL;


INSERT INTO transaction (exit_plaza, entry_plaza, money_value) 
VALUES ('123', '124', 3.45);