from pathlib import Path

from app.config import Settings


def test_cors_origins_are_parsed_from_a_comma_separated_value() -> None:
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000, https://example.test")

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://example.test",
    ]


def test_artifact_directory_is_configurable() -> None:
    settings = Settings(ARTIFACT_DIRECTORY="custom-artifacts")

    assert settings.artifact_directory == Path("custom-artifacts")


def test_portable_artifacts_are_the_default_format() -> None:
    assert Settings().artifact_format == "portable"
