from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresConfig(BaseModel):
    host: str | None = Field(default=None, validate_default=False)
    port: int | None = Field(default=None, validate_default=False)
    user: str | None = Field(default=None, validate_default=False)
    password: str | None = Field(default=None, validate_default=False)
    database: str | None = Field(default=None, validate_default=False)


class Options(BaseSettings):
    """
    XidpOptions is a class that contains the configuration for xidp.

    Attributes:
        model_config (SettingsConfigDict): The configuration for the model.
        devmode (DevMode): The configuration for development mode.
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="_", env_nested_max_split=1, env_prefix="xihr_"
    )
    postgres_config: PostgresConfig = Field(
        default=PostgresConfig(), validate_default=False
    )


class Config:
    options = Options()

    @classmethod
    def reload(cls):
        """
        Reload the configuration from the environment variables.

        two ways to set configuration:
            1. set environment variable:<br>
                e.g. export xihr_postgres_config_host="127.0.0.1"<br>
                or os.environ['xihr_postgres_config_host'] = "127.0.0.1"<br>
            2. directly set the variable:<br>
                e.g. Config.options.postgres_config.host = "127.0.0.1"

        Note:
            1. the environment variable name should start with "xihr_"
        """
        cls.options = Options()
