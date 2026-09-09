# Breaky Backend API Reference

## Endpoints

### Health Check
- **GET** `/health`
- **Response:** `{"status": "ok"}`

### Data Ingestion
- **POST** `/ingest`: Single record ingestion
- **POST** `/ingest/batch`: Batch record ingestion

## Database Seeding
- Standard run: `python backend/seed.py`
- With reset flag: `python backend/seed.py --reset`