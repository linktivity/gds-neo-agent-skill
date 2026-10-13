# Troubleshooting

## Start here: read the error body

Every `4xx` and `5xx` returns an `ErrorResponse`:

```json
{
  "code": 9,
  "error_code": "BOOKING_ADAPTER_BOOKING_NO_AVAILABILITY",
  "message": "booking adapter error",
  "details": [
    {
      "metadata": {
        "booking_adapter_error_code": "2004",
        "request_id": "e9c30653-eafa-4169-a08e-9e28748adb69"
      }
    }
  ],
  "retryable": false
}
```

The one exception: requests rejected by the auth check at the HTTP edge return
`{"message": "..."}` only — see `auth.md`.

- **Branch on `error_code`**, never on `message` (its wording changes). New values can appear
  at any time; handle an unknown one by its `code`.
- **`retryable` decides resends.** `true`: resend the same request as is after a short wait.
  `false`: don't; act on `error_code`. It is authoritative — the same code can be retryable on
  one endpoint and not another.
- **`details[].metadata`** carries `request_id` (quote it to support) plus the keys documented
  for the code — `field` / `constraint` for validation errors, `booking_id` for cancellation
  errors. If an integrator says "the error doesn't tell me anything", ask whether they log
  the whole body — most client wrappers keep only `message`.

When no business code applies, `error_code` is the gRPC code name:

| `error_code` | `code` | HTTP | Meaning | `retryable` |
| --- | --- | --- | --- | --- |
| `INVALID_ARGUMENT` | 3 | 400 | Body isn't valid JSON, or a field fails validation without a more specific code. | false |
| `DEADLINE_EXCEEDED` | 4 | 504 | Passed the 30 s server limit. **Outcome unknown** — check state before resending a booking or cancellation. | true |
| `NOT_FOUND` | 5 | 404 | Entity doesn't exist and no more specific code applies. | false |
| `PERMISSION_DENIED` | 7 | 403 | The entity belongs to another OTA or OTA group. | false |
| `RESOURCE_EXHAUSTED` | 8 | 429 | Quota or rate limit. Back off. | true |
| `FAILED_PRECONDITION` | 9 | 400 | Wrong state for the operation; the endpoint description names the cases. | false |
| `ABORTED` | 10 | 409 | Another request is working on the same session/booking/bundle. Resend after a few seconds. | true |
| `UNIMPLEMENTED` | 12 | 405 | Wrong HTTP method for the path. | false |
| `INTERNAL` | 13 | 500 | Internal error. Quote `request_id`. | false |
| `UNAVAILABLE` | 14 | 503 | A dependency is unreachable. | true |
| `UNAUTHENTICATED` | 16 | 401 | Missing header, bad signature, or `timestamp` out of range — see `auth.md`. | false |

Business codes you will meet most (the full table, with metadata keys, is in the spec's
`info.description` under **Errors**):

| `error_code` | HTTP | Meaning |
| --- | --- | --- |
| `VALIDATION_FAILED` | 400 | Any endpoint: a field failed validation. One `details` entry per field (`field`, `constraint`). |
| `BOOKING_REQUIRED_INFO_MISSING` | 400 | StartBooking: a required participant/booking field is missing or malformed. Per field. |
| `BOOKING_INVALID_FORM_RESPONSE` | 400 | StartBooking: a custom form response is missing or invalid. Per response. |
| `INSUFFICIENT_BALANCE` | 400 / 503 | Wallet can't cover the booking. **400**: nothing booked — top up, then retry. **503** (FinalBooking, after the supplier placed it): the booking is **held** — top up and resend FinalBooking on the same session; never create a new booking. |
| `BOOKING_ADAPTER_*` | various | The supplier rejected or failed the operation (`..._NO_AVAILABILITY`, `..._NOT_ENOUGH_ALLOTMENT`, `..._DEADLINE_PASSED`, `..._EXTERNAL_PENDING`, ...). `message` is always `booking adapter error`; tell them apart by `error_code`. Ignore the legacy `booking_adapter_error_code` metadata — it will be removed. |
| `BOOKING_ADAPTER_INTERNAL` | 500 | The supplier connection failed unclassifiably. **Outcome unknown** — don't assume the supplier did nothing. |

Cancellation codes are listed under **Cancellation failures** below.

## Authentication

Everything about `401 invalid api-key-id`, `401 invalid signature`, and
`401 timestamp out of range` is in `auth.md`, including a signature debugging checklist
ordered by likelihood. Use `scripts/gds_sign.py` to compute the expected signature from
their inputs rather than reasoning about the chain by eye.

The two fastest discriminators:

