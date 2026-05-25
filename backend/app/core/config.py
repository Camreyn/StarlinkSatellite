from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Starlink Lifecycle Research"
    database_url: str = Field(default="sqlite:///./data/starlink_lifecycle.db")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    space_track_username: str | None = None
    space_track_password: str | None = None
    celestrak_starlink_gp_url: str = (
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json"
    )
    celestrak_starlink_tle_url: str = (
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
    )
    celestrak_satcat_url: str = "https://celestrak.org/pub/satcat.csv"
    planet4589_starlink_stats_url: str = "https://planet4589.org/space/con/star/stats.html"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlite_path(self) -> Path | None:
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            return Path(self.database_url.removeprefix(prefix))
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
