from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YAP_")
    data_dir: Path = Path(__file__).resolve().parents[1] / "data"
    db_path: Path | None = None
    inbox_dir: Path | None = None

    def model_post_init(self, __context) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.db_path is None:
            self.db_path = self.data_dir / "app.db"
        if self.inbox_dir is None:
            self.inbox_dir = self.data_dir / "inbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
