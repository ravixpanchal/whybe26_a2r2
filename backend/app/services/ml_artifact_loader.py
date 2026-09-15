import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from app.config import Settings
from app.core.exceptions import ArtifactLoadError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadedArtifacts:
    model: Any
    metadata: dict[str, Any]
    preprocessing: Any | None


class MLArtifactLoader:
    """Loads and validates the configured artifact bundle once at startup."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._artifacts: LoadedArtifacts | None = None

    @property
    def artifacts(self) -> LoadedArtifacts | None:
        return self._artifacts

    def load(self) -> LoadedArtifacts:
        if self._artifacts is not None:
            return self._artifacts

        artifact_dir = self._settings.artifact_directory
        metadata_path = artifact_dir / self._settings.model_metadata_filename
        self._require_file(metadata_path)

        try:
            with metadata_path.open("r", encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ArtifactLoadError(
                f"Unable to read model metadata at {metadata_path}: {exc}"
            ) from exc

        preprocessing = None
        if self._settings.artifact_format == "portable":
            manifest_path = artifact_dir / self._settings.portable_manifest_filename
            self._require_file(manifest_path)
            try:
                from app.services.portable_ensemble import PortableSoftVotingEnsemble

                model = PortableSoftVotingEnsemble.from_manifest(manifest_path)
            except Exception as exc:
                raise ArtifactLoadError(
                    f"Unable to load portable model bundle at {manifest_path}: {exc}"
                ) from exc
            self._validate_metadata(metadata)
            self._artifacts = LoadedArtifacts(
                model=model,
                metadata=metadata,
                preprocessing=None,
            )
            logger.info("Loaded portable ML artifacts from %s", manifest_path)
            return self._artifacts
        if self._settings.artifact_format != "legacy_joblib":
            raise ArtifactLoadError(
                "ARTIFACT_FORMAT must be one of: legacy_joblib, portable"
            )

        model_path = artifact_dir / self._settings.model_filename
        self._require_file(model_path)
        preprocessing_path = artifact_dir / self._settings.preprocessing_filename
        if self._settings.preprocessing_mode == "separate":
            self._require_file(preprocessing_path)
        elif self._settings.preprocessing_mode not in {"embedded", "auto"}:
            raise ArtifactLoadError(
                "PREPROCESSING_MODE must be one of: separate, embedded, auto"
            )

        if self._settings.preprocessing_mode in {"separate", "auto"}:
            if preprocessing_path.exists():
                try:
                    preprocessing = joblib.load(preprocessing_path)
                except Exception as exc:
                    raise ArtifactLoadError(
                        f"Unable to load preprocessing artifact at "
                        f"{preprocessing_path}: {exc}"
                    ) from exc
            elif self._settings.preprocessing_mode == "separate":
                raise ArtifactLoadError(
                    f"Required preprocessing artifact is missing: {preprocessing_path}"
                )

        try:
            model = joblib.load(model_path)
        except Exception as exc:
            raise ArtifactLoadError(
                f"Unable to load model artifact at {model_path}: {exc}"
            ) from exc

        self._validate_metadata(metadata)
        if not callable(getattr(model, "predict", None)):
            raise ArtifactLoadError(f"Model artifact has no callable predict(): {model_path}")

        self._artifacts = LoadedArtifacts(
            model=model,
            metadata=metadata,
            preprocessing=preprocessing,
        )
        logger.info(
            "Loaded ML artifacts from %s (preprocessing_mode=%s)",
            artifact_dir,
            self._settings.preprocessing_mode,
        )
        return self._artifacts

    @staticmethod
    def _require_file(path: Path) -> None:
        if not path.is_file():
            raise ArtifactLoadError(f"Required ML artifact is missing: {path}")

    @staticmethod
    def _validate_metadata(metadata: object) -> None:
        if not isinstance(metadata, dict):
            raise ArtifactLoadError("Model metadata must be a JSON object")
        for key in ("target", "feature_count", "features"):
            if key not in metadata:
                raise ArtifactLoadError(f"Model metadata is missing required field: {key}")
        if metadata["target"] != "defaulted":
            raise ArtifactLoadError(
                f"Unsupported model target {metadata['target']!r}; expected 'defaulted'"
            )
        if metadata["feature_count"] != len(metadata["features"]):
            raise ArtifactLoadError("Model metadata feature_count does not match features")
