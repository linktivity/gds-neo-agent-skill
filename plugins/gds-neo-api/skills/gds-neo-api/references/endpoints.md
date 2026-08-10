# Endpoint reference

All paths are relative to the environment base URL (see `auth.md`). All 14 operations
require the five auth headers. Every operation returns `rpc.Status` for `4xx` and `5xx`.

Enum-typed parameters are listed by their enum name; the value lists are in `enums.md`.
Every enum-typed **query parameter** in this API defaults to `UNDEFINED`, meaning
"unspecified / no filter" — not a real value to send deliberately. Enum-typed **body** fields
have their own defaults, which are not always `UNDEFINED` (`cancellation.CancelReason`
defaults to `UNKNOWN`, `CollectingTiming` to `ON_BOOKING`, and so on); check `enums.md`.

---

## Partner

### `GET /v1/partner/list-suppliers` — ListContractedSuppliers

Returns the full set in one response; no pagination and no parameters.

**Response** `ListContractedSuppliersResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `supplier_summaries[]` | `SupplierSummary` | Suppliers contracted with this OTA. **Order is not guaranteed.** |

---

## Activity

### `GET /v1/activity/search-activities` — SearchActivities

Paginated list of activity overviews. Use `next_cursor` from the response to fetch the
following page.

| Parameter | In | Required | Type | Notes |
| --- | --- | --- | --- | --- |
| `page_size` | query | **yes** | int32 | Max activities per response. Must be ≥ 1. |
| `cursor` | query | no | string | Pass the previous response's `next_cursor`. Opaque. |
| `supplier_ids` | query | no | string[] | Repeat the param per value (`collectionFormat: multi`). e.g. `SKYTREE`, `SAGANO`, `JRWEST`. |
| `activity_ids` | query | no | string[] | Limit to specific activity ids. Multi. |
| `query` | query | no | string | Free-text keyword matched against the activity title. Language-sensitive. |
| `language_code` | query | no | `Language` | Display language for text in the response. **If unset, results come back in every available language.** |
| `display_currency` | query | no | `CurrencyCode` | ISO-4217 code for `price` fields. Defaults to the OTA's configured currency. |
| `categories` | query | no | `TravelProductCategory[]` | Multi. |
| `country` | query | no | `CountryCode` | |
| `prefecture` | query | no | `Prefecture` | Japanese prefecture. |
| `confirmation_type` | query | no | `ConfirmationType` | |

**Response** `SearchActivitiesResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `activities[]` | `SearchActivitiesResponse.ActivityOverview` | |
| `total` | int32 | Total matches across all pages. |
| `next_cursor` | string | Empty when there are no more pages. |

### `GET /v1/activity/get-activity-detail` — GetActivityDetail

Use this to populate a product detail page, and to obtain the IDs and form definition
needed to book.

| Parameter | In | Required | Type | Notes |
| --- | --- | --- | --- | --- |
| `activity_id` | query | **yes** | string | From `search-activities`. |
| `plan_id` | query | no | string | Limit to one plan. If omitted, every plan is returned. |
| `language_code` | query | no | `Language` | If unset, every available language is returned. |
| `display_currency` | query | no | `CurrencyCode` | |

**Response** `GetActivityDetailResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `activity` | `Activity` | Includes `plans[]` of `GetActivityDetailResponse.Plan`. |
| `cancellation_policy` | `external.CancellationPolicy` | Top level, **not** per plan. |

---

## Availability

### `GET /v1/price/get-price-and-availability-calendar` — GetPriceAndAvailabilityCalendar

Availability calendar extended with price information, per date.

| Parameter | In | Required | Type | Notes |
| --- | --- | --- | --- | --- |
| `language_code` | query | **yes** | `Language` | Note: required here, optional on the activity endpoints. |
| `activity_id` | query | **yes** | string | |
| `target_date_from` | query | **yes** | string | `YYYY-MM-DD`, inclusive. Must be ≤ `target_date_to`. |
| `target_date_to` | query | **yes** | string | `YYYY-MM-DD`, inclusive. |
| `plan_id` | query | no | string | If omitted, every plan under the activity is returned. |
| `display_currency` | query | no | `CurrencyCode` | |

**Response** `GetPriceAndAvailabilityCalendarResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `activity_id` | string | Required in response. |
| `activity_name` | string | Required in response. |
| `plans[]` | `plan` | Nests `days[] → plan_items[] → units[]`. |
| `language_code` | `Language` | Required in response. |

