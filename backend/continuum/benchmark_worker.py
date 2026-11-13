"""Run one benchmark task inside a disposable Docker container."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .application import Application
from .config import Settings


def git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout


def prepare(row: dict, benchmark: str, workspace: Path) -> None:
    if benchmark == "swebench":
        repo = str(row["repo"])
        commit = str(row["base_commit"])
        if len(repo.split("/")) != 2 or not all(part.replace("-", "").replace("_", "").replace(".", "").isalnum() for part in repo.split("/")):
            raise ValueError("Invalid repository name")
        workspace.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--quiet", f"https://github.com/{repo}.git", str(workspace))
        git("checkout", "--quiet", commit, cwd=workspace)
    elif benchmark == "featurebench":
        prepare_featurebench(row, workspace)
    else:
        raise ValueError(benchmark)


def prepare_featurebench(row: dict, workspace: Path) -> None:
    """Match the public FeatureBench level 1/2 workspace and masking contract."""
    workspace.mkdir(parents=True, exist_ok=True)
    for item in workspace.iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()
    level = int(row.get("level", 1))
    if level == 1:
        source = Path("/root/my_repo")
        if not source.is_dir():
            raise FileNotFoundError("FeatureBench image is missing /root/my_repo")
        for item in source.iterdir():
            if item.name.startswith("."):
                continue
            target = workspace / item.name
            if item.is_dir() and not item.is_symlink():
                shutil.copytree(item, target, symlinks=True)
            elif item.is_symlink():
                target.symlink_to(os.readlink(item))
            else:
                shutil.copy2(item, target)
        shutil.rmtree(source)
        mask = row.get("patch") or ""
        if mask:
            subprocess.run(["git", "apply", "--whitespace=fix", "-"], input=mask,
                           cwd=workspace, text=True, capture_output=True, check=True)
        for raw in row.get("FAIL_TO_PASS") or []:
            candidate = (workspace / raw.removeprefix("/testbed/")).resolve()
            if not candidate.is_relative_to(workspace.resolve()):
                raise ValueError(f"Test path escapes FeatureBench workspace: {raw}")
            if candidate.is_file():
                candidate.unlink()
        for cache in workspace.rglob("__pycache__"):
            if cache.is_dir():
                shutil.rmtree(cache)
        for pattern in ("*.pyc", "*.pyo"):
            for bytecode in workspace.rglob(pattern):
                bytecode.unlink()
    elif level == 2:
        shutil.rmtree(Path("/root/my_repo"), ignore_errors=True)
        (workspace / "README.md").write_text("put all codes in this folder\n", encoding="utf-8")
    else:
        raise ValueError(f"Unsupported FeatureBench level: {level}")
    git("init", "-q", cwd=workspace)
    git("add", "-A", cwd=workspace)
    git("-c", "user.name=FeatureBench", "-c", "user.email=fb@bench.com",
        "commit", "-q", "--allow-empty", "-m", "Initial commit for FeatureBench evaluation", cwd=workspace)


def collect_patch(workspace: Path) -> str:
    git("add", "-N", "--all", cwd=workspace)
    return git("diff", "--binary", "HEAD", "--", ".", cwd=workspace)


async def run(row: dict, benchmark: str) -> dict:
    workspace = Path(os.environ["CONTINUUM_WORKSPACE_DIR"])
    prepare(row, benchmark, workspace)
    settings = Settings()
    app = Application(settings)
    await app.start()
    error = None
    try:
        conversation = (await app.conversation_create({"title": str(row["instance_id"])}))["conversation"]
        prompt = str(row["problem_statement"])
        result = await app.conversation_send({"conversation_id": conversation["id"], "content": prompt})
        if result["result"].get("stop_reason") not in (None, "completed"):
            error = str(result["result"].get("stop_reason"))
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        await app.close()
    patch = collect_patch(workspace)
    output = {"instance_id": row["instance_id"], "model_patch": patch}
    if benchmark == "swebench":
        output["model_name_or_path"] = f"Continuum/{settings.model}"
    else:
        output.update(agent="continuum", model=settings.model, n_attempt=1,
                      task_metadata={}, success=error is None, error=error, agent_exit_status="completed" if error is None else "failed")
    if error:
        print(error, file=sys.stderr)
    return output


def main() -> None:
    if os.environ.get("CONTINUUM_BENCHMARK_CONTAINER") != "true":
        raise SystemExit("benchmark worker requires a disposable benchmark container")
    payload = json.load(sys.stdin)
    result = asyncio.run(run(payload["row"], payload["benchmark"]))
    print("CONTINUUM_BENCH_RESULT=" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
