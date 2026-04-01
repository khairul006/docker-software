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


select * from sensor_data;

INSERT INTO sensor_data 
SELECT 
    rand() % 1000 AS sensor_id,
    multiIf(number % 3 == 0, 'NORTH', number % 3 == 1, 'SOUTH', 'CENTRAL') AS area_code,
    (rand() % 10000) / 100.0 AS reading_value,
    now() - (number / 100) AS timestamp,
    if(reading_value > 90, 'FAIL', if(reading_value > 70, 'WARN', 'OK')) AS status
FROM numbers(1);