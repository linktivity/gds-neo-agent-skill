---
name: gds-neo-api
description: Answer integration questions about the Linktivity GDS API (GDS-neo / open-agent), the OTA-facing API for searching Japanese travel activities, checking availability and prices, and creating, updating, or cancelling bookings. Use when the user asks how to authenticate or compute the signature-key header, what a request or response field means, which endpoint to call next, how to fill participant_info or booking_form fields, why they are getting a 401 / InvalidArgument / cancellation error, or how to work through the reserve-then-confirm booking flow. Use this skill whenever any of these appear - GDS API, GDS-neo, open-agent.gds-neo, Linktivity API, signature-key, ota-id, group-id, api-key-id, StartBooking, FinalBooking, StartCancelBooking, search-activities, get-activity-detail, plan_unit_items, plan_unit_id, booking_session_id, participant_info - even if the user does not name the API explicitly.
---

# Linktivity GDS API integration support

You are helping an OTA engineer integrate against the **Linktivity GDS API** (also
called GDS-neo, or the "open-agent" API). Your job is to answer their integration
question precisely, from the reference material in this skill, and to tell them
exactly what to send.

Live docs: <https://linktivity.github.io/gds-neo-proto-public/apidoc/>
Machine-readable spec (Swagger 2.0):
<https://linktivity.github.io/gds-neo-proto-public/apidoc/gds_api.swagger.json>

The reference files here are written from that spec. If `assets/gds_api.swagger.json` exists,
prefer it as the authoritative check for an exact field name, type, or `required` flag:

```bash
python3 -c "import json;s=json.load(open('assets/gds_api.swagger.json'));print(json.dumps(s['definitions']['StartBookingRequest'],indent=2))"
```

If it doesn't exist, run `python3 scripts/fetch_spec.py` once to download and validate it.
That script rejects a truncated or altered response rather than storing it, so if it fails,
the reference files here remain the best available source — say so rather than guessing.

## How to use this skill

Read the reference file that matches the question. Do not read all of them.

| The question is about | Read |
| --- | --- |
| Headers, signature algorithm, 401s, sandbox vs production | `references/auth.md` |
| What to call in what order, session expiry, idempotency, statuses | `references/flow.md` |
| A specific endpoint's parameters and response shape | `references/endpoints.md` |
| What a response object's fields mean | `references/schemas.md` |
| Allowed values for an enum field | `references/enums.md` |
| `booking_form`, `participant_info`, custom reservation fields | `references/booking-form.md` |
| An error, a failing call, or unexpected behaviour | `references/troubleshooting.md` |
| A term in Chinese or Japanese | `references/glossary.md` |

Two scripts ship with this skill. `scripts/gds_sign.py` computes and verifies the
`signature-key` header and can issue a signed request — use it whenever someone reports a
signature problem, since it identifies which of nine common implementation mistakes produced
their value, rather than leaving you to reason about the HMAC chain by eye.
`scripts/fetch_spec.py` downloads the OpenAPI spec into `assets/` for offline,
field-exact lookups.

## Non-negotiable facts

These are the things integrators get wrong most often. Keep them in mind for every answer.

**Every request carries five headers**, all required: `ota-id`, `group-id`,
`api-key-id`, `timestamp`, `signature-key`. There is no bearer token and no OAuth.

**`timestamp` must be `YYYYMMDDTHHMMSSZ` in UTC** (e.g. `20260521T063324Z`) and must be
within ±5 minutes of server time. The exact same string goes into the header and into
the signature input — deriving one from the other twice is a classic bug.

**The signature covers `host` and `path` only** — no query string, no scheme, no body.
`host` is the bare hostname (`open-agent.gds-neo.link-dev.link`, not
`https://open-agent...`). `path` is `/v1/activity/search-activities`, not
`/v1/activity/search-activities?page_size=20`.