### `POST /v1/price/check-availability-and-calculate-amount` — CheckAvailabilityAndCalculateAmount

Availability and calculated amount for one specific date and unit mix.

**Body** `CheckAvailabilityAndCalculateAmountRequest`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `language_code` | **yes** | `Language` | |
| `activity_id` | **yes** | string | |
| `plan_id` | **yes** | string | |
| `plan_item_id` | **yes** | string | The start-time item. |
| `target_date` | **yes** | string | `yyyy-MM-dd`. |
| `units[]` | no | `unitRequest` | `{plan_unit_id, request_quantity}`, both required within each element. |
| `display_currency` | no | `CurrencyCode` | |

```json
{
  "language_code": "ENGLISH",
  "activity_id": "LINKTIVITY-1QCOC",
  "plan_id": "FUJIQHL-1QCOZ-1",
  "plan_item_id": "LINKTIVITY-1QCOC-1-1",
  "target_date": "2026-08-12",
  "units": [
    { "plan_unit_id": "EggKAggSEgIIQQ==", "request_quantity": 2 },
    { "plan_unit_id": "CAMSBgoAEgIIEg==", "request_quantity": 1 }
  ],
  "display_currency": "JPY"
}
```

**Response** `CheckAvailabilityAndCalculateAmountResponse` — `activity_id`, `activity_name`,
`plan_id`, `plan_name`, `target_date`, `language_code` (all required in the response) plus
`plan_items[]` of `CheckAvailabilityAndCalculateAmountResponse.planItem`, each carrying
`availability_status` and `original_amount` / `display_amount` / `payment_amount`.

---

## Booking

### `POST /v1/booking/ota/start-booking` — StartBooking

Phase 1 of booking (Reserve). Returns a `session_id` required by `final-booking`.

**Body** `StartBookingRequest`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `language_code` | **yes** | `Language` | Response and voucher language. **Must be one of the activity's configured languages** or the call fails with `InvalidArgument` + `ErrorInfo` carrying `LANGUAGE_CODE`, `ALLOWED_LANGS`, `ACTIVITY_ID`. |
| `country_code` | **yes** | `CountryCode` | Traveler's country, ISO 3166-1 alpha-3. |
| `activity_id` | **yes** | string | e.g. `LINKTIVITY-1QCOC`. |
| `plan_id` | **yes** | string | e.g. `FUJIQHL-1QCOZ-1`. |
| `plan_item_id` | **yes** | string | Start-time id, e.g. `LINKTIVITY-1QCOC-1-1`. |
| `plan_unit_items[]` | **yes** | `CustomIdCount` | `{id, count}` — participant type and quantity. `id` is a `plan_unit_id` from `get-activity-detail` (equivalently `unit.custom_id`), sent back verbatim. The published example uses a different id shape here than everywhere else in the spec — see `booking-form.md`. |
| `display_currency_code` | **yes** | `CurrencyCode` | Drives `display_currency_price` in the response. |
| `target_date` | conditional | string | `YYYY-MM-DD` in the activity's timezone. Required **unless** `confirmation_type` is `FREE_SALE_OPEN_DATE`. |
| `participant_info` | conditional | `ParticipantInfo` | Marked optional in the schema, but required in practice for any plan whose `booking_form` asks for anything — and if you send the object at all, `first_name` and `last_name` are required inside it. Shaped by the plan's `booking_form`. See `booking-form.md`. |
| `agent_booking_id` | no | string | Your own reference. Filterable in `list-bookings`. |
| `agent_reservation_note` | no | string | Free-text, your own use. |
| `idempotent_key` | no | string | Max 64 chars; longer is rejected. Same key → same `session_id`. Effective 24 hours. |

