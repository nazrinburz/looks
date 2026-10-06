"""
config.py - Application configuration management.

Loads environment variables from .env file and provides
centralized constants for the application.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Base configuration class with all settings."""

    # Flask settings
    DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    ENV: str = os.getenv("FLASK_ENV", "development")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "./database.db")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_EXPIRY_HOURS: int = 24

    # Validation limits
    MIN_PASSWORD_LENGTH: int = 8
    MAX_FEEDBACK_LENGTH: int = 500
    MIN_RATING: int = 1
    MAX_RATING: int = 10

    # CORS – restrict in production
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # Pagination defaults
    DEFAULT_PAGE_LIMIT: int = 20


# Expose a singleton instance used across the app
config = Config()
