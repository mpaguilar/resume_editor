import logging
from functools import lru_cache

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines all configuration values used by the application,
    including database connection details, security parameters, and API keys.
    Values are loaded from environment variables with fallback defaults.

    Attributes:
        database_url (PostgresDsn): Database connection URL for PostgreSQL.
            This is used to establish connection to the application's database.
        secret_key (str): Secret key for signing JWT tokens.
            Must be kept secure and changed in production.
        algorithm (str): Algorithm used for JWT token encoding.
            Currently uses HS256 (HMAC-SHA256).
        access_token_expire_minutes (int): Duration in minutes for which access tokens remain valid.
        llm_api_key (str | None): API key for accessing LLM services.
            Optional; used when LLM functionality is needed.
        encryption_key (str): Key used for encrypting sensitive data.

    """

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # Database settings
    db_host: str = Field(default="localhost", validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="DB_PORT")
    db_name: str = Field(default="resume_editor", validation_alias="DB_NAME")
    db_user: str = Field(default="postgres", validation_alias="DB_USER")
    db_password: str = Field(default="", validation_alias="DB_PASSWORD")

    @computed_field
    @property
    def database_url(self) -> PostgresDsn:
        """
        Assembled database URL from components.

        Args:
            None: This property does not take any arguments.

        Returns:
            PostgresDsn: The fully assembled PostgreSQL connection URL.

        Notes:
            1. Constructs the database URL using the components: scheme, username, password, host, port, and path.
            2. The scheme is set to "postgresql".
            3. The username, password, host, port, and database name are retrieved from the instance attributes.
            4. The resulting URL is returned as a PostgresDsn object.
            5. This function performs disk access to read the .env file at startup.

        """
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            path=self.db_name,
        )

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=120,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # API keys
    llm_api_key: str | None = Field(default=None, validation_alias="LLM_API_KEY")

    # Encryption key
    encryption_key: str = Field(validation_alias="ENCRYPTION_KEY")


@lru_cache
def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function returns a singleton instance of the Settings class,
    which contains all application configuration values.

    Args:
        None: This function does not take any arguments.

    Returns:
        Settings: The global settings instance, containing all configuration values.
            The instance is created by loading environment variables and applying defaults.

    Raises:
        ValidationError: If required environment variables are missing or invalid.
        ValueError: If the .env file cannot be read or parsed.

    Notes:
        1. Reads configuration from environment variables using the .env file.
        2. If environment variables are not set, default values are used.
        3. The Settings class uses Pydantic's validation and configuration features to ensure correct values.
        4. The function returns a cached instance to avoid repeated parsing of the .env file.
        5. This function performs disk access to read the .env file at startup.
        6. If the .env file is missing or cannot be read, a ValidationError may be raised.
        7. The function may raise a ValueError if required environment variables are not provided and no default is available.

    """
    return Settings()
