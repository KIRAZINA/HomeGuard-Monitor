-- Initialize TimescaleDB extension and create hypertables

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the metrics table as a hypertable for time-series data
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    tags JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on device_id for faster queries
CREATE INDEX IF NOT EXISTS idx_metrics_device_id ON metrics (device_id);

-- Create index on metric_type for faster queries
CREATE INDEX IF NOT EXISTS idx_metrics_metric_type ON metrics (metric_type);

-- Create index on timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics (timestamp);

-- Convert metrics table to hypertable
SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);

-- Create continuous aggregates for hourly summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    device_id,
    metric_type,
    COUNT(*) as count,
    MIN(value) as min_value,
    MAX(value) as max_value,
    AVG(value) as avg_value
FROM metrics
GROUP BY hour, device_id, metric_type;

-- Add refresh policy for continuous aggregate
ADD CONTINUOUS AGGREGATE POLICY IF NOT EXISTS metrics_hourly_policy
ON metrics_hourly
WITH (start_offset => INTERVAL '1 day', end_offset => INTERVAL '1 hour', schedule_interval => INTERVAL '1 hour');

-- Create continuous aggregates for daily summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS day,
    device_id,
    metric_type,
    COUNT(*) as count,
    MIN(value) as min_value,
    MAX(value) as max_value,
    AVG(value) as avg_value
FROM metrics
GROUP BY day, device_id, metric_type;

-- Add refresh policy for continuous aggregate
ADD CONTINUOUS AGGREGATE POLICY IF NOT EXISTS metrics_daily_policy
ON metrics_daily
WITH (start_offset => INTERVAL '7 days', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 day');

-- Create retention policy to automatically delete old data
SELECT add_retention_policy('metrics', INTERVAL '30 days');

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
