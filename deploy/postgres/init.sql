-- PostgreSQL Initialization Script
-- Creates dedicated databases for inference telemetry and MLflow tracking

CREATE DATABASE mlflow;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO postgres;
