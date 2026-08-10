# Troubleshooting

## Start here: read the error body

Every `4xx` and `5xx` returns an `rpc.Status`:

The shape, with the one error the spec documents concretely — `start-booking` rejecting a
`language_code` the activity doesn't support:

```json
{
  "code": 3,
  "message": "...",
  "details": [
    {
      "@type": "type.googleapis.com/google.rpc.ErrorInfo",
      "metadata": {
        "LANGUAGE_CODE": "GERMAN",
        "ALLOWED_LANGS": "...",
        "ACTIVITY_ID": "LINKTIVITY-1QCOC"
      }
    }
  ]
}
```

The three `metadata` keys are documented in the spec's `StartBookingRequest.language_code`
description. The exact `message`, `reason` and `domain` values are not documented anywhere —
read them from the real response rather than matching on them, and don't build logic around
string equality with a `reason` you haven't observed in your own environment.

`code` is a numeric [google.rpc.Code](https://cloud.google.com/apis/design/errors), **not**
the HTTP status. `details[]` is where the actionable information is. If an integrator says
"the error doesn't tell me anything", the first question is whether they are logging
`details[]` — most client wrappers throw away everything but `message`.

Common `code` values and what they mean here:

| `code` | Name | Typical meaning in the GDS API |
| --- | --- | --- |
| 3 | `INVALID_ARGUMENT` | A field is missing, malformed, or not allowed for this activity. Read `details[]`. |
| 5 | `NOT_FOUND` | An id doesn't exist, or an expired session id. |
| 7 | `PERMISSION_DENIED` | Credentials valid but not entitled to this supplier or activity. |
| 9 | `FAILED_PRECONDITION` | Correct request, wrong state — e.g. confirming an expired session, cancelling an already-cancelled booking. |
| 8 | `RESOURCE_EXHAUSTED` | Inventory unavailable, or the pending-reservation limit reached. |
| 16 | `UNAUTHENTICATED` | The 401 family — see `auth.md`. |
| 14 | `UNAVAILABLE` | Supplier system down or timing out. Retry with backoff. |
| 4 | `DEADLINE_EXCEEDED` | Supplier didn't respond in time. Do **not** blindly retry a booking — check state first. |

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

**`InvalidArgument` naming `LANGUAGE_CODE` / `ALLOWED_LANGS`.** The `language_code` you sent
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

**`participant_info` rejected.** Work through `booking-form.md`. The recurring causes are:
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

**`cancel_check_code` isn't `CAN_BE_CANCELLED`.** Each value has a distinct meaning; see the
table in `flow.md`. Notably `ALREADY_CANCELLED` is a terminal, benign state — not something
to retry — and `SHOULD_DECLINE_INSTEAD_OF_CANCEL` means the booking is a `REQUEST` still
awaiting review, which is a decline flow rather than a cancellation.

**`CANCEL_PENDING`.** Not a failure. Some suppliers cancel asynchronously. Poll
`get-booking` until the booking status leaves `CANCEL_PENDING`. Do **not** retry
`final-cancel-booking` while pending.

**`CANCEL_FAILED` with a `failed_reason`.** The supplier refused. Read `failed_reason`; it
is passed through from the supplier and is usually specific.

**Cancelling a bundle child directly fails.** Bundle child bookings are generally not
directly cancellable. Cancel the parent; `FinalCancelBookingResponse.children_results[]`
reports each child's outcome.

**Refund amount differs from the quote.** `start-cancel-booking` gives an indicative figure.
The actual fee is always recomputed server-side at cancel time, and crossing a
`CancellationRule` boundary between quote and commit changes it. Quote and commit close
together, and reconcile against the figures in `FinalCancelBookingResponse` /
`get-booking`'s `cancel_refund`.

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

**`UpdateBookingParticipantInfoRequest.required` lists `id`, not `booking_id`.** The declared
property is `booking_id`. Send `booking_id`. A generated client emitting `id` is the cause of
an otherwise inexplicable `InvalidArgument`.

**`session_id` vs `booking_session_id` vs `booking_session_ids`.** `StartBookingResponse`
calls it `session_id`; `FinalBookingRequest` calls it `booking_session_id`; and
`CancelReservationsRequest` takes an array named `booking_session_ids`. Same value, three
field names.

**`display_currency` vs `display_currency_code`.** `search-activities`,
`get-activity-detail`, `get-price-and-availability-calendar` and
`check-availability-and-calculate-amount` all use `display_currency`. `start-booking` uses
`display_currency_code`. Sending the wrong one means the parameter is silently ignored and
you get the OTA's default currency instead.

**`expiry` has two formats.** `StartBookingResponse.expiry` is RFC 3339;
`ListReservationsResponse.BookingSession.expiry` is Unix seconds as a string.

**The `Prefecture` enum is defined as `Perfecture`.** Misspelled in the schema; the query
parameter is correctly `prefecture` and the values are identical. Only affects generated
model class names.

**`TEMPLES_SHINES`.** The `TravelProductCategory` value is spelled `SHINES`, not `SHRINES`.
Send it as spelled.

**Async final-booking types with no endpoint.** `AsyncFinalBookingResponse`,
`GetFinalBookingStatusResponse` and `AsyncFinalBookingStatus` are defined in `definitions`
but **no path exposes them**. Don't code against them; confirm availability with Linktivity.

**Named enum types whose values are inlined at each use site.** `BookingModel.Status`,
`CancelCheckCode`, `CancelBookingStatus`, `IssuedStatus`, `RefundRuleType`, `QRCodeCodeType`,
`cancellation.CancelReason` and `Perfecture` all exist as named definitions, but every
operation and object that uses them repeats the value list inline instead of `$ref`-ing the
definition. Consequence for code generation: you get a separate anonymous enum type per field
rather than one shared type, so a value you can assign in one place won't type-check in
another. Either post-process your generated client to collapse them, or hand-write the enums
from `enums.md`. Of the 119 definitions, only `ParentBooking` and the three async types are
genuinely unreachable; these eight are reachable by value, just not by reference.

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

Include in the report: the full `rpc.Status` body with `details[]`, the `timestamp` header
value, the endpoint path, `agent_booking_id` and `booking_id` where applicable, and whether
it is sandbox or production. Never include the API key secret.
