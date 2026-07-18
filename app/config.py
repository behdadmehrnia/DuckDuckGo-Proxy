from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8080
    api_key: str = ""

    default_max_results: int = 5
    search_timeout_sec: float = 8.0
    safesearch: str = "moderate"
    region: str = "wt-wt"
    backends: str = "duckduckgo"
    # Set false behind SSL-inspecting proxies (corporate MITM).
    verify_ssl: bool = True

    @property
    def auth_required(self) -> bool:
        return bool(self.api_key.strip())

    @property
    def backend_list(self) -> str:
        # ddgs accepts a comma-separated backend string
        return ",".join(
            part.strip() for part in self.backends.split(",") if part.strip()
        ) or "duckduckgo"


settings = Settings()
