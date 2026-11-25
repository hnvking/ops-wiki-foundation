#!/usr/bin/env python3
"""一键启动整套服务：WeKnora + 知识库 Wiki + MCP。

用法：
    python start_all.py

按 Ctrl+C 停止全部由本脚本启动的进程。PostgreSQL / Redis 由 Docker Desktop
承载，脚本只负责启动容器，不会启动 Docker Desktop 本身。
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEKNORA = ROOT / "weknora" / "WeKnora"
LOGS = ROOT / ".workbuddy" / "logs"
PID_FILE = ROOT / ".workbuddy" / "service_pids.json"
PYTHON = sys.executable
NPM = shutil.which("npm") or "npm"

SERVICES = [
    {
        "name": "weknora-backend",
        "cmd": [PYTHON, "-X", "utf8", str(ROOT / "weknora" / "run_server.py")],
        "cwd": WEKNORA,
        "url": "http://127.0.0.1:8080/health",
        "env": {},
    },
    {
        "name": "weknora-frontend",
        "cmd": [NPM, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        "cwd": WEKNORA / "frontend",
        "url": "http://127.0.0.1:5173",
        "env": {},
    },
    {
        "name": "wiki-backend",
        "cmd": [PYTHON, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "cwd": ROOT,
        "url": "http://127.0.0.1:8000/api/health",
        "env": {},
    },
    {
        "name": "wiki-mcp",
        "cmd": [PYTHON, str(ROOT / "mcp_server.py")],
        "cwd": ROOT,
        "url": "http://127.0.0.1:8001/mcp",
        "env": {
            "WIKI_BASE_URL": "http://127.0.0.1:8000",
            "WIKI_MCP_HOST": "127.0.0.1",
            "WIKI_MCP_PORT": "8001",
        },
    },
]


def start_infra():
    env_file = WEKNORA / ".env"
    compose = WEKNORA / "docker-compose.dev.yml"
    if not env_file.exists() or not compose.exists():
        raise SystemExit(f"缺少 {env_file} 或 {compose}，无法启动数据库容器")
    print("启动 PostgreSQL / Redis 容器…", flush=True)
    result = subprocess.run(
        ["docker", "compose", "--env-file", str(env_file), "-f", str(compose),
         "up", "-d", "postgres", "redis"],
        cwd=str(WEKNORA), check=False,
    )
    if result.returncode != 0:
        raise SystemExit("Docker 容器启动失败。先启动 Docker Desktop，再重跑本脚本。")


def main():
    start_infra()
    LOGS.mkdir(parents=True, exist_ok=True)
    procs = {}
    for service in SERVICES:
        log_path = LOGS / f"{service['name']}.log"
        log = open(log_path, "w", encoding="utf-8")
        env = os.environ.copy()
        env.update(service["env"])
        proc = subprocess.Popen(
            service["cmd"], cwd=str(service["cwd"]), env=env,
            stdout=log, stderr=subprocess.STDOUT,
        )
        procs[service["name"]] = proc
        print(f"启动 {service['name']}  PID={proc.pid}  日志={log_path}", flush=True)
        time.sleep(1)

    PID_FILE.write_text(
        json.dumps({name: proc.pid for name, proc in procs.items()}, indent=2),
        encoding="utf-8",
    )
    print("\n服务地址：")
    for service in SERVICES:
        print(f"  {service['name']:18} {service['url']}")
    print("\n按 Ctrl+C 停止全部服务。", flush=True)

    try:
        while True:
            for name, proc in procs.items():
                if proc.poll() is not None:
                    print(f"警告：{name} 已退出，退出码 {proc.returncode}", flush=True)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n停止全部服务…", flush=True)
        for name, proc in procs.items():
            if proc.poll() is None:
                proc.terminate()
        for name, proc in procs.items():
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("已全部停止。", flush=True)


if __name__ == "__main__":
    main()
