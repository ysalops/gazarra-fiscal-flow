from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GAZARRA POC"
    database_url: str = "postgresql+psycopg://gazarra:gazarra@db:5432/gazarra"
    llm_provider: str = "none"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    cors_origins: str = "http://localhost:8080"

    # Autenticação local da POC. Trocar AUTH_SECRET antes de qualquer publicação.
    auth_secret: str = "CHANGE-ME-GAZARRA-LOCAL-ONLY"
    auth_token_hours: int = 10
    seed_demo_users: bool = True
    demo_admin_email: str = "admin@gazarra.local"
    demo_admin_password: str = "Gazarra@123"
    demo_analyst_email: str = "analista@gazarra.local"
    demo_analyst_password: str = "Analista@123"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
