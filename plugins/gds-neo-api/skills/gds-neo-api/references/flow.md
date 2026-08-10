# End-to-end integration flow

## The shape of the integration

There are four stages, and the API is designed to be walked in order. Skipping a stage is
possible but leads to avoidable failures, because each stage produces IDs that the next one
requires.

```
1. Discover     list-suppliers                          → supplier_id
                search-activities                       → activity_id
                get-activity-detail                     → plan_id, plan_item_id,
                                                          plan_unit_id, booking_form,
                                                          cancellation_policy
2. Price        get-price-and-availability-calendar     → which dates are bookable
                check-availability-and-calculate-amount → exact amount for a unit mix
3. Book         start-booking                           → session_id  (holds inventory)
                final-booking                           → booking_id  (commits)
                cancel-reservations                      (releases an abandoned session)
4. Manage       get-booking / list-bookings             → status, vouchers, QR codes
                update-booking-participant-info         → correct traveler details
                start-cancel-booking                    → refund quote
                final-cancel-booking                    → commits the cancellation
```

## Stage 1 — discovery

`list-suppliers` returns every supplier contracted to your OTA in one response, with no
pagination. Each entry gives you both a numeric internal `id` and a stable human-readable
`supplier_id` (e.g. `SKYTREE`, `SAGANO`, `JRWEST`). **Always use `supplier_id`** for
filtering and for anything you persist; the numeric `id` is an internal handle.

`search-activities` is cursor-paginated. `page_size` is the only required parameter and
must be ≥ 1. To page, pass the previous response's `next_cursor` back as `cursor`; stop
when `next_cursor` comes back empty. `total` tells you the full match count. Do not build
offset arithmetic on top of the cursor — it is opaque.

`get-activity-detail` is where the data you actually need to book comes from. It returns
the `Activity` with its `plans[]`, and each plan carries:

- `units[]` — the participant types, each with a `plan_unit_id`. This is the ID you put in
  `plan_unit_items[].id` when booking.
- `plan_items[]` — the bookable start times, each with a `plan_item_id`, an optional
  `start_time` (`HH:MM` local) and an optional `cutoff_time`.
- `booking_rule` — `confirmation_type`, plus the booking window and deadline.
- `booking_form` — which traveler fields you must collect. See `booking-form.md`.
- `min_capacity_inclusive` / `max_capacity_inclusive` — the allowed total unit count.
- `voucher_expiration_period` — when the issued voucher stops being valid.

The response's `cancellation_policy` sits at the top level of `GetActivityDetailResponse`,
not inside the plan.

If you omit `language_code`, text fields come back populated for **every** available
language in their `i18n_text` map. Passing a specific `language_code` narrows this and makes
responses substantially smaller — worth doing in production.

## Stage 2 — pricing and availability

Two endpoints, used for different questions.

`get-price-and-availability-calendar` (GET) answers *"which dates can I sell?"* across a
range. `language_code`, `activity_id`, `target_date_from` and `target_date_to` are all
required; dates are `YYYY-MM-DD` and `from` must be ≤ `to`. Omitting `plan_id` returns every
plan under the activity. The response nests
`plans[] → days[] → plan_items[] → units[]`, and each unit carries
`availability_status` (`OK` / `NG`), `allotment_quantity`, `allotment_type`, and prices.

`allotment_type` matters for how you interpret `allotment_quantity`:

| Value | Meaning |
| --- | --- |
| `PLAN_ITEM_SHARED` | One pool shared across start times — booking the 10:00 slot reduces what's left at 14:00. |
| `UNIT_SHARED` | One pool shared across units — adult and child draw from the same count. |
| `PLAN_ITEM_AND_UNIT_SHARED` | Shared across both dimensions. |
| `INDEPENDENT` | This unit on this start time has its own count. |

Summing `allotment_quantity` across units under a shared type will overcount what you can
actually sell.

`check-availability-and-calculate-amount` (POST) answers *"what does exactly this cost,
right now?"* for one date and one unit mix. Required: `language_code`, `activity_id`,
`plan_id`, `plan_item_id`, `target_date`. `units[]` carries `{plan_unit_id, request_quantity}`
pairs. This is the call to make immediately before showing a total to a traveler, because
the calendar's prices are indicative and this one applies the actual quantity-dependent
calculation.

