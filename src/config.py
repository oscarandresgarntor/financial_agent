"""
Configuration and environment variables for the Voice AI Agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Vapi.ai Configuration
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")

    # OpenAI Configuration (used by Vapi for LLM)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Webhook Configuration
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Agent Configuration
    ASSISTANT_NAME: str = "Andrew"
    BANK_NAME: str = "Bull Bank"

    @classmethod
    def validate(cls) -> list[str]:
        """Validate that required environment variables are set."""
        errors = []
        if not cls.VAPI_API_KEY:
            errors.append("VAPI_API_KEY is required")
        return errors


# Create a singleton config instance
config = Config()
