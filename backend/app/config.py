"""
Central configuration for WeatherGPT backend.
All secrets/config are pulled from environment variables (see .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "WeatherGPT Backend"
    ENV: str = "development"
    ALLOWED_ORIGINS: str = "*"  # comma-separated list of allowed frontend origins

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://weathergpt:weathergpt@localhost:5432/weathergpt"

    # --- OpenRouter ---
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openrouter/free"

    # --- Weather data provider (OpenWeatherMap) ---
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