```json
{
  "language_code": "JAPANESE",
  "country_code": "JPN",
  "activity_id": "LINKTIVITY-1QCOC",
  "plan_id": "FUJIQHL-1QCOZ-1",
  "plan_item_id": "LINKTIVITY-1QCOC-1-1",
  "target_date": "2026-08-12",
  "plan_unit_items": [
    { "id": "EggKAggSEgIIQQ==", "count": 2 },
    { "id": "CAMSBgoAEgIIEg==", "count": 1 }
  ],
  "display_currency_code": "JPY",
  "agent_booking_id": "AGENT-BOOKING-1QCOC",
  "idempotent_key": "checkout-8f3a1c9e-2026-08-06",
  "participant_info": {
    "first_name": "San",
    "last_name": "Zhang",
    "booking_representative_fields": {
      "participant_email_address": "traveler@example.com"
    }
  }
}
```

**Response** `StartBookingResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `session_id` | string | Pass to `final-booking` or `cancel-reservations`. |
| `booking_custom_id` | string | e.g. `PRIVATE-20260212-8PUQT8B5`. |
| `supplier_currency_price` | `price.Price` | |
| `payment_currency_price` | `price.Price` | What you are billed. |
| `display_currency_price` | `price.Price` | For traveler display. |
| `expiry` | date-time | RFC 3339. Normally non-null; **15-minute fallback** if the adapter provides none. |
| `booking_rule` | `BookingRule` | |
| `unit_prices[]` | `UnitPrice` | Per-unit breakdown with full `unit.Unit` detail. |

### `GET /v1/booking/ota/list-reservations` — ListReservations

All pending reservation sessions for the current OTA account. No parameters.

**Response** `ListReservationsResponse` → `sessions[]` of
`ListReservationsResponse.BookingSession`, each with `session_id`, `expiry` (Unix seconds,
int64 as string), `language_code`, `activity_id`, `plan_id`, `activity_title`, `plan_title`,
`target_date`, `participant_last_name`, `participant_first_name`,
`participant_email_address`, `agent_booking_id`.

### `POST /v1/booking/ota/final-booking` — FinalBooking

Phase 2 of booking (Confirm).

**Body** `FinalBookingRequest`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `booking_session_id` | **yes** | string | The `session_id` from `start-booking`. |

**Response** `FinalBookingResponse` → `booking_id`, e.g. `PRIVATE-20260212-WR2F2VPA`.

For `REQUEST`-type products the resulting booking status is `REQUEST_PENDING`, not
`CONFIRMED`. See `flow.md`.

### `POST /v1/booking/ota/cancel-reservations` — CancelReservations

Releases pending sessions in batch, so you don't hit the pending-reservation limit.

**Body** `CancelReservationsRequest`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `booking_session_ids[]` | **yes** | string[] | Session ids from `start-booking` or `list-reservations`. |

**Response** empty object `{}` on success.

### `GET /v1/booking/ota/get-booking` — GetBooking

| Parameter | In | Required | Type |
| --- | --- | --- | --- |
| `booking_id` | query | **yes** | string |

**Response** `GetBookingResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `booking_info` | `external.BookingInfo` | |
| `voucher_urls` | `VoucherUrls` | `redemption_url` present only when configured on the activity. |
| `cancel_refund` | `external.CancelRefundDisplay` | Populated once cancelled. |
| `participant_info` | `ParticipantInfo` | Field-by-field breakdown is in `booking-form.md`, not `schemas.md`. |
| `prices` | `Prices` | All three currency views. |
| `qrcode` | `external.QRCode` | `per_booking` and/or `per_participant[]`. |
| `is_cancellable_now` | boolean | Evaluated at read time without a lock — a hint, not a guarantee. Bundle children generally not directly cancellable. |

