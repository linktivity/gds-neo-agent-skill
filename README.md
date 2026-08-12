# Linktivity GDS API — agent skill

An [Agent Skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
that teaches an AI assistant how the **Linktivity GDS API** (GDS-neo / open-agent) works, so
you can ask it your integration questions directly instead of reading the whole spec.

It knows the HMAC `signature-key` algorithm and can tell you which of nine common
implementation mistakes produced a wrong signature. It knows every endpoint's parameters and
required fields, the reserve-then-confirm booking and cancellation flows, how to map
`booking_form` onto the `participant_info` payload, and how to read a `rpc.Status` error. The
full OpenAPI spec is bundled, so answers are grounded in the actual schema rather than
paraphrase.

API documentation: <https://linktivity.github.io/gds-neo-proto-public/apidoc/>

---

## Install

### Claude Code / Cowork (recommended)

```
/plugin marketplace add linktivity/gds-neo-agent-skill
/plugin install gds-neo-api@linktivity-gds
```

To update later:

```
/plugin marketplace update linktivity-gds
```

### Claude web and desktop apps

1. Download [`dist/gds-neo-api.skill`](dist/gds-neo-api.skill).
2. In Claude, go to **Customize → Skills**, click **+**, then **Create skill → Upload a
   skill**, and select the downloaded file.

Requires code execution to be enabled on your account. Skills uploaded this way are private to
your own account — if your whole team needs it, ask an organization owner to provision it under
**Organization settings → Skills** (Team and Enterprise plans).

### Codex CLI

```
codex plugin marketplace add linktivity/gds-neo-agent-skill
codex plugin add gds-neo-api@linktivity-gds
```

### Any other agent, or manual use

The skill is plain Markdown plus two Python scripts. Clone the repo and point your tool at
`plugins/gds-neo-api/skills/gds-neo-api/`, or just read the files — start with `SKILL.md`, which
routes to the right reference file for your question.

```bash
git clone https://github.com/linktivity/gds-neo-agent-skill.git
```

---

## What's in it

| File | Covers |
| --- | --- |
| `SKILL.md` | Routing, the facts integrators get wrong most often, endpoint map |
| `references/auth.md` | Five required headers, the signature algorithm, reference code in five languages, a debugging checklist |
| `references/flow.md` | Four-stage integration flow, two-phase booking and cancellation, session expiry, status model, the three currency figures |
| `references/endpoints.md` | All 14 operations — parameters, required flags, responses, copy-pasteable request bodies |
| `references/schemas.md` | Every response object's fields |
| `references/enums.md` | Every enum value, including the full currency, country and prefecture lists |
| `references/booking-form.md` | `booking_form` → `participant_info` mapping, custom reservation fields, worked example |
| `references/troubleshooting.md` | Symptom → cause → fix, error codes, known spec quirks |
| `references/glossary.md` | English / 中文 / 日本語 terminology |
| `scripts/gds_sign.py` | Compute, verify and diagnose the `signature-key`; issue signed requests |
| `scripts/fetch_spec.py` | Refresh and validate the bundled OpenAPI spec |
| `assets/gds_api.swagger.json` | The full Swagger 2.0 spec — 14 operations, 119 definitions |

## Debugging a signature by hand

The most common support question is `401 invalid signature`. You can resolve it yourself:

```bash
export GDS_API_KEY='your-api-key-secret'   # the secret, not api-key-id

# What should the header be?
python3 scripts/gds_sign.py sign \
  --env sandbox --path /v1/activity/search-activities

# My client produced a signature the server rejects. Why?
python3 scripts/gds_sign.py verify \
  --env sandbox --path /v1/activity/search-activities \
  --timestamp 20260521T063324Z --signature '<what your client produced>'
```

`verify` compares against the expected value and, on a mismatch, names the specific bug —
hex-encoded intermediates between HMAC steps, standard instead of URL-safe base64, stripped
`=` padding, a scheme left on the host, transposed message and key arguments, and so on.

## Contributing

`dist/*.skill` is a packaged copy of `plugins/gds-neo-api/skills/*/`, committed alongside the
source (see [Install](#install) above). After editing anything under `plugins/gds-neo-api/skills/`,
rebuild it:

```bash
scripts/package_skill.sh
```

To do that automatically, enable the repo's pre-commit hook once per clone:

```bash
git config core.hooksPath .githooks
```

It reruns `scripts/package_skill.sh` and stages the result whenever a commit touches
`plugins/gds-neo-api/skills/`. Either way, `.github/workflows/package-check.yml` rebuilds and
diffs every package in CI, so an out-of-date `dist/*.skill` fails the check rather than merging
silently.

## Support

Questions about the API itself, credentials, or supplier entitlement:
<info@linktivity.co.jp> / <https://www.linktivity.co.jp/Contact>

Issues with this skill — a wrong field, a missing endpoint, an answer that sent you the wrong
way: please open an issue on this repository.

## Note on accuracy

The reference files are written from the published OpenAPI spec, and every factual claim in
them was checked against it programmatically. `references/troubleshooting.md` also documents
several inconsistencies in the spec itself (a `host` field carrying a scheme, a `required`
array naming a property that doesn't exist, enum types inlined rather than referenced) because
they surface as confusing generated-client behaviour rather than as clear errors.

The bundled spec is a snapshot. Run `python3 scripts/fetch_spec.py --force` to refresh it, and
`--check` to validate a copy.
