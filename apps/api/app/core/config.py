from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+psycopg://rgp:rgp@localhost:5432/rgp"
    sqlite_fallback_url: str = "sqlite:///./rgp.db"
    redis_url: str = "redis://localhost:6379/0"
    check_dispatch_backend: str = "local"
    auth_mode: str = "local"
    auth_token_secret: str = "rgp-dev-secret"
    allow_dev_auth_fallback: bool = False
    allow_dev_token_issuance: bool = True
    auth_jwks_url: str | None = None
    auth_jwt_issuer: str | None = None
    auth_jwt_audience: str | None = None
    runtime_callback_secret: str = "rgp-runtime-secret"
    runtime_callback_hmac_secret: str = "rgp-runtime-hmac-secret"
    runtime_callback_max_skew_seconds: int = 300
    runtime_adapter_base_url: str | None = None
    deployment_adapter_base_url: str | None = None
    integration_secret_key: str | None = None
    integration_allow_http_loopback: bool = True
    integration_openai_allowed_hosts: list[str] = ["api.openai.com"]
    integration_anthropic_allowed_hosts: list[str] = ["api.anthropic.com"]
    integration_microsoft_allowed_hosts: list[str] = ["graph.microsoft.com"]
    integration_runtime_allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    integration_deployment_allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    event_bus_enabled: bool = False
    event_bus_backend: str = "outbox"
    event_bus_topic_prefix: str = "rgp"
    event_bus_http_endpoint: str | None = None
    telemetry_enabled: bool = True
    telemetry_service_name: str = "rgp-api"
    telemetry_exporter: str = "console"
    telemetry_otlp_endpoint: str | None = None
    performance_latency_slo_ms: int = 1000
    performance_availability_slo_percent: float = 99.0
    object_store_backend: str = "filesystem"
    object_store_root: str = "/Volumes/data/development/rgp/.rgp-object-store"
    agent_provider_fallback_mode: str = "simulate"
    agent_openai_api_key: str | None = None
    agent_openai_base_url: str = "https://api.openai.com/v1"
    agent_openai_model: str = "gpt-5.4"
    agent_anthropic_api_key: str | None = None
    agent_anthropic_base_url: str = "https://api.anthropic.com/v1"
    agent_anthropic_model: str = "claude-sonnet-4-5"
    agent_anthropic_max_tokens: int = 1024
    agent_microsoft_copilot_token: str | None = None
    agent_microsoft_copilot_base_url: str = "https://graph.microsoft.com/beta/copilot"

    model_config = SettingsConfigDict(
        env_prefix="RGP_",
        extra="ignore",
    )


settings = Settings()