The response gives three price figures per plan item, but under different names than the
booking endpoints use: `original_amount` (the supplier's currency), `display_amount` and
`payment_amount`. They correspond to `supplier_currency_price`, `display_currency_price` and
`payment_currency_price` respectively — see "Currencies" below for which to use. The calendar
endpoint's `unit` objects carry only `display_amount` and `payment_amount`, with no
supplier-currency figure.

## Stage 3 — booking (two-phase)

### Phase 1: `start-booking`

Holds inventory and returns a `session_id`. Nothing is sold yet.

Required fields: `language_code`, `country_code`, `activity_id`, `plan_id`, `plan_item_id`,
`plan_unit_items`, `display_currency_code`.

`target_date` is required **unless** the plan's `confirmation_type` is
`FREE_SALE_OPEN_DATE` — open-date products have no participation date to specify.

`plan_unit_items[]` is `{id, count}` where `id` is a `plan_unit_id` from
`get-activity-detail`. Respect `min_capacity_inclusive` / `max_capacity_inclusive`. Units
with `include_in_capacity: false` (typically infants) do **not** count toward the minimum —
the spec describes the flag as "count as minimum booking capacity or not", so it is defined
against the minimum only and says nothing about the maximum. Compute the minimum check from
capacity-counted units and the maximum check from the raw total, and if a booking sits near
the maximum with non-capacity units in it, confirm the intended behaviour with Linktivity.
Separately, units with `can_be_book_independently: false` (typically children) cannot be the
only thing in the basket.

`language_code` must be one of the languages configured on the activity
(`activity.language_codes`). If it isn't, the call fails with `InvalidArgument` and an
`ErrorInfo` in `details[]` carrying `LANGUAGE_CODE`, `ALLOWED_LANGS` and `ACTIVITY_ID`.
This is a frequent first-integration failure.

`participant_info` carries traveler details, shaped by the plan's `booking_form`. See
`booking-form.md` — this is the most error-prone part of the payload.

`agent_booking_id` is your own reference; it is stored, returned on the booking, and is
filterable in `list-bookings`. Set it — it is how you reconcile against your own system.
`agent_reservation_note` is free-text for your own use.

`idempotent_key` is optional but strongly recommended. Two consecutive successful
`start-booking` calls with the same key return the **same** `session_id` instead of holding
inventory twice. Maximum 64 characters; longer keys are rejected. The key is honoured for
24 hours, so to deliberately start a fresh attempt (e.g. a previous one is stuck), send a
new key.

The response gives you `session_id`, `booking_custom_id`, the three price figures,
`expiry` (RFC 3339), `booking_rule`, and `unit_prices[]` with a per-unit breakdown.

### The session expiry window

`expiry` is normally supplied by the supplier's booking adapter. When the adapter does not
provide one, a **15-minute fallback** applies. Treat 15 minutes as your planning floor,
not a guarantee — read the actual `expiry` and drive your checkout timer from it.

Sessions you neither confirm nor cancel keep occupying your pending-reservation allowance.
The intended pattern is:

- Traveler abandons checkout, or your payment step fails → `cancel-reservations` with that
  session id in `booking_session_ids[]`.
- On startup or on a schedule → `list-reservations` to find orphaned sessions and release
  them in a batch.

`cancel-reservations` takes `booking_session_ids[]` and cancels them in one call. Its
success response body is an empty object.

### Phase 2: `final-booking`

Takes exactly one field, `booking_session_id`, and returns `booking_id` — e.g.
`PRIVATE-20260212-WR2F2VPA`. That `booking_id` is the handle for everything afterwards.

The `session_id` from `start-booking` and the `booking_session_id` here are the same value;
the field is just named differently on the two sides. This inconsistency causes real bugs
in strongly-typed clients.

If `final-booking` fails or times out, **do not blindly retry** — a successful confirmation
also removes the session from `list-reservations`, so "session gone" alone does not mean
"nothing was created". Determine state in this order:

1. `list-reservations` — session still there? It did not confirm. Retry `final-booking` on
   the same session while `expiry` allows.
2. Session gone → `list-bookings` filtered by your `agent_booking_id`. A booking there means
   it succeeded and you lost the response; take the `booking_id` from it.
3. Neither → nothing was created. Start over from `start-booking` with a **new**
   `idempotent_key`.

Step 2 only works if you set `agent_booking_id` on `start-booking`. There is no
`session_id` or `booking_custom_id` filter on `list-bookings` and `external.BookingInfo`
carries neither, so without `agent_booking_id` there is no documented way to find a booking
whose id you never received — you would have to ask Linktivity. Set it on every booking.

### `confirmation_type` changes what confirmation means

| Value | Behaviour |
| --- | --- |
| `FREE_SALE` | Specific date, unlimited inventory. Confirms immediately. |
| `FREE_SALE_OPEN_DATE` | No date required, unlimited inventory. Confirms immediately. Omit `target_date`. |
| `INVENTORY` | Specific date, finite inventory. Confirms immediately if stock is held. |
| `REQUEST` | Specific date, requires manual supplier review. `final-booking` returns a `booking_id` whose status is `REQUEST_PENDING`, **not** `CONFIRMED`. |

For `REQUEST` products you must poll `get-booking` (or `list-bookings` filtered by
`booking_status`) until the status settles to `CONFIRMED` or `REQUEST_REJECTED`. Do not
show the traveler a confirmed booking on the strength of a `booking_id` alone.

## Stage 4 — post-booking management

`get-booking` takes `booking_id` and returns the full picture: `booking_info`,
`voucher_urls`, `cancel_refund` (populated once cancelled), `participant_info`, `prices`,
`qrcode`, and `is_cancellable_now`.

`is_cancellable_now` is evaluated at read time after refreshing from the supplier, without
holding a lock. It is a strong hint, not a guarantee — a subsequent cancellation can still
fail. Bundle **child** bookings are generally not directly cancellable; cancel them through
the parent.

`voucher_urls` has four always-present URLs (`mobile_html_url`, `mobile_pdf_url`,
`printable_html_url`, `printable_pdf_url`) plus `redemption_url`, which appears **only**
when the activity has it configured. Treat its absence as normal, not as an error.

`list-bookings` is offset-paginated: `page_no` starts at 1, with `page_size`. Filters
include `booking_id[]`, `agent_booking_id[]`, `supplier_booking_id[]`, `booking_at_start`,
`booking_at_end`, and `booking_status[]`. `order_bys` accepts `field|direction` strings but
today only `booking_at` is sortable; the default is `booking_at` descending.

The timestamp filters are RFC 3339. When you include a timezone offset like `+09:00`, the
`+` **must** be percent-encoded as `%2B` in the query string, or it will be parsed as a
space and the filter will silently misbehave.

`update-booking-participant-info` takes `booking_id` and `participant_info` and
**completely overwrites** the stored participant information. Read the current values from
`get-booking` first and send the full merged object — a partial payload deletes whatever
you left out. New voucher URLs come back in the response, so re-fetch or re-issue vouchers
after an update.

## Cancellation (two-phase)

`start-cancel-booking` takes `booking_id` and returns:

- `cancel_check_code` — whether cancellation is permitted at all.
- `cancel_refund_display` — the refund and fee breakdown in all three currencies, plus
  `refund_rule_type` and `cancel_at`.
- `child_cancel_refund_display[]` — per-child breakdown, bundle bookings only.

`cancel_check_code` values:

| Value | Meaning |
| --- | --- |
| `CAN_BE_CANCELLED` | Proceed to `final-cancel-booking`. |
| `ALREADY_CANCELLED` | Nothing to do. Not an error condition to retry. |
| `CAN_NOT_CANCEL` | Policy forbids it. Check `cancellation_policy` from `get-activity-detail`. |
| `BOOKING_EXPIRED` | The voucher has passed its expiration. |
| `SHOULD_DECLINE_INSTEAD_OF_CANCEL` | A `REQUEST` booking still pending review — decline it rather than cancel. |

Show the traveler the fee from `cancel_refund_display` and get their agreement **before**
calling phase two. The quoted figure is indicative: the actual fee is always recomputed
server-side at cancel time.

`final-cancel-booking` requires `booking_id` and `cancel_by` (an identifier for whoever
initiated it — a person's name or an operator ID). `cancel_reason` and `comment` are
optional; `cancel_reason` is an enum, see `enums.md`.

Its response is a `parent_result` plus `children_results[]` (empty for non-bundle
bookings). Each result has a `status` of `CANCEL_SUCCEED`, `CANCEL_PENDING`, or
`CANCEL_FAILED`, with `failed_reason` populated on failure.

**`CANCEL_PENDING` is not a failure.** Some suppliers cancel asynchronously. Poll
`get-booking` until the booking status leaves `CANCEL_PENDING` and settles to
`CANCELLED_BY_TRAVELER` or `CANCEL_FAILED`. Do not retry `final-cancel-booking` while it
is pending — you risk double-cancellation handling on the supplier side.

## Booking status model

`booking_status` (also `BookingModel.Status`) on a confirmed booking:

| Status | Meaning |
| --- | --- |
| `REQUEST_PENDING` | Awaiting supplier review (`REQUEST` products). |
| `REQUEST_REJECTED` | Supplier declined the request. |
| `CONFIRMED` | Booked and confirmed. Covers both instant products and approved requests. |
| `CANCELLED_BY_TRAVELER` | Cancelled from your side. |
| `CANCELLED_BY_SUPPLIER` | Cancelled by the supplier. |
| `CANCEL_PENDING` | Cancellation in flight at the supplier. |
| `CANCEL_FAILED` | Cancellation attempted and failed. |
| `INVALID` | Invalid record. |
| `UNDEFINED` | Reserved; should not appear in practice. |

Separately, `issued_status` tracks voucher redemption: `DISABLE` (not applicable),
`NOT_ISSUED` (booked, vouchers not yet issued), `PARTIAL` (some units redeemed), `ISSUED`
(all redeemed, or expired and no longer usable). `PARTIAL` and `ISSUED` are about
redemption, not about booking success.

## Currencies

Three price figures accompany most monetary responses, and they answer three different
questions:

| Field | Meaning |
| --- | --- |
| `supplier_currency_price` | The supplier's own currency — the authoritative original amount (e.g. JPY for a Japanese attraction). |
| `payment_currency_price` | Converted by LINK into your OTA settlement currency. **This is what you are billed.** |
| `display_currency_price` | Converted into whatever you asked for via `display_currency_code`, for showing the traveler. |

Reconcile against `payment_currency_price`. `display_currency_price` is presentation only —
if you have no need to display a converted price, set `display_currency_code` to a fixed
currency such as `JPY` and ignore the field.

Each price object carries `net` and `gross`. `net` is your cost, `gross` is the retail
figure; the difference is your margin. `CancelRefundDisplay.Price` extends this with
`net_refund`, `gross_refund`, and `cancel_fee`.

Naming varies by endpoint and there is no single convention: booking endpoints use
`*_currency_price`, `check-availability-and-calculate-amount` uses `original_amount` /
`display_amount` / `payment_amount`, the calendar's `unit` uses `display_amount` /
`payment_amount`, and `search-activities` overviews use a bare
`price_exchanges` map of currency → number with no net/gross split at all. Map them onto the
three concepts above rather than expecting consistent field names.

## Async final-booking (present in schemas, not in the documented paths)

The spec defines `AsyncFinalBookingResponse`, `GetFinalBookingStatusResponse`, and
`AsyncFinalBookingStatus` (whose values carry the full `ASYNC_FINAL_BOOKING_STATUS_` prefix:
`_ACCEPTED` → `_PROCESSING` → `_COMPLETED` / `_FAILED`), and
`GetFinalBookingStatusResponse` includes a `can_retry` flag meaning it is safe to retry via
`start-booking` then `AsyncFinalBooking`. However **no path in the published spec exposes
these** — there is no async endpoint in the 14 documented operations.

If an integrator asks about async booking, tell them the types exist in the schema but the
endpoints are not in the published API, and to confirm availability with Linktivity rather
than coding against them.
