import os

class Settings:
    PROJECT_NAME: str = "GetVideo"
    VERSION: str = "2.0.0"
    CHUNK_SIZE: int = 65536  # 64 KB par chunk
    ALLOWED_ORIGINS: list = ["*"]
    
    # User-Agent moderne
    DEFAULT_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

settings = Settings()
