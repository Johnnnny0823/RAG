import argparse
import json
import time
from urllib.error import URLError
from urllib.request import urlopen


def read(url: str) -> str:
    with urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8")


def smoke(api: str, web: str) -> None:
    if json.loads(read(f"{api}/api/v1/health")) != {"status": "ok"}:
        raise ValueError("Unexpected liveness response")
    if json.loads(read(f"{web}/api/v1/ready")) != {"status": "ready"}:
        raise ValueError("Unexpected readiness response through web proxy")
    if '<html lang="zh-Hant">' not in read(web):
        raise ValueError("Unexpected web entry page")


def verify_deployment(web: str) -> None:
    expected_csp = {
        "default-src 'self'",
        "base-uri 'none'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
    }
    with urlopen(web, timeout=5) as response:
        csp = {
            part.strip()
            for part in response.headers.get("Content-Security-Policy", "").split(";")
        }
        if csp != expected_csp:
            raise ValueError("Unexpected deployment content security policy")
        if (
            response.headers.get("X-Content-Type-Options") != "nosniff"
            or response.headers.get("Referrer-Policy") != "no-referrer"
        ):
            raise ValueError("Unexpected deployment browser security headers")
        if "/@vite/client" in response.read().decode("utf-8"):
            raise ValueError("Deployment uses the Vite development page")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--web", default="http://127.0.0.1:5173")
    parser.add_argument("--deployment", action="store_true")
    args = parser.parse_args()

    deadline = time.monotonic() + 45
    while True:
        try:
            smoke(args.api, args.web)
            if args.deployment:
                verify_deployment(args.web)
        except (OSError, URLError, ValueError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)
        else:
            print(
                "Smoke passed: API liveness, pgvector readiness via web proxy, web entry page"
            )
            if args.deployment:
                print("Deployment smoke passed: packaged frontend and security headers")
            break
