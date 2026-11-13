from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _path(name: str, default: Path) -> Path:
    raw = os.getenv(name, "").strip()
    return Path(raw).expanduser().resolve() if raw else default.resolve()


@dataclass(frozen=True)
class Settings:
    """集中读取环境配置；数据目录与工作目录可分别覆盖。"""

    provider: str = os.getenv("CONTINUUM_PROVIDER", "openai")
    model: str = os.getenv("CONTINUUM_MODEL", "gpt-4.1-mini")
    api_key: str = os.getenv("CONTINUUM_API_KEY", "")
    base_url: str = os.getenv("CONTINUUM_BASE_URL", "https://api.openai.com/v1")
    search_provider: str = os.getenv("CONTINUUM_SEARCH_PROVIDER", "auto")
    tavily_api_key: str = os.getenv("CONTINUUM_TAVILY_API_KEY", "")
    http_allow_private_network: bool = os.getenv("CONTINUUM_HTTP_ALLOW_PRIVATE_NETWORK", "false").lower() == "true"
    host: str = os.getenv("CONTINUUM_HOST", "127.0.0.1")
    port: int = int(os.getenv("CONTINUUM_PORT", "8765"))
    data_dir: Path = _path("CONTINUUM_DATA_DIR", ROOT / ".continuum")
    user_skills_dir: Path = _path("CONTINUUM_USER_SKILLS_DIR", Path.home() / ".continuum" / "skills")
    workspace_dir: Path = _path("CONTINUUM_WORKSPACE_DIR", ROOT / "workspace")
    web_dir: Path | None = (
        _path("CONTINUUM_WEB_DIR", ROOT / "web") if os.getenv("CONTINUUM_WEB_DIR", "").strip() else None
    )
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CONTINUUM_ALLOWED_ORIGINS", "http://localhost:8765,http://127.0.0.1:8765").split(",")
        if origin.strip()
    )
    computer_enabled: bool = os.getenv("CONTINUUM_COMPUTER_ENABLED", "false").lower() == "true"
    # Only the one-task benchmark container may bypass the macOS Seatbelt requirement.
    benchmark_container: bool = (
        os.getenv("CONTINUUM_BENCHMARK_CONTAINER", "false").lower() == "true"
        and Path(sys.argv[0]).name == "benchmark_worker.py"
    )
    max_steps: int = int(os.getenv("CONTINUUM_MAX_STEPS", "12"))
    run_warning_tokens: int = int(os.getenv("CONTINUUM_RUN_WARNING_TOKENS", "80000"))
    run_finalization_tokens: int = int(os.getenv("CONTINUUM_RUN_FINALIZATION_TOKENS", "100000"))
    run_hard_tokens: int = int(os.getenv("CONTINUUM_RUN_HARD_TOKENS", "120000"))
    run_warning_model_calls: int = int(os.getenv("CONTINUUM_RUN_WARNING_MODEL_CALLS", "16"))
    run_finalization_model_calls: int = int(os.getenv("CONTINUUM_RUN_FINALIZATION_MODEL_CALLS", "20"))
    run_hard_model_calls: int = int(os.getenv("CONTINUUM_RUN_HARD_MODEL_CALLS", "24"))

    @property
    def database(self) -> Path:
        return self.data_dir / "continuum.db"

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.workspace_dir,
            self.data_dir / "artifacts",
            self.data_dir / "memory",
            self.data_dir / "skills",
            self.data_dir / "screenshots",
            self.data_dir / "settings",
        ):
            path.mkdir(parents=True, exist_ok=True)
