"""
Configuration management using Pydantic Settings.
Loads environment variables and provides type-safe configuration.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration (with demo defaults for testing)
    supabase_url: str = Field(default="https://fwsqwuyvsbyxycbcxijz.supabase.co", description="Supabase project URL")
    supabase_anon_key: str = Field(default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3c3F3dXl2c2J5eHljYmN4aWp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDM3NzksImV4cCI6MjA3MjU3OTc3OX0.52NRL9iiolmJ_XFQKPxCJ_S_GZJcPodVWwOBsghz3E4", description="Supabase anonymous key")
    supabase_service_role_key: str = Field(default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3c3F3dXl2c2J5eHljYmN4aWp6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzAwMzc3OSwiZXhwIjoyMDcyNTc5Nzc5fQ.tUv27y2g70wZmMcaO5nSunPVYwGiEO3cPpKIWj9kJF8", description="Supabase service role key")
    
    # Database Configuration (with demo default for testing)
    database_url: str = Field(default="postgresql+asyncpg://postgres:restaurant-saas@db.fwsqwuyvsbyxycbcxijz.supabase.co:6543/postgres", description="PostgreSQL database URL")
    
    # JWT Configuration (with demo default for testing)
    jwt_jwks_url: str = Field(default="https://fwsqwuyvsbyxycbcxijz.supabase.co/auth/v1/keys", description="JWT JWKS endpoint URL")
    jwt_algorithm: str = Field(default="RS256", description="JWT signing algorithm")
    jwt_audience: str = Field(default="authenticated", description="JWT audience")
    jwt_secret: Optional[str] = Field(default=None, description="JWT secret for HS256 algorithm")
    
    # OpenAI Configuration (Optional)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # Application Configuration
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    api_v1_str: str = Field(default="/api/v1", description="API v1 prefix")
    project_name: str = Field(default="Restaurant SaaS API", description="Project name")
    
    # CORS Configuration - using simpler approach to avoid parsing issues
    allowed_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://192.168.1.129:3001",
        description="Comma-separated list of allowed CORS origins",
        alias="ALLOWED_ORIGINS"
    )
    allowed_methods_str: str = Field(
        default="GET,POST,PUT,DELETE,PATCH,OPTIONS,HEAD",
        description="Comma-separated list of allowed HTTP methods",
        alias="ALLOWED_METHODS"
    )
    allowed_headers_str: str = Field(
        default="*",
        description="Comma-separated list of allowed headers",
        alias="ALLOWED_HEADERS"
    )
    
    @property
    def allowed_origins(self) -> List[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]
    
    @property 
    def allowed_methods(self) -> List[str]:
        """Parse comma-separated methods into a list."""
        return [method.strip() for method in self.allowed_methods_str.split(",") if method.strip()]
    
    @property
    def allowed_headers(self) -> List[str]:
        """Parse comma-separated headers into a list."""
        return [header.strip() for header in self.allowed_headers_str.split(",") if header.strip()]
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings instance."""
    return settings
