# assets/

## `gds_api.swagger.json` — the machine-readable spec

Shipped in this package as a snapshot. Refresh or validate it with:

```bash
python3 scripts/fetch_spec.py --force   # re-download + validate, overwriting this snapshot
python3 scripts/fetch_spec.py --check   # validate the copy that's already here
```

Source URL:
<https://linktivity.github.io/gds-neo-proto-public/apidoc/gds_api.swagger.json>

If this file is missing — e.g. an older checkout, or an install method that didn't carry
`assets/` — run `python3 scripts/fetch_spec.py` (no flags) to fetch it. If the machine has no
direct internet access, download the file by hand and save it here as `gds_api.swagger.json`,
then run `--check` to confirm it is complete.

### Why bother

`SKILL.md` prefers this file over the hand-written `references/` files whenever a question
turns on an exact field name, type, or `required` flag, and an agent can query it directly:

```bash
python3 -c "import json;s=json.load(open('assets/gds_api.swagger.json'));print(json.dumps(s['definitions']['StartBookingRequest'],indent=2))"
```

Two payoffs. Every claim in `references/` becomes machine-checkable rather than trust-me, and
the skill stops needing network access to answer field-level questions.

### Validation, and why it refuses partial downloads

`fetch_spec.py` will not store a response that fails to parse, is not Swagger 2.0, is missing
any of the 14 documented operations, or is missing any of ~22 definitions the reference files
make specific claims about. Those definitions sit late in the document, so their presence is
what proves the download wasn't truncated — some proxies and doc-fetching tools silently cut
long JSON, and a half-spec treated as authoritative is worse than no spec at all. If
validation fails, nothing is written and `references/` remains the source of truth.

The script also prints a note if the spec contains operations this skill does not document
yet — a useful signal that the API has grown and the reference files need a pass.

### Staleness

`info.version` is `1.0.{DATE}`, so a stored copy is a snapshot. When you refresh it, re-check
the "Known spec quirks" section of `references/troubleshooting.md` — those are the claims most
likely to be fixed upstream and silently falsified here.

The skill works without this file. Nothing breaks if you skip it.