- Signature works on one endpoint and fails on another → the `path` isn't being derived per
  request, or the query string is leaking into it.
- Signature fails on everything, consistently → hex-vs-raw-bytes in the HMAC chain, or the
  wrong secret.

## `start-booking` failures

**`INVALID_ARGUMENT` with `LANGUAGE_CODE` / `ALLOWED_LANGS` in `details[].metadata`.** The `language_code` you sent
isn't among the activity's configured languages. Read `activity.language_codes` from
`get-activity-detail` and send one of those. This is the single most common first-day
failure.

**`target_date` rejected as missing.** Required unless the plan's `confirmation_type` is
`FREE_SALE_OPEN_DATE`. Check `booking_rule.confirmation_type`.

**`target_date` rejected as out of range.** Two rules apply, both from `booking_rule`:
`booking_period` (how far ahead you may book, e.g. 30 `DAY`) and `booking_deadline`
(`before_days` + `deadline_time`, e.g. 1 day before at 23:00). Also check
`publication_period` on the plan, and remember `target_date` is interpreted in the
**activity's** timezone, not yours — a booking that looks in-window at 08:00 JST may be out
of window when evaluated against a different local date.

**Unit or capacity rejection.** Check three things. First, the **capacity-counted** total —
units with `include_in_capacity: false` (infants, typically) are excluded — against
`min_capacity_inclusive`; use the raw `plan_unit_items[]` total for `max_capacity_inclusive`,
since the flag is documented against the minimum only. Second, whether you're booking a unit
with `can_be_book_independently: false` on its own (children usually need an accompanying
adult). Third, that each `plan_unit_id` actually belongs to the `plan_id` you're booking.

**Inventory unavailable despite the calendar saying otherwise.** The calendar is a snapshot.
Between reading it and booking, someone else may have taken the stock. Also check
`allotment_type` — if it's `PLAN_ITEM_SHARED` or `UNIT_SHARED`, the `allotment_quantity` you
read for one unit is shared with others, so summing across units overstates what's
available. Call `check-availability-and-calculate-amount` immediately before booking.

**Pending-reservation limit reached.** You have too many held-but-unconfirmed sessions. Call
`list-reservations` and release the orphans with `cancel-reservations`. Fix the root cause:
every abandoned checkout must trigger a `cancel-reservations`.

**`participant_info` rejected** (`BOOKING_REQUIRED_INFO_MISSING` /
`BOOKING_INVALID_FORM_RESPONSE`). `details[].metadata.field` names each offending field. Work
through `booking-form.md`. The recurring causes are:
`weight_kg` / `height_cm` / `shoe_size_cm` sent as numbers instead of strings; `gender` not
exactly `"male"` / `"female"` / `"other"`; a custom field's `responses` containing an index
or id instead of the choice **label**; and the `user_information_fields[]` count or
`plan_unit_id` distribution not matching `plan_unit_items[]`.

## `final-booking` failures

**Session expired.** Read `expiry` from the `start-booking` response and drive your checkout
timer from it. When the adapter provides no expiry a 15-minute fallback applies, so treat 15
minutes as the floor. Once expired, start over from `start-booking`.

**Ambiguous outcome — did it book or not?** Do not retry blindly. Determine state first:

1. `list-reservations` — if the session is still there, it did not confirm; retry
   `final-booking` on the same session.
2. `list-bookings` filtered by your `agent_booking_id` — if a booking exists, it succeeded
   and you lost the response.
3. Neither — the session is gone and nothing was created. Start over from `start-booking`
   with a **new** `idempotent_key`.

This is why setting `agent_booking_id` on every `start-booking` matters: it is the only way
to find a booking you never received the id for.

**Booking returned but status isn't `CONFIRMED`.** Expected for `REQUEST` products — the
status is `REQUEST_PENDING` until the supplier reviews it. Poll `get-booking` until it
becomes `CONFIRMED` or `REQUEST_REJECTED`. Never show the traveler a confirmed booking on
the strength of a `booking_id` alone.

**`idempotent_key` returning a stale session.** The key is honoured for 24 hours, so
reusing one from an earlier attempt returns that attempt's `session_id`. To force a fresh
booking, send a new key. Keys longer than 64 characters are rejected outright.

## Cancellation failures

A booking that can't be cancelled, or a cancellation that didn't go through, is an HTTP error
with a business `error_code` — never a 200. (`cancel_check_code` is deprecated and always
`CAN_BE_CANCELLED` on a 200; `CANCEL_FAILED` never appears in a `final-cancel-booking` 200.)

