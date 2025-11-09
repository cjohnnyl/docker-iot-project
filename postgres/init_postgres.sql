CREATE TABLE IF NOT EXISTS viveiro_iot (
    sensor_id VARCHAR(50),
    estufa_id VARCHAR(50),
    bed_id INT,
    clone_id VARCHAR(50),
    soil_temp_c FLOAT,
    humidity FLOAT,
    timestamp TIMESTAMP
);
