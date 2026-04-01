CREATE TABLE sensor_data (
    sensor_id UInt32,
    area_code LowCardinality(String),
    reading_value Float64,
    timestamp DateTime64(3, 'UTC'),
    status Enum8('OK' = 1, 'WARN' = 2, 'FAIL' = 3)
) 
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (area_code, sensor_id, timestamp);

-- Insert dummy data
INSERT INTO sensor_data 
SELECT 
    rand() % 1000 AS sensor_id,
    multiIf(number % 3 == 0, 'NORTH', number % 3 == 1, 'SOUTH', 'CENTRAL') AS area_code,
    (rand() % 10000) / 100.0 AS reading_value,
    now() - (number / 100) AS timestamp,
    if(reading_value > 90, 'FAIL', if(reading_value > 70, 'WARN', 'OK')) AS status
FROM numbers(1000000);

-- Simple Count
select * from sensor_data;

-- Grouped Aggregation (The bread and butter of OLAP):
SELECT 
    area_code, 
    avg(reading_value) AS avg_reading, 
    max(reading_value) AS max_reading
FROM sensor_data 
WHERE status != 'OK'
GROUP BY area_code
ORDER BY avg_reading DESC;

-- Time-Series Analysis
SELECT 
    toStartOfHour(timestamp) AS hour, 
    count() AS total_events
FROM sensor_data 
GROUP BY hour 
ORDER BY hour DESC 
LIMIT 10;

-- Check Disk Usage
SELECT 
    table, 
    formatReadableSize(sum(data_compressed_bytes)) AS compressed, 
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed,
    round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS ratio
FROM system.parts 
WHERE table = 'sensor_data' AND active 
GROUP BY table;