| `error_code` | Endpoint | Meaning / what to do |
| --- | --- | --- |
| `BOOKING_NOT_FOUND` | both | No booking matches `booking_id`. |
| `BOOKING_ALREADY_CANCELLED` | both | Terminal and benign. Treat as settled; don't retry. |
| `CANCEL_DEADLINE_PASSED` | both | The voucher expiration time has passed. |
| `BOOKING_ALREADY_ISSUED` | both | The voucher is redeemed in full or in part. |
| `BOOKING_NOT_CANCELLABLE` | both | Status, policy, bulk/bundle constraint, or one bundle child forbids it. `message` tells the cases apart; `metadata.booking_id` names the blocking child for a bundle. Cancel a bundle via its parent. |
| `CANCEL_NOT_STARTED` | final | No open cancellation request. Call `start-cancel-booking` first. |
| `CANCEL_REFUND_CHANGED` | final | The fee changed since `start-cancel-booking`, so that request is void. Call `start-cancel-booking` again for the current amounts. |

**`CANCEL_PENDING`.** Not a failure. Some suppliers cancel asynchronously or by hand. Call
`final-cancel-booking` again later — it resumes the open request instead of cancelling twice.

**A bundle cancellation failed part-way.** One child's error fails the whole call, with
`details[].metadata.booking_id` naming that child. Children already cancelled stay cancelled
and the parent's request stays open: resolve the cause, then call `final-cancel-booking`
again.

**`get-booking` shows `CANCEL_FAILED`.** Still possible there even though
`final-cancel-booking` never returns it: the call failed after the supplier had accepted, or a
bundle stopped on a child. The booking is **not** cancelled. Resume a bundle parent with
`final-cancel-booking`; otherwise retry from `start-cancel-booking`, and escalate if it fails
again.

**Refund amount differs from the quote.** It doesn't silently: `final-cancel-booking` applies
exactly the amounts `start-cancel-booking` quoted, and fails with `CANCEL_REFUND_CHANGED` if
they moved (e.g. a `CancellationRule` boundary was crossed). Quote and commit close together.

**`is_cancellable_now` was `true` but cancellation failed.** Documented behaviour: it is
evaluated at read time without holding a lock, so it's a hint, not a reservation.

## Query and encoding issues

**`list-bookings` timestamp filters silently returning wrong results.** The `+` in an RFC
3339 offset like `2026-04-01T14:53:34+09:00` **must** be percent-encoded as `%2B`. Unencoded,
it is parsed as a space and the filter misbehaves without erroring. Sending UTC (`...Z`)
avoids the problem entirely.

**Array parameters not filtering.** `supplier_ids`, `activity_ids`, `categories`,
`booking_id`, `agent_booking_id`, `supplier_booking_id`, `booking_status` and `order_bys` all
use `collectionFormat: multi` — repeat the parameter (`?supplier_ids=A&supplier_ids=B`).
Comma-joining into one value (`?supplier_ids=A,B`) will not work.

**`plan_unit_id` mangled.** These are opaque base64-looking strings often ending in `==`.
Copy them verbatim. If one ends up in a query string, URL-encode it properly; `=` and `+`
survive poorly otherwise.

**Pagination behaving oddly.** `search-activities` is **cursor**-based (`cursor` /
`next_cursor`, opaque — no offset arithmetic). `list-bookings` is **offset**-based (`page_no`
from 1, `page_size`). They are different models; don't apply one's idiom to the other.

## Data and response surprises

**Responses are enormous.** You omitted `language_code`. Without it, every `Text` field is
populated for every configured language. Pass a specific `language_code` in production.

**`redemption_url` is missing.** Normal. It is populated only when the activity has it
configured. The other four `voucher_urls` entries are always present.

**`Text.i18n_text` doesn't have my language.** Fall back to `text`. Keys are `Language`
enum **names** (`"ENGLISH"`, `"SIMPLIFIED_CHINESE"`), not IETF tags. If you're looking up
`"en-US"`, that's the bug. Separately, `LocalizedValue.language_code` inside `Choice`
**does** use lowercase tags like `"ja-jp"` — the API has two localisation conventions.

**Prices don't reconcile.** Three figures serve three purposes. Reconcile settlement against
`payment_currency_price`; `display_currency_price` is presentation only and depends on the
`display_currency_code` you sent. Within each, `net` is your cost and `gross` is retail.
Note `check-availability-and-calculate-amount` names these `*_amount` rather than
`*_currency_price`.

**`allotment_quantity` doesn't match what I can sell.** Read `allotment_type` first. Under
`PLAN_ITEM_SHARED` / `UNIT_SHARED` / `PLAN_ITEM_AND_UNIT_SHARED` the number is a shared pool;
summing across units double-counts.

**Dates are off by a day.** `target_date`, `booking_date`, `expiration_date` and
`plan_item_value` are all in the **activity's** timezone (`activity_timezone`, e.g.
`Asia/Tokyo`). `booking_at` is an RFC 3339 instant. Converting the instant to a date in your
own timezone will disagree with `booking_date` near midnight.

**`origins` has a different shape on two endpoints.** `search-activities` returns
`SimpleLocation` (`title` + `description` only); `get-activity-detail` returns
`PreciseLocation` with coordinates and Google Maps fields. Same field name, different type.

**Coordinates field is `lon`, not `lng`.** `PreciseLocation.LatLng` is `{lat, lon}`.

**Supplier list order changed.** `list-suppliers` explicitly does not guarantee order. Sort
client-side if you need stability.

## Known spec quirks

Worth knowing because they surface as odd generated-client behaviour rather than as errors.

**`host` includes the scheme.** The spec's `host` is
`https://open-agent.gds-neo.link-dev.link`, which is unusual for Swagger 2.0 — generators
sometimes produce `https://https//...`. Strip the scheme for the host and set it separately.
The signing host is always the bare hostname.

**`session_id` vs `booking_session_id` vs `booking_session_ids`.** `StartBookingResponse`
calls it `session_id`; `FinalBookingRequest` calls it `booking_session_id`; and
`CancelReservationsRequest` takes an array named `booking_session_ids`. Same value, three
field names.

**`display_currency` vs `display_currency_code`.** `search-activities`,
`get-activity-detail`, `get-price-and-availability-calendar` and
`check-availability-and-calculate-amount` all use `display_currency`. `start-booking` uses
`display_currency_code`. Sending the wrong one means the parameter is silently ignored and
you get the OTA's default currency instead.

**The `Prefecture` enum is defined as `Perfecture`.** Misspelled in the schema; the query
parameter is correctly `prefecture` and the values are identical. Only affects generated
model class names.

**`TEMPLES_SHINES`.** The `TravelProductCategory` value is spelled `SHINES`, not `SHRINES`.
Send it as spelled.

**Async final-booking types with no endpoint.** `AsyncFinalBookingResponse`,
`GetFinalBookingStatusResponse` and `AsyncFinalBookingStatus` are defined in `definitions`
but **no path exposes them**. Don't code against them; confirm availability with Linktivity.

**Named enum types whose values are inlined at each use site.** `BookingModel.Status`,
`CancelBookingStatus`, `IssuedStatus`, `RefundRuleType`, `QRCodeCodeType`,
`cancellation.CancelReason` and `Perfecture` all exist as named definitions, but every
operation and object that uses them repeats the value list inline instead of `$ref`-ing the
definition. Consequence for code generation: you get a separate anonymous enum type per field
rather than one shared type, so a value you can assign in one place won't type-check in
another. Either post-process your generated client to collapse them, or hand-write the enums
from `enums.md`. Of the 119 definitions, only `ParentBooking` and the three async types are
genuinely unreachable; these seven are reachable by value, just not by reference.

**`4xx` / `5xx` as response keys.** The spec uses wildcard status keys rather than specific
codes, so generated clients may not map individual statuses. Handle the ranges.

**The `plan_unit_items` example uses an inconsistent id shape.** The published
`StartBookingRequest` example shows `plan_unit_items[].id` as `LINKTIVITY-1QCOC-1-1`, which is
the same value as that example's `plan_item_id`; every other example in the spec uses the
opaque base64 form. Don't infer a format from the example — read `plan_unit_id` from
`get-activity-detail` and send it unchanged. See `booking-form.md`.

## When to escalate

Escalate to <info@linktivity.co.jp> — or <https://www.linktivity.co.jp/Contact> — rather
than debugging further, when:

- Credentials appear correct and `scripts/gds_sign.py` reproduces the client's signature
  exactly, yet the server still returns `401 invalid signature`.
- `PERMISSION_DENIED` on a supplier or activity the integrator believes they are contracted
  for. Entitlement is configured server-side; the API cannot tell them why.
- A booking is stuck in `REQUEST_PENDING` or `CANCEL_PENDING` far longer than the supplier's
  normal turnaround.
- `booking_id` exists but the supplier has no matching record, or `supplier_booking_id` is
  empty on a `CONFIRMED` booking.
- Repeated `UNAVAILABLE` / `DEADLINE_EXCEEDED` from one supplier while others work.

Include in the report: the full error body (including `error_code` and `details[].metadata.request_id`), the `timestamp` header
value, the endpoint path, `agent_booking_id` and `booking_id` where applicable, and whether
it is sandbox or production. Never include the API key secret.
