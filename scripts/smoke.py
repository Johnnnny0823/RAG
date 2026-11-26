import argparse
import json
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request, build_opener, install_opener, urlopen


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
    if web.startswith("https://"):
        expected = f"{web}/api/v1/health"
        with urlopen(f"{expected}/", timeout=5) as response:
            if response.url != expected or json.load(response) != {"status": "ok"}:
                raise ValueError("API redirect did not preserve the HTTPS origin")


def verify_rate_limits(web: str) -> None:
    for path, attempts in (("/auth/register", 10), ("/queries/analyze", 18)):
        reached_backend = False
        for _ in range(attempts):
            request = Request(
                f"{web}/api/v1{path}",
                data=b"{}",
                headers={"Content-Type": "application/json"},
            )
            try:
                with urlopen(request, timeout=3):
                    raise ValueError(f"{path} unexpectedly accepted the empty payload")
            except HTTPError as error:
                if error.code == 422:
                    reached_backend = True
                    continue
                if (
                    error.code != 429
                    or not reached_backend
                    or json.load(error)["error"]["code"] != "RATE_LIMITED"
                    or error.headers.get("Retry-After") != "2"
                    or error.headers.get("Cache-Control") != "no-store"
                    or not error.headers.get("Content-Security-Policy")
                ):
                    raise ValueError(
                        f"Unexpected rate-limit response for {path}"
                    ) from error
                break
        else:
            raise ValueError(f"No rate limit applied to {path}")

    if json.loads(read(f"{web}/api/v1/ready")) != {"status": "ready"}:
        raise ValueError("Readiness is unavailable during rate limiting")
    try:
        with urlopen(f"{web}/api/v1/search-jobs/active", timeout=3):
            raise ValueError("Search job status accepted an unauthenticated request")
    except HTTPError as error:
        if error.code != 401:
            raise ValueError("Search job status did not reach the API") from error


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--web", default="http://127.0.0.1:5173")
    parser.add_argument("--deployment", action="store_true")
    parser.add_argument("--deployment-rate-limit", action="store_true")
    parser.add_argument(
        "--ca-file", help="Trust an additional CA certificate for HTTPS"
    )
    args = parser.parse_args()
    if args.deployment_rate_limit and not args.deployment:
        parser.error("--deployment-rate-limit requires --deployment")
    if args.ca_file:
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=args.ca_file)
        install_opener(build_opener(HTTPSHandler(context=context)))

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
    if args.deployment_rate_limit:
        verify_rate_limits(args.web)
        print("Rate limit smoke passed: API error contract and unaffected status reads")
