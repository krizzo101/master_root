import uvicorn
from .logger import setup_logger

if __name__ == "__main__":
    setup_logger()
    uvicorn.run(
        "json_data_processor.api:app", host="0.0.0.0", port=8000, log_level="info"
    )
