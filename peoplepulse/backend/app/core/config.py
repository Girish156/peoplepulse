"""
PeoplePulse application configuration.

All settings can be overridden via environment variables or a .env file.

WARNING: DEMO_MODE=True is NOT production-ready.  In demo mode the app uses
hard-coded credentials and a shared secret key.  Set DEMO_MODE=False and
supply strong values for SECRET_KEY, DATABASE_URL, etc. before deploying.
"""
from __future__ import annotations

import os
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = "sqlite:///./peoplepulse.db"

    # ------------------------------------------------------------------ #
    # JWT / Auth                                                           #
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = "dev-secret-key-change-in-production-never-use-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ------------------------------------------------------------------ #
    # CORS                                                                 #
    # ------------------------------------------------------------------ #
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    # ------------------------------------------------------------------ #
    # Application metadata                                                 #
    # ------------------------------------------------------------------ #
    APP_NAME: str = "PeoplePulse"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ------------------------------------------------------------------ #
    # Demo mode                                                            #
    # WARNING: NOT for production use.  DEMO_MODE enables built-in        #
    # credential shortcuts that bypass real identity management.           #
    # ------------------------------------------------------------------ #
    DEMO_MODE: bool = True
    DEMO_USERNAME: str = "admin@peoplepulse.demo"
    DEMO_PASSWORD: str = "PeoplePulse2026!"


settings = Settings()
