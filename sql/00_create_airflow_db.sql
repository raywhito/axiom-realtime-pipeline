-- Create a separate metadata database for Airflow (runs before the landing schema).
-- Executed by the Postgres container on first boot, from the default connection.
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
