#!/usr/bin/env python3
"""
Linktivity GDS API signature helper.

Three subcommands:

  sign    Compute the signature-key for a request. Prints the header block.
  verify  Compare a client's signature against the expected value, and
          diagnose the most common chain mistakes when they don't match.
  call    Issue a signed request and print the response.

The API key secret is read from the GDS_API_KEY environment variable, or from
--api-key. Prefer the environment variable so the secret stays out of shell
history and process listings.

Examples
--------
  export GDS_API_KEY='...'

  # What headers should I be sending?
  ./gds_sign.py sign --host open-agent.gds-neo.link-dev.link \\
                     --path /v1/activity/search-activities

  # Client produced a signature that the server rejects. Why?
  ./gds_sign.py verify --host open-agent.gds-neo.link-dev.link \\
                       --path /v1/activity/search-activities \\
                       --timestamp 20260521T063324Z \\
                       --signature '3gjtSDLmvsr4M6RdQ9vY5sYPZ1Y7iV...='

  # Actually hit the sandbox.
  ./gds_sign.py call --env sandbox \\
                     --path /v1/partner/list-suppliers \\
                     --ota-id LINKTIVITY \\
                     --group-id '[default-group]:LINKTIVITY' \\
                     --api-key-id VJgSBDVXXXXXXXXX

  # POST with a body.
  ./gds_sign.py call --env sandbox --method POST \\
                     --path /v1/booking/ota/final-booking \\
                     --ota-id LINKTIVITY --group-id '[default-group]:LINKTIVITY' \\
                     --api-key-id VJgSBDVXXXXXXXXX \\
                     --body-file final_booking.json
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PREFIX_SALT = "congaree"
SUFFIX_SALT = "veltra"

ENVIRONMENTS = {
    "sandbox": "open-agent.gds-neo.link-dev.link",
    "production": "open-agent.gds-neo.linktivity.io",
}

TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


# ---------------------------------------------------------------- core algorithm


def _hmac(key: bytes, msg: bytes) -> bytes:
    """One HMAC-SHA256 step, returning the 32 raw digest bytes."""
    return hmac.new(key, msg, hashlib.sha256).digest()


def signature_key(api_key: str, timestamp: str, host: str, path: str) -> str:
    """The documented chained-HMAC signature, base64-url encoded with padding."""
    k1 = _hmac((PREFIX_SALT + api_key).encode(), timestamp.encode())
    k2 = _hmac(k1, host.encode())
    k3 = _hmac(k2, path.encode())
    k = _hmac(k3, SUFFIX_SALT.encode())
    return base64.urlsafe_b64encode(k).decode()


def utc_timestamp() -> str:
    return time.strftime(TIMESTAMP_FORMAT, time.gmtime())


# ---------------------------------------------------------------- normalisation


def normalise_host(host: str) -> tuple[str, list[str]]:
    """Strip what must not be in the signed host. Returns (host, warnings)."""
    warnings: list[str] = []
    original = host.strip()
    host = original
    had_scheme = "://" in host
    if had_scheme:
        host = host.split("://", 1)[1]
    host = host.rstrip("/")
    had_path = "/" in host
    if had_path:
        host = host.split("/", 1)[0]
    if had_scheme:
        warnings.append(
            f"host contained a scheme ({original!r}); the signed host must be the "
            f"bare hostname. Using {host!r}."
        )
    if had_path:
        warnings.append(f"host contained a path; using {host!r}.")
    if ":" in host:
        warnings.append(
            f"host contains a port ({host!r}). The documented signing input is the "
            "hostname only — remove the port if the server rejects the signature."
        )
    return host, warnings


def normalise_path(path: str) -> tuple[str, list[str]]:
    """Strip query/fragment and ensure a leading slash. Returns (path, warnings)."""
    warnings: list[str] = []
    original = path
    if "#" in path:
        path = path.split("#", 1)[0]
        warnings.append("path contained a fragment; removed it before signing.")
    if "?" in path:
        path = path.split("?", 1)[0]
        warnings.append(
            f"path contained a query string ({original!r}); the signature covers the "
            f"path only. Using {path!r}."
        )
    if not path.startswith("/"):
        path = "/" + path
        warnings.append(f"path had no leading slash; using {path!r}.")
    if len(path) > 1 and path.endswith("/"):
        warnings.append(
            f"path has a trailing slash ({path!r}). Sign the path exactly as it appears "
            "in the request line — a trailing slash the server does not expect will "
            "cause a mismatch."
        )
    return path, warnings


def resolve_host(args) -> tuple[str, list[str]]:
    if getattr(args, "env", None):
        if args.env not in ENVIRONMENTS:
            sys.exit(f"unknown --env {args.env!r}; choose from {', '.join(ENVIRONMENTS)}")
        return ENVIRONMENTS[args.env], []
    if not getattr(args, "host", None):
        sys.exit("one of --host or --env is required")
    return normalise_host(args.host)


def resolve_api_key(args) -> str:
    key = getattr(args, "api_key", None) or os.environ.get("GDS_API_KEY")
    if not key:
        sys.exit(
            "API key secret not found. Set GDS_API_KEY in the environment, or pass "
            "--api-key (less safe — it lands in shell history)."
        )
    stripped = key.strip()
    if stripped != key:
        print(
            "warning: the API key had surrounding whitespace, which is a common "
            "copy-paste error. Using the stripped value.",
            file=sys.stderr,
        )
    return stripped


def emit_warnings(warnings: list[str]) -> None:
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)


# ---------------------------------------------------------------- subcommands


def cmd_sign(args) -> int:
    api_key = resolve_api_key(args)
    host, hw = resolve_host(args)
    path, pw = normalise_path(args.path)
    emit_warnings(hw + pw)

    timestamp = args.timestamp or utc_timestamp()
    sig = signature_key(api_key, timestamp, host, path)

    if args.json:
        print(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "signature-key": sig,
                    "signed_host": host,
                    "signed_path": path,
                },
                indent=2,
            )
        )
        return 0

    print(f"signed host : {host}")
    print(f"signed path : {path}")
    print()
    print(f"timestamp: {timestamp}")
    print(f"signature-key: {sig}")
    if args.ota_id or args.group_id or args.api_key_id:
        print()
        print("curl headers:")
        for name, value in (
            ("ota-id", args.ota_id),
            ("group-id", args.group_id),
            ("api-key-id", args.api_key_id),
            ("timestamp", timestamp),
            ("signature-key", sig),
        ):
            if value:
                print(f"  --header '{name}: {value}' \\")
    return 0


def _diagnostic_variants(api_key: str, timestamp: str, host: str, path: str) -> dict[str, str]:
    """
    Recreate the signature under each common implementation mistake, so a mismatched
    client signature can be attributed to a specific bug rather than guessed at.
    """
    variants: dict[str, str] = {}

    def chain(steps_hex: bool = False, prefix: str = PREFIX_SALT,
              suffix: str = SUFFIX_SALT, ts: str = None, h: str = None,
              p: str = None) -> bytes:
        ts = timestamp if ts is None else ts
        h = host if h is None else h
        p = path if p is None else p
        k1 = _hmac((prefix + api_key).encode(), ts.encode())
        if steps_hex:
            k1 = binascii.hexlify(k1)
        k2 = _hmac(k1, h.encode())
        if steps_hex:
            k2 = binascii.hexlify(k2)
        k3 = _hmac(k2, p.encode())
        if steps_hex:
            k3 = binascii.hexlify(k3)
        return _hmac(k3, suffix.encode())

    raw = chain()
    variants["standard base64 instead of URL-safe"] = base64.b64encode(raw).decode()
    variants["padding stripped from the output"] = (
        base64.urlsafe_b64encode(raw).decode().rstrip("=")
    )
    variants["hex output instead of base64"] = binascii.hexlify(raw).decode()
    variants["hex-encoded intermediates between chain steps"] = (
        base64.urlsafe_b64encode(chain(steps_hex=True)).decode()
    )
    variants["scheme left on the host"] = base64.urlsafe_b64encode(
        chain(h="https://" + host)
    ).decode()
    variants["trailing slash on the path"] = base64.urlsafe_b64encode(
        chain(p=path.rstrip("/") + "/")
    ).decode()
    variants["salts swapped (veltra first, congaree last)"] = base64.urlsafe_b64encode(
        chain(prefix=SUFFIX_SALT, suffix=PREFIX_SALT)
    ).decode()
    variants["prefix salt omitted from the key"] = base64.urlsafe_b64encode(
        chain(prefix="")
    ).decode()

    # msg/key transposed at every step -- the classic error when porting between
    # languages whose HMAC helpers take (key, msg) vs (msg, key).
    def swapped() -> bytes:
        k1 = _hmac(timestamp.encode(), (PREFIX_SALT + api_key).encode())
        k2 = _hmac(host.encode(), k1)
        k3 = _hmac(path.encode(), k2)
        return _hmac(SUFFIX_SALT.encode(), k3)

    variants["msg and key arguments transposed"] = base64.urlsafe_b64encode(
        swapped()
    ).decode()
    return variants


def cmd_verify(args) -> int:
    api_key = resolve_api_key(args)
    host, hw = resolve_host(args)
    path, pw = normalise_path(args.path)
    emit_warnings(hw + pw)

    timestamp = args.timestamp
    expected = signature_key(api_key, timestamp, host, path)
    given = args.signature.strip()

    print(f"signed host   : {host}")
    print(f"signed path   : {path}")
    print(f"timestamp     : {timestamp}")
    print(f"expected      : {expected}")
    print(f"client sent   : {given}")
    print()

    if hmac.compare_digest(expected, given):
        print("MATCH — the signature is correct.")
        print()
        print("If the server still returns 401, the cause is elsewhere:")
        print("  - the timestamp header does not carry this exact string")
        print("  - the clock is more than +/-5 minutes off server time")
        print("  - api-key-id, ota-id or group-id is wrong or missing")
        print("  - sandbox credentials are being sent to production, or vice versa")
        return 0

    print("MISMATCH.")
    for label, value in _diagnostic_variants(api_key, timestamp, host, path).items():
        if hmac.compare_digest(value, given):
            print()
            print(f"Cause identified: {label}.")
            print("Fix that and the signature will match.")
            return 1

    print()
    print("Not explained by any of the common implementation mistakes. The most likely")
    print("remaining causes, in order:")
    print("  1. The secret is wrong. Confirm you are using the API key SECRET and not")
    print("     the api-key-id header value -- they are different values.")
    print("  2. The secret belongs to the other environment (sandbox vs production).")
    print("  3. The timestamp string used for signing differs from the header value.")
    print("  4. The path signed differs from the request line (encoding, case, slash).")
    print("Then escalate to info@linktivity.co.jp with the timestamp, path, and environment.")
    return 1


def cmd_call(args) -> int:
    api_key = resolve_api_key(args)
    host, hw = resolve_host(args)
    path, pw = normalise_path(args.path)
    emit_warnings(hw + pw)

    for name, value in (
        ("--ota-id", args.ota_id),
        ("--group-id", args.group_id),
        ("--api-key-id", args.api_key_id),
    ):
        if not value:
            sys.exit(f"{name} is required for `call`")

    body: bytes | None = None
    if args.body_file:
        with open(args.body_file, "rb") as fh:
            body = fh.read()
    elif args.body:
        body = args.body.encode()

    method = args.method.upper()
    if body and method == "GET":
        print("warning: a body was supplied with GET; switching to POST.", file=sys.stderr)
        method = "POST"

    url = f"https://{host}{path}"
    if args.query:
        # Signature covers the path only, so query params are appended after signing.
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{args.query.lstrip('?&')}"

    timestamp = args.timestamp or utc_timestamp()
    sig = signature_key(api_key, timestamp, host, path)

    headers = {
        "ota-id": args.ota_id,
        "group-id": args.group_id,
        "api-key-id": args.api_key_id,
        "timestamp": timestamp,
        "signature-key": sig,
    }
    if body:
        headers["Content-Type"] = "application/json"

    if args.verbose:
        print(f"{method} {url}", file=sys.stderr)
        for k, v in headers.items():
            print(f"  {k}: {v}", file=sys.stderr)
        print(file=sys.stderr)

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            status = resp.status
            payload = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = exc.read().decode("utf-8", "replace")
    except urllib.error.URLError as exc:
        sys.exit(f"request failed: {exc.reason}")

    print(f"HTTP {status}", file=sys.stderr)
    try:
        print(json.dumps(json.loads(payload), indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(payload)

    if status >= 400:
        print(
            "\nNon-2xx. For 401 see references/auth.md; otherwise read `details[]` in the "
            "rpc.Status body — it usually names the offending field. "
            "references/troubleshooting.md maps codes to causes.",
            file=sys.stderr,
        )
        return 1
    return 0


# ---------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Linktivity GDS API signature helper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--api-key", help="API key secret. Prefer $GDS_API_KEY.")
        group = p.add_mutually_exclusive_group()
        group.add_argument("--host", help="Bare request host, no scheme.")
        group.add_argument("--env", choices=sorted(ENVIRONMENTS),
                           help="Resolve the host from a known environment.")
        p.add_argument("--path", required=True,
                       help="Request path, e.g. /v1/activity/search-activities")

    p_sign = sub.add_parser("sign", help="Compute the signature-key header.")
    add_common(p_sign)
    p_sign.add_argument("--timestamp", help="Override the timestamp (YYYYMMDDTHHMMSSZ).")
    p_sign.add_argument("--ota-id")
    p_sign.add_argument("--group-id")
    p_sign.add_argument("--api-key-id")
    p_sign.add_argument("--json", action="store_true", help="Emit JSON.")
    p_sign.set_defaults(func=cmd_sign)

    p_verify = sub.add_parser(
        "verify",
        help="Compare a client's signature against the expected value and diagnose it.",
    )
    add_common(p_verify)
    p_verify.add_argument("--timestamp", required=True,
                          help="The exact timestamp the client used.")
    p_verify.add_argument("--signature", required=True,
                          help="The signature-key the client produced.")
    p_verify.set_defaults(func=cmd_verify)

    p_call = sub.add_parser("call", help="Issue a signed request.")
    add_common(p_call)
    p_call.add_argument("--method", default="GET")
    p_call.add_argument("--query", help="Query string, appended after signing.")
    p_call.add_argument("--body", help="Request body as a JSON string.")
    p_call.add_argument("--body-file", help="Request body read from a file.")
    p_call.add_argument("--timestamp")
    p_call.add_argument("--ota-id")
    p_call.add_argument("--group-id")
    p_call.add_argument("--api-key-id")
    p_call.add_argument("--timeout", type=float, default=30.0)
    p_call.add_argument("-v", "--verbose", action="store_true",
                        help="Print the request line and headers to stderr.")
    p_call.set_defaults(func=cmd_call)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