### `GET /v1/booking/ota/list-bookings` — ListBookings

Offset-paginated, filterable.

| Parameter | In | Required | Type | Notes |
| --- | --- | --- | --- | --- |
| `page_no` | query | no | int32 | Starts at 1. |
| `page_size` | query | no | int32 | No default or maximum is documented. Set it explicitly rather than relying on the server's choice. |
| `order_bys` | query | no | string[] | `field_name\|direction`; `direction` is `asc` or `desc`, default `asc`. **Only `booking_at` is sortable today.** Overall default is `booking_at desc`. |
| `booking_id` | query | no | string[] | Multi. |
| `agent_booking_id` | query | no | string[] | Multi. |
| `supplier_booking_id` | query | no | string[] | Multi. |
| `booking_at_start` | query | no | date-time | RFC 3339. **Percent-encode `+` as `%2B`** for offsets like `+09:00`. |
| `booking_at_end` | query | no | date-time | Same encoding caveat. |
| `booking_status` | query | no | `BookingModel.Status[]` | Multi; matches any of the given statuses. |

**Response** `ListBookingsResponse` → `page_no`, `page_size`, `total`, `bookings[]` of
`external.BookingInfo`.

### `POST /v1/booking/ota/update-booking-participant-info` — UpdateBookingParticipantInfo

**Body** `UpdateBookingParticipantInfoRequest`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `booking_id` | **yes** | string | |
| `participant_info` | **yes** | `ParticipantInfo` | **Completely overwrites** the existing participant information. Field-by-field breakdown in `booking-form.md`. |

Spec quirk: the schema's `required` array lists `["id", "participant_info"]` while the
declared property is `booking_id`. Send `booking_id` — that is the documented property, and
the endpoint description refers to "booking `id`". If a generated client emits `id`, that
is the cause.

**Response** `UpdateBookingParticipantInfoResponse` → `voucher_urls` (refreshed after the
change; re-issue vouchers).

### `POST /v1/booking/ota/start-cancel-booking` — StartCancelBooking

Phase 1 of cancellation. Quotes, does not commit.

**Body** `StartCancelBookingRequest`

| Field | Required | Type |
| --- | --- | --- |
| `booking_id` | **yes** | string |

**Response** `StartCancelBookingResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `cancel_check_code` | `CancelCheckCode` | Gate on this before phase 2. |
| `cancel_refund_display` | `external.CancelRefundDisplay` | Refund and fee in all three currencies. |
| `child_cancel_refund_display[]` | `external.CancelRefundDisplay` | Bundle bookings only. |

### `POST /v1/booking/ota/final-cancel-booking` — FinalCancelBooking

Phase 2 of cancellation. Commits.

**Body** `FinalCancelBookingRequest`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `booking_id` | **yes** | string | |
| `cancel_by` | **yes** | string | Who initiated it, e.g. `Gary Chen` or an operator id. |
| `cancel_reason` | no | `cancellation.CancelReason` | Enum; send the string name. |
| `comment` | no | string | Free-text note. |

```json
{
  "booking_id": "PRIVATE-20260212-WR2F2VHE",
  "cancel_reason": "PARTICIPANT_OR_DATE_CHANGE",
  "comment": "Customer requested cancellation due to change in travel plans.",
  "cancel_by": "Gary Chen"
}
```

**Response** `FinalCancelBookingResponse`

| Field | Type | Notes |
| --- | --- | --- |
| `parent_result` | `Result` | For non-bundle bookings this is the only result. |
| `children_results[]` | `Result` | Empty for non-bundle bookings. |

`Result` is `{booking_id, status, failed_reason}` where `status` is `CANCEL_SUCCEED`,
`CANCEL_PENDING`, or `CANCEL_FAILED`, and `failed_reason` appears only on failure.
`CANCEL_PENDING` means poll `get-booking`; do not retry.
