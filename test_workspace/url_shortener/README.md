# URL Shortener Service

A production-ready URL shortener service built with FastAPI and SQLite. Features include custom short codes, expiration dates, click tracking, and comprehensive API documentation.

## Features

- **URL Shortening**: Convert long URLs into short, manageable links
- **Custom Codes**: Option to specify custom short codes
- **Expiration**: Set expiration dates for short URLs
- **Click Tracking**: Monitor click counts for each shortened URL
- **RESTful API**: Full REST API with automatic documentation
- **Caching**: Built-in caching for improved performance
- **Rate Limiting**: Configurable rate limiting for API protection
- **Health Checks**: Built-in health check endpoints
- **Comprehensive Testing**: Full test coverage with pytest
- **Production Ready**: Error handling, logging, and configuration management

## Project Structure

```
url_shortener/
├── __init__.py          # Package initialization
├── base62.py            # Base62 encoding/decoding module
├── database.py          # Database models and operations
├── main.py              # FastAPI application and endpoints
├── config/
│   ├── __init__.py
│   ├── settings.py      # Application settings
│   └── logging_config.py # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_base62.py   # Base62 module tests
│   ├── test_database.py # Database tests
│   └── test_api.py      # API endpoint tests
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or navigate to the project directory:**
   ```bash
   cd ./test_workspace/url_shortener
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment configuration (optional):**
   Create a `.env` file in the project root to customize settings:
   ```env
   # Application Settings
   APP_NAME=URL Shortener
   DEBUG=false

   # Server Settings
   HOST=0.0.0.0
   PORT=8000

   # Database
   DATABASE_URL=url_shortener.db

   # URL Settings
   BASE_URL=http://localhost:8000
   MIN_CODE_LENGTH=6

   # Security (optional)
   ENABLE_API_KEY=false
   API_KEY=your-secret-key

   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=logs/app.log
   ```

## Usage

### Starting the Server

**Development mode (with auto-reload):**
```bash
uvicorn url_shortener.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
gunicorn url_shortener.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### API Documentation

Once the server is running, you can access:
- **Interactive API documentation**: http://localhost:8000/docs
- **Alternative API documentation**: http://localhost:8000/redoc

### API Endpoints

#### 1. **Shorten URL**
```bash
POST /shorten

# Basic usage
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url"}'

# With custom code
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/very/long/url",
    "custom_code": "mycode"
  }'

# With expiration (7 days)
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/very/long/url",
    "expires_in_days": 7
  }'
```

Response:
```json
{
  "short_url": "http://localhost:8000/abc123",
  "original_url": "https://example.com/very/long/url",
  "short_code": "abc123",
  "expires_at": null
}
```

#### 2. **Redirect to Original URL**
```bash
GET /{code}

# Browser or curl
curl -L "http://localhost:8000/abc123"
```

#### 3. **Get URL Statistics**
```bash
GET /api/stats/{code}

curl "http://localhost:8000/api/stats/abc123"
```

Response:
```json
{
  "original_url": "https://example.com/very/long/url",
  "short_code": "abc123",
  "created_at": "2024-01-15T10:30:00",
  "click_count": 42,
  "is_active": true,
  "expires_at": null
}
```

#### 4. **Delete URL**
```bash
DELETE /api/{code}

curl -X DELETE "http://localhost:8000/api/abc123"
```

#### 5. **Health Check**
```bash
GET /api/health

curl "http://localhost:8000/api/health"
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "total_urls": 150,
  "active_urls": 145
}
```

## Running Tests

Run all tests with coverage report:
```bash
pytest --cov=url_shortener --cov-report=term-missing
```

Run specific test modules:
```bash
# Test base62 encoding
pytest tests/test_base62.py

# Test database operations
pytest tests/test_database.py

# Test API endpoints
pytest tests/test_api.py
```

Run tests with verbose output:
```bash
pytest -v
```

## Configuration

The service can be configured through environment variables or a `.env` file. Key configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `DATABASE_URL` | SQLite database path | url_shortener.db |
| `BASE_URL` | Base URL for shortened links | http://localhost:8000 |
| `MIN_CODE_LENGTH` | Minimum length for generated codes | 6 |
| `ENABLE_API_KEY` | Enable API key authentication | false |
| `API_KEY` | API key for protected endpoints | None |
| `LOG_LEVEL` | Logging level | INFO |
| `ENABLE_CACHE` | Enable URL caching | true |
| `CACHE_TTL` | Cache time-to-live in seconds | 300 |

## Security Features

1. **API Key Authentication**: Optional API key protection for admin endpoints
2. **Rate Limiting**: Configurable request rate limiting
3. **Input Validation**: Strict validation of URLs and custom codes
4. **SQL Injection Protection**: Parameterized queries
5. **CORS Configuration**: Customizable CORS settings

## Performance Features

1. **Caching**: TTL-based caching for frequently accessed URLs
2. **Database Indexing**: Optimized indexes for fast lookups
3. **Async Operations**: Non-blocking click count updates
4. **Connection Pooling**: Efficient database connection management

## Production Deployment

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "url_shortener.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t url-shortener .
docker run -p 8000:8000 -v $(pwd)/url_shortener.db:/app/url_shortener.db url-shortener
```

### Environment Variables for Production

```env
DEBUG=false
BASE_URL=https://your-domain.com
ENABLE_API_KEY=true
API_KEY=your-secure-api-key
LOG_FILE=/var/log/url_shortener.log
DATABASE_URL=/data/url_shortener.db
```

### Database Backup

SQLite database can be backed up with:
```bash
sqlite3 url_shortener.db ".backup backup.db"
```

## Monitoring

The service includes several monitoring features:

1. **Health checks** at `/api/health`
2. **Structured logging** with configurable levels
3. **Click tracking** for analytics
4. **Database statistics** via API

## API Rate Limiting

When rate limiting is enabled (`RATE_LIMIT_ENABLED=true`), the service limits requests per IP address:
- Default: 100 requests per 60 seconds
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_PERIOD`

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, please create an issue in the project repository.