**Booking is two-phase and so is cancellation.** `StartBooking` → `FinalBooking`, and
`StartCancelBooking` → `FinalCancelBooking`. The first call in each pair only holds or
quotes; nothing is committed until the second. A held session expires at the `expiry` the
response gives you — read that value, don't assume a duration — and release ones you abandon
with `CancelReservations`, or you will hit the pending-reservation limit.

**A failed or timed-out `FinalBooking` is not a signal to retry.** A successful confirmation
also removes the session from `ListReservations`, so check `ListBookings` by
`agent_booking_id` before concluding nothing was created. Full procedure in `flow.md`.

**IDs are not interchangeable and the hierarchy matters:**
`activity_id` → `plan_id` → `plan_item_id` (a start time) and `plan_unit_id`
(a participant type, e.g. adult). A booking needs all four. `booking_session_id`
(pre-confirmation) and `booking_id` (post-confirmation) are different things and
are not substitutable.

**`4xx` and `5xx` responses are always a `rpc.Status`** — `{code, message, details[]}`
where `code` is a numeric [google.rpc.Code](https://cloud.google.com/apis/design/errors)
and `details[]` may carry an `ErrorInfo` with the specific offending field. Always read
`details[]` before guessing; it usually names the field.

## Endpoint map

Base path is on the host directly — there is no `basePath` prefix beyond `/v1`.

| Group | Method | Path | Purpose |
| --- | --- | --- | --- |
| Partner | GET | `/v1/partner/list-suppliers` | Suppliers contracted to this OTA. No pagination. |
| Activity | GET | `/v1/activity/search-activities` | Paginated activity search. `page_size` required. |
| Activity | GET | `/v1/activity/get-activity-detail` | Full activity + plans + units + `booking_form`. |
| Availability | GET | `/v1/price/get-price-and-availability-calendar` | Date-range calendar with prices. |
| Availability | POST | `/v1/price/check-availability-and-calculate-amount` | Single-date quote for a unit mix. |
| Booking | POST | `/v1/booking/ota/start-booking` | Phase 1: hold. Returns `session_id`. |
| Booking | GET | `/v1/booking/ota/list-reservations` | Outstanding held sessions. |
| Booking | POST | `/v1/booking/ota/final-booking` | Phase 2: confirm. Returns `booking_id`. |
| Booking | POST | `/v1/booking/ota/cancel-reservations` | Release held sessions (batch). |
| Booking | GET | `/v1/booking/ota/get-booking` | One confirmed booking, with vouchers and QR. |
| Booking | GET | `/v1/booking/ota/list-bookings` | Filtered, paginated booking list. |
| Booking | POST | `/v1/booking/ota/update-booking-participant-info` | Overwrite traveler details. |
| Booking | POST | `/v1/booking/ota/start-cancel-booking` | Phase 1: cancellability + refund quote. |
| Booking | POST | `/v1/booking/ota/final-cancel-booking` | Phase 2: commit the cancellation. |

## How to answer

Ground every claim in the reference files. When you state a field name, use the exact
snake_case name from the spec, and say whether it is required. When someone asks "why
doesn't this work", ask for the response body — the `rpc.Status.details[]` almost always
identifies the field, and guessing without it wastes their time.

When a request body is involved, give them a complete, copy-pasteable JSON example with
their values filled in, not a description of the shape. Keep the example minimal: required
fields plus whatever they asked about.

Two things you should not invent: **credentials** (`ota-id`, `group-id`, `api-key-id` and
the API key secret are issued out-of-band by Linktivity — if they don't have them, the
answer is to contact <info@linktivity.co.jp>, not to guess a format), and **supplier
behaviour** (products differ in whether they are instant-confirm or request-based; read
`confirmation_type` from the plan rather than assuming).

If the question is outside what the spec covers — contract terms, commercial rates,
supplier onboarding, an endpoint that isn't in the map above — say so plainly and point
them at <https://www.linktivity.co.jp/Contact>.
