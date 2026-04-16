from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


load_dotenv()


TRUE_VALUES = {"1", "true", "yes", "on"}


class ConfigError(RuntimeError):
    """Raised when application configuration is invalid."""


@dataclass(frozen=True)
class EnvValue:
    name: str
    default: str | None = None
    required: bool = False
    allow_blank: bool = False


def _get_env(spec: EnvValue) -> str:
    value = os.getenv(spec.name, spec.default)
    if value is None:
        if spec.required:
            raise ConfigError(f"Missing required environment variable: {spec.name}")
        return ""

    value = value.strip()
    if not value and not spec.allow_blank and spec.required:
        raise ConfigError(f"Environment variable {spec.name} must not be empty")
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


class BaseConfig:
    TESTING = False
    DEBUG = False

    SECRET_KEY = _get_env(EnvValue("SECRET_KEY", "dev-secret-key"))
    JWT_SECRET_KEY = _get_env(EnvValue("JWT_SECRET_KEY", "dev-jwt-secret-key"))

    SQLALCHEMY_DATABASE_URI = _get_env(
        EnvValue(
            "DATABASE_URL",
            "sqlite+pysqlite:///schedule_system.db" if _get_bool("USE_SQLITE_DEV_DB") else "postgresql://admin:password@localhost:5432/schedule_system",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    KEYCLOAK_PUBLIC_URL = _get_env(EnvValue("KEYCLOAK_PUBLIC_URL", "http://localhost:8081"))
    KEYCLOAK_INTERNAL_URL = _get_env(EnvValue("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080"))
    KEYCLOAK_REALM = _get_env(EnvValue("KEYCLOAK_REALM", "maga-school"))
    KEYCLOAK_CLIENT_ID = _get_env(EnvValue("KEYCLOAK_CLIENT_ID", "maga-backend"))
    KEYCLOAK_CLIENT_SECRET = _get_env(EnvValue("KEYCLOAK_CLIENT_SECRET", "", allow_blank=True))
    KEYCLOAK_AUDIENCE = _get_env(EnvValue("KEYCLOAK_AUDIENCE", "account"))

    KEYCLOAK_ISSUER = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}"
    KEYCLOAK_JWKS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
    KEYCLOAK_WELL_KNOWN_URL = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"

    @classmethod
    def validate(cls) -> None:
        database_uri = str(getattr(cls, "SQLALCHEMY_DATABASE_URI", "") or "").strip()
        if not database_uri:
            raise ConfigError("SQLALCHEMY_DATABASE_URI must not be empty")

        for attr in ("KEYCLOAK_PUBLIC_URL", "KEYCLOAK_INTERNAL_URL", "KEYCLOAK_REALM", "KEYCLOAK_CLIENT_ID"):
            value = str(getattr(cls, attr, "") or "").strip()
            if not value:
                raise ConfigError(f"{attr} must not be empty")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _get_env(EnvValue("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:"))
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    DEBUG = False

    SECRET_KEY = _get_env(EnvValue("SECRET_KEY", required=True))
    JWT_SECRET_KEY = _get_env(EnvValue("JWT_SECRET_KEY", required=True))
    SQLALCHEMY_DATABASE_URI = _get_env(EnvValue("DATABASE_URL", required=True))
    KEYCLOAK_PUBLIC_URL = _get_env(EnvValue("KEYCLOAK_PUBLIC_URL", required=True))
    KEYCLOAK_INTERNAL_URL = _get_env(EnvValue("KEYCLOAK_INTERNAL_URL", required=True))
    KEYCLOAK_REALM = _get_env(EnvValue("KEYCLOAK_REALM", required=True))
    KEYCLOAK_CLIENT_ID = _get_env(EnvValue("KEYCLOAK_CLIENT_ID", required=True))
    KEYCLOAK_CLIENT_SECRET = _get_env(EnvValue("KEYCLOAK_CLIENT_SECRET", required=True))
    KEYCLOAK_AUDIENCE = _get_env(EnvValue("KEYCLOAK_AUDIENCE", default="account"))

    @classmethod
    def validate(cls) -> None:
        super().validate()

        insecure_values = {
            "dev-secret-key",
            "dev-jwt-secret-key",
            "postgresql://admin:password@localhost:5432/schedule_system",
        }
        values_to_check: dict[str, Any] = {
            "SECRET_KEY": cls.SECRET_KEY,
            "JWT_SECRET_KEY": cls.JWT_SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI": cls.SQLALCHEMY_DATABASE_URI,
        }
        for key, value in values_to_check.items():
            if str(value).strip() in insecure_values:
                raise ConfigError(f"{key} uses an insecure development default in production")


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "test": TestConfig,
    "testing": TestConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
}


Config = DevelopmentConfig


def resolve_config(config_object: type | str | None = None) -> type:
    if config_object is None:
        env_name = os.getenv("FLASK_ENV", os.getenv("APP_ENV", "development")).strip().lower()
        return CONFIG_BY_NAME.get(env_name, DevelopmentConfig)

    if isinstance(config_object, str):
        return CONFIG_BY_NAME.get(config_object.strip().lower(), DevelopmentConfig)

    return config_object
