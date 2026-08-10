#!/usr/bin/env python3
"""
Download the Linktivity GDS API OpenAPI spec into this skill's assets/ directory.

Run once after installing the skill. Afterwards SKILL.md will prefer the local copy
as the authoritative source for exact field names, types, and required flags, and the
skill works with no network access.

    python3 scripts/fetch_spec.py

The download is validated before it is written: it must parse as JSON, be Swagger 2.0,
and contain all 14 documented operations and a set of definitions the reference files
depend on. A truncated or proxy-mangled response is rejected rather than silently
trusted — a partial spec presented as authoritative is worse than none.

Options:
    --url URL     Override the source URL.
    --output PATH Override the destination (default: assets/gds_api.swagger.json).
    --force       Overwrite an existing file without asking.
    --check       Validate the existing local copy and exit; download nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = (
    "https://linktivity.github.io/gds-neo-proto-public/apidoc/gds_api.swagger.json"
)

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "gds_api.swagger.json"

EXPECTED_PATHS = [
    "/v1/partner/list-suppliers",
    "/v1/activity/search-activities",
    "/v1/activity/get-activity-detail",
    "/v1/price/get-price-and-availability-calendar",
    "/v1/price/check-availability-and-calculate-amount",
    "/v1/booking/ota/start-booking",
    "/v1/booking/ota/list-reservations",
    "/v1/booking/ota/final-booking",
    "/v1/booking/ota/cancel-reservations",
    "/v1/booking/ota/get-booking",
    "/v1/booking/ota/list-bookings",
    "/v1/booking/ota/update-booking-participant-info",
    "/v1/booking/ota/start-cancel-booking",
    "/v1/booking/ota/final-cancel-booking",
]

# Definitions the reference files make specific claims about. These sit late in the
# document, so their presence is what proves the download was not truncated.
EXPECTED_DEFINITIONS = [
    "rpc.Status",
    "Activity",
    "GetActivityDetailResponse.Plan",
    "external.BookingForm",
    "BookingFieldSpec",
    "CustomFieldSpec",
    "StartBookingRequest",
    "StartBookingResponse",
    "FinalBookingRequest",
    "CancelReservationsRequest",
    "ParticipantInfo",
    "UserInformationFields",
    "BookingRepresentativeFields",
    "OthersInformationFields",
    "external.BookingInfo",
    "external.CancelRefundDisplay",
    "StartCancelBookingResponse",
    "FinalCancelBookingRequest",
    "UpdateBookingParticipantInfoRequest",
    "unit.Unit",
    "price.Price",
    "Text",
]

EXPECTED_SECURITY_HEADERS = {
    "ota-id",
    "group-id",
    "api-key-id",
    "timestamp",
    "signature-key",
}


def validate(spec: dict) -> list[str]:
    """Return a list of problems. Empty list means the spec looks complete."""
    problems: list[str] = []

    version = spec.get("swagger") or spec.get("openapi")
    if version != "2.0":
        problems.append(f"expected swagger 2.0, found {version!r}")

    paths = spec.get("paths") or {}
    missing_paths = [p for p in EXPECTED_PATHS if p not in paths]
    if missing_paths:
        problems.append(f"missing {len(missing_paths)} expected path(s): {missing_paths}")
    extra_paths = sorted(set(paths) - set(EXPECTED_PATHS))
    if extra_paths:
        # Not an error — the API may have grown. Worth surfacing.
        print(
            f"note: {len(extra_paths)} path(s) present that this skill does not document "
            f"yet: {extra_paths}",
            file=sys.stderr,
        )

    definitions = spec.get("definitions") or (spec.get("components") or {}).get("schemas") or {}
    missing_defs = [d for d in EXPECTED_DEFINITIONS if d not in definitions]
    if missing_defs:
        problems.append(
            f"missing {len(missing_defs)} expected definition(s) — the document is most "
            f"likely truncated: {missing_defs}"
        )

    sec = spec.get("securityDefinitions") or {}
    missing_headers = EXPECTED_SECURITY_HEADERS - set(sec)
    if missing_headers:
        problems.append(f"missing securityDefinitions: {sorted(missing_headers)}")

    return problems


def summarise(spec: dict) -> None:
    info = spec.get("info") or {}
    definitions = spec.get("definitions") or {}
    servers = spec.get("x-servers") or []
    print(f"  title       : {info.get('title')}")
    print(f"  version     : {info.get('version')}")
    print(f"  operations  : {len(spec.get('paths') or {})}")
    print(f"  definitions : {len(definitions)}")
    for s in servers:
        print(f"  server      : {s.get('description')} -> {s.get('url')}")


def load_local(path: Path) -> int:
    if not path.exists():
        print(f"No local spec at {path}")
        print("Run without --check to download it.")
        return 1
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Local spec at {path} is not valid JSON: {exc}")
        return 1
    problems = validate(spec)
    print(f"Local spec: {path} ({path.stat().st_size:,} bytes)")
    summarise(spec)
    if problems:
        print("\nINCOMPLETE:")
        for p in problems:
            print(f"  - {p}")
        print("\nRe-download with --force.")
        return 1
    print("\nComplete and consistent with what this skill documents.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        return load_local(args.output)

    if args.output.exists() and not args.force:
        print(f"{args.output} already exists. Pass --force to overwrite, or --check to validate it.")
        return 1

    print(f"Fetching {args.url}")
    try:
        req = urllib.request.Request(args.url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code} fetching the spec. Check the URL is still correct.")
        return 1
    except urllib.error.URLError as exc:
        print(f"Could not reach the spec: {exc.reason}")
        print(
            "If this machine has no direct internet access, download the file manually "
            "and place it at:\n  " + str(args.output)
        )
        return 1

    print(f"Received {len(raw):,} bytes")

    try:
        spec = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"Response is not valid JSON ({exc}).")
        print("A proxy or captive portal may have altered the response. Not writing it.")
        return 1

    problems = validate(spec)
    summarise(spec)
    if problems:
        print("\nREJECTED — the download does not look like a complete spec:")
        for p in problems:
            print(f"  - {p}")
        print("\nNothing was written. A partial spec treated as authoritative is worse")
        print("than none; the reference files in this skill remain usable on their own.")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Re-serialise so the stored file is stable and diffable.
    args.output.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {args.output} ({args.output.stat().st_size:,} bytes)")
    print("SKILL.md will now prefer this file for exact field-level questions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
