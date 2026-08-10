# Schema reference

Object definitions from the spec. Enum value lists live in `enums.md`; the booking form and
`participant_info` payload are covered in depth in `booking-form.md`.

Field names are exactly as they appear on the wire (snake_case). Where the spec marks a
field `required`, it is noted — note that for many response objects the spec marks fields
required meaning "always present in the response", not "you must send it".

---

## Shared building blocks

### `Text` — internationalised string

Almost every human-readable field is a `Text`, not a plain string.

| Field | Type | Notes |
| --- | --- | --- |
| `text` | string | Default / fallback text. |
| `i18n_text` | map<string,string> | Key is the **`Language` enum name as a string** — `"ENGLISH"`, `"JAPANESE"`, `"SIMPLIFIED_CHINESE"` — not an IETF tag like `en-US`. |

```json
{ "text": "AGE_CHILD", "i18n_text": { "JAPANESE": "子供 (0-18歳)", "TRADITIONAL_CHINESE": "兒童 (0-18歳)" } }
```

If you requested a specific `language_code`, expect one entry. If you omitted it, expect
every configured language. Fall back to `text` when your language is absent.

Watch out: `LocalizedValue` (used inside `Choice`) uses a **different** convention —
lowercase IETF-ish tags like `"en-us"`, `"ja-jp"`, `"ko-kr"`, `"zh-hans"`, `"zh-hant"`. The
two are not interchangeable.

### `price.Price`

| Field | Type | Notes |
| --- | --- | --- |
| `net` | double | Your cost. |
| `gross` | double | Retail figure. `gross - net` is your margin. |
| `currency_code` | `CurrencyCode` | |

### `Prices` — the three-currency view

| Field | Type |
| --- | --- |
| `supplier_currency_price` | `price.Price` |
| `payment_currency_price` | `price.Price` |
| `display_currency_price` | `price.Price` |

See `flow.md` for which to reconcile against (`payment_currency_price`).

### `Attachment`

| Field | Type | Notes |
| --- | --- | --- |
| `attachment_type` | `FileType` | `PDF`, `IMAGE`, `VIDEO`, `HTML`. |
| `caption` | string | Title or note. |
| `url` | string | Downloadable or browsable link. |

### `Media`

| Field | Type |
| --- | --- |
| `thumbnail` | string (URL) |
| `images[]` | `Attachment` |
| `videos[]` | `Attachment` |

### `PreciseLocation`

| Field | Type | Notes |
| --- | --- | --- |
| `title` | `Text` | |
| `description` | `Text` | |
| `coordinate` | `PreciseLocation.LatLng` | `{lat, lon}` doubles. `lat` ∈ [-90, 90], `lon` ∈ [-180, 180]. Note the field is `lon`, not `lng`. |
| `address` | `Text` | |
| `place_id` | string | Google Maps place id. |
| `country` | string | From Google Maps API. |
| `administrative_area_level_1` | string | From Google Maps API. |
| `locality` | string | From Google Maps API. |
| `postal_code` | string | From Google Maps API. |
| `attachments[]` | `Attachment` | |

### `SimpleLocation`

`{title: Text, description: Text}`. Used in search results where full geocoding isn't
returned. `SearchActivitiesResponse.ActivityOverview.origins[]` uses this, while
`Activity.origins[]` uses the richer `PreciseLocation` — the same conceptual field has
different types on the search and detail endpoints.

### Date and time helpers

| Type | Shape | Notes |
| --- | --- | --- |
| `neo_datetime.Date` | `{year, month, day}` int32 | `year` 1–9999, or 0 for year-independent. `day` may be 0 when not significant. |
| `DateRange` | `{start, end}` of `neo_datetime.Date` | Half-open: `[start, end)`. |
| `DatePeriod` | `{unit: PeriodUnit, value: int32}` | e.g. 30 `DAY`. |
| `DayOffset` | `{num_days: int32, time_of_day: string}` | `time_of_day` is `HH:MM` local. |
| `TimePoint` | `{anchor: Anchor, duration: string, day_offset: DayOffset}` | `duration` is a protobuf Duration string, negative = before the anchor, e.g. `-259200s` = 3 days before. |
| `UnitRange` | `{min_inclusive, max_inclusive}` int32 | Both inclusive. Usually an age range. |

---

## Partner

### `SupplierSummary`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string (int64) | Numeric internal identifier in GDS. Don't use externally. |
| `supplier_id` | string | Stable human-readable id — **use this one**. |
| `original_name` | string | Name in the supplier's local language. |
| `english_name` | string | May be empty if the supplier provided none. |

---

## Activity

### `SearchActivitiesResponse.ActivityOverview`

| Field | Type | Notes |
| --- | --- | --- |
| `activity_id` | string | |
| `supplier_id` | string | |
| `supplier_name` | string | |
| `title` | `Text` | |
| `description` | `Text` | |
| `thumbnail` | string (URL) | Plain string here, not `Media`. |
| `language_codes[]` | `Language` | Languages the activity supports. |
| `categories[]` | `TravelProductCategory` | |
| `plans[]` | `ActivityOverview.PlanOverview` | Summary only. |
| `origins[]` | `SimpleLocation` | |
| `start_date` | string | |
| `end_date` | string | |
| `booking_type` | `BookingType` | `SINGLE` or `BULK`. |
| `version` | string (int64) | |
| `updated_at` | date-time | |

### `ActivityOverview.PlanOverview`

| Field | Type | Notes |
| --- | --- | --- |
| `plan_id` | string | |
| `title` | `Text` | |
| `description` | `Text` | |
| `confirmation_type` | `ConfirmationType` | |
| `price_exchanges` | map<string,double> | Price keyed by currency. A bare number, not a `price.Price` — no net/gross split at overview level. |

### `Activity` (from `get-activity-detail`)

| Field | Type | Notes |
| --- | --- | --- |
| `activity_id` | string | |
| `supplier_id` / `supplier_name` | string | |
| `language_codes[]` | `Language` | **This is the list `StartBookingRequest.language_code` is validated against.** |
| `timezone` | string | IANA, e.g. `Asia/Tokyo`. All `target_date` values are interpreted here. |
| `original_currency` | `CurrencyCode` | |
| `title` / `description` | `Text` | |
| `categories[]` | `TravelProductCategory` | |
| `origins[]` / `destinations[]` | `PreciseLocation` | |
| `display_price` | `price.Price` | Reference price in the requested display currency. |
| `media` | `Media` | |
| `plans[]` | `GetActivityDetailResponse.Plan` | |
| `version` | string (int64) | |
| `updated_at` | date-time | |

### `GetActivityDetailResponse.Plan`

The most important object in the API — everything you need to book comes from here.

| Field | Type | Notes |
| --- | --- | --- |
| `plan_id` | string | |
| `supplier_id` / `supplier_name` | string | |
| `title` / `description` | `Text` | |
| `publication_period` | `DateRange` | When the plan is sellable. |
| `min_capacity_inclusive` | int32 | Minimum total booking units. |
| `max_capacity_inclusive` | int32 | Maximum total booking units. |
| `meetup_or_pickup_points[]` | `PreciseLocation` | |
| `dismissal_or_dropoff_points[]` | `PreciseLocation` | |
| `booking_rule` | `BookingRule` | `confirmation_type`, window, deadline. |
| `booking_form` | `external.BookingForm` | Which traveler fields to collect — see `booking-form.md`. |
| `checklist[]` | `CheckListItem` | Restrictions, what to bring, what's included. |
| `schedule[]` | `ItineraryItem` | |
| `faqs[]` | `FAQ` | `{question: Text, answer: Text}`. |
| `display_price` | `price.Price` | |
| `media` | `Media` | |
| `units[]` | `GetActivityDetailResponse.Unit` | **Source of `plan_unit_id`.** |
| `plan_items[]` | `GetActivityDetailResponse.PlanItem` | **Source of `plan_item_id`.** |
| `voucher_expiration_period` | `VoucherExpirationPeriod` | |
| `updated_at` | date-time | |

### `GetActivityDetailResponse.Unit`

| Field | Type | Notes |
| --- | --- | --- |
| `plan_unit_id` | string | Put this in `plan_unit_items[].id` and `user_information_fields[].plan_unit_id`. |
| `title` | `Text` | e.g. "Adult (18+)", "Child (6-11)". |
| `include_in_capacity` | boolean | `false` for units that don't count toward `min_capacity_inclusive` (typically infants). |
| `can_be_book_independently` | boolean | `false` means this unit cannot be booked alone (typically children need an accompanying adult). |
| `unit_type` | `UnitType` | |
| `range` | `UnitRange` | Normally an age range. |

### `GetActivityDetailResponse.PlanItem`

| Field | Type | Notes |
| --- | --- | --- |
| `plan_item_id` | string | Put this in `plan_item_id`. |
| `title` | `Text` | e.g. "10:00", "11:00", "Full Day". |
| `start_time` | string | `HH:MM` local, if the product has one. |
| `cutoff_time` | string | `HH:MM` local booking cutoff, if any. |

### `BookingRule`, `BookingPeriod`, `BookingDeadline`

| Type | Fields |
| --- | --- |
| `BookingRule` | `confirmation_type: ConfirmationType`, `booking_period: BookingPeriod`, `booking_deadline: BookingDeadline` |
| `BookingPeriod` | `amount: int32`, `unit: PeriodUnit` — how far ahead the product can be booked, e.g. 30 `DAY`. |
| `BookingDeadline` | `before_days: int32`, `deadline_time: string` — e.g. 1 day before at `23:00`. |

Together these define the bookable window. A request outside it is rejected even when
inventory exists.

### `CheckListItem`

`{type: CheckListItem.Type, title: Text, description: Text, pdf[]: Attachment, images[]: Attachment}`.
See `enums.md` for the `Type` values — they distinguish hard restrictions from
nice-to-haves and from what's included in the price.

### `ItineraryItem`

`{title: Text, description: Text, image: Attachment}`.

### `VoucherExpirationPeriod`

| Field | Type | Notes |
| --- | --- | --- |
| `type` | `VoucherExpirationPeriodType` | Read this first; it tells you which of the others applies. |
| `after_purchase_date` | `DatePeriod` | For `FROM_PURCHASE_DATE`. |
| `after_activity_date` | `DatePeriod` | For `FROM_ACTIVITY_DATE`, e.g. a metro 3-day pass. |
| `fixed_date` | string | `YYYY-MM-DD`, for `FIXED_DATE`. |
| `annual_fixed_date` | `AnnualFixedDate` | For `RELATIVE_FIXED_DATE`. |

`AnnualFixedDate` is `{annual_fixed_date, annual_cut_off_date}`, both `MM-DD`. The rule: the
voucher expires on `annual_fixed_date` each year; if the purchase date is before
`annual_cut_off_date`, it's this year's date, otherwise next year's. Example
`annual_fixed_date: "07-01"`, `annual_cut_off_date: "04-01"` — buy in March, expires 1 July
this year; buy in May, expires 1 July next year.

### `external.CancellationPolicy` and `CancellationRule`

| Field | Type | Notes |
| --- | --- | --- |
| `custom_description` | `Text` | **Use this as the cancellation policy text you show travelers.** |
| `rules[]` | `CancellationRule` | Ordered **most-restrictive-first**. |

`CancellationRule`:

| Field | Type | Notes |
| --- | --- | --- |
| `description` | `Text` | Auto-generated from the rule, may be empty. Reference only — prefer `custom_description`. |
| `applies_from` | `TimePoint` | When the rule takes effect. |
| `free` | boolean | No cancellation fee. |
| `charge_percent` | double | Percent of total, 0–100. |
| `charge_fixed` | double | Fixed amount in the display currency. |
| `not_cancellable` | boolean | Cancellation not accepted. |

`rules[0]` is the most restrictive, e.g. "not cancellable on the activity day", then "100%
within 24h", then "free before that". This ordering is for display; **the actual fee is
always determined server-side at cancel time** via `start-cancel-booking`.

---

## Availability (calendar)

The calendar response nests four levels. Note these type names are lowercase in the spec.

### `plan`

`{plan_id, plan_name, confirmation_type, days[]}` — `plan_id`, `plan_name`,
`confirmation_type` always present.

### `day`

`{date, plan_items[]}` — `date` is `YYYY-MM-DD`, always present.

### `plan.planItem`

`{plan_item_id, plan_item_name, units[], start_time}` — ids always present; `start_time` is
`HH:MM` local if the product has one.

### `unit`

| Field | Type | Notes |
| --- | --- | --- |
| `plan_unit_id` | string | Always present. |
| `unit_name` | string | Always present. Plain string here, not `Text`. |
| `allotment_quantity` | int32 | Remaining count — interpret via `allotment_type`. |
| `allotment_type` | `AllotmentType` | Whether the pool is shared across plan items and/or units. |
| `availability_status` | `AvailabilityStatus` | `OK` or `NG`. |
| `display_amount` | `price.Price` | |
| `payment_amount` | `price.Price` | |
| `unit_type` | `UnitType` | |

### `unitRequest` (request side)

`{plan_unit_id, request_quantity}` — both required.

### `CheckAvailabilityAndCalculateAmountResponse.planItem`

| Field | Type | Notes |
| --- | --- | --- |
| `plan_item_id` / `plan_item_name` | string | Always present. |
| `confirmation_type` | `ConfirmationType` | |
| `availability_status` | `AvailabilityStatus` | |
| `original_amount` | `price.Price` | Supplier's currency. |
| `display_amount` | `price.Price` | |
| `payment_amount` | `price.Price` | |

Note this endpoint names its price fields `*_amount`, while booking responses use
`*_currency_price`. Same concept, different names.

---

## Booking

### `ParticipantInfo` and its sub-objects

Documented in **`booking-form.md`**, not here — `ParticipantInfo`,
`BookingRepresentativeFields`, `OthersInformationFields`, `UserInformationFields`,
`PerBookingCustomReservationFields`, `PerParticipantCustomReservationFields`, `Choice` and
`LocalizedValue` only make sense alongside the `booking_form` that drives them, so they live
in that file. It covers both the request and response sides.

### `CustomIdCount`

`{id: string, count: int32}` — used for `plan_unit_items[]`. `id` is a `plan_unit_id`.

### `external.BookingInfo`

Returned by `get-booking` (inside `booking_info`) and by `list-bookings` (in `bookings[]`).

| Field | Type | Notes |
| --- | --- | --- |
| `booking_id` | string | e.g. `PRIVATE-20260212-WR2F2AIS`. |
| `supplier_booking_id` | string | The supplier's own reference. |
| `agent_booking_id` | string | Your reference, as sent on `start-booking`. |
| `agent_reservation_note` | string | |
| `status` | `BookingModel.Status` | |
| `activity_id` | string | |
| `activity_title_supplier_language` | string | |
| `activity_title_traveler_language` | string | |
| `activity_timezone` | string | IANA, e.g. `Asia/Tokyo`. |
| `plan_id` | string | |
| `plan_item_id` | string | |
| `plan_item_value` | string | Typically the start time, e.g. `12:00`, in the activity's timezone. |
| `plan_title_supplier_language` | string | |
| `plan_title_traveler_language` | string | |
| `target_date` | string | Activity date, in the activity's timezone. |
| `expiration_date` | string | Voucher expiration, in the activity's timezone. |
| `booking_at` | date-time | RFC 3339 instant the booking was made. |
| `booking_date` | string | The same moment as a date in the activity's timezone. |
| `issued_status` | `IssuedStatus` | Voucher redemption state. |
| `order_count` | string (int64) | Total units ordered. |
| `participant_first_name` / `participant_last_name` | string | |
| `participant_resident_region` | `CountryCode` | |
| `participant_email_address` | string | |
| `destination_email` | string | For booking-related notifications. |

Titles come in two language variants — supplier language and traveler language. Use the
traveler-language variant in customer-facing surfaces and the supplier-language one when
communicating with the supplier.

### `ListReservationsResponse.BookingSession`

| Field | Type | Notes |
| --- | --- | --- |
| `session_id` | string | |
| `expiry` | string (int64) | **Unix seconds**, as a string. Note `StartBookingResponse.expiry` is RFC 3339 instead — the same concept in two formats. 15-minute fallback if the adapter gives none. |
| `language_code` | `Language` | |
| `activity_id` / `plan_id` | string | |
| `activity_title` / `plan_title` | string | Plain strings here. |
| `target_date` | string | In the activity's timezone. |
| `participant_first_name` / `participant_last_name` | string | |
| `participant_email_address` | string | |
| `agent_booking_id` | string | Match sessions to your own orders with this. |

### `VoucherUrls`

`{mobile_html_url, mobile_pdf_url, printable_html_url, printable_pdf_url, redemption_url}`.
`redemption_url` is populated **only** when the activity has it configured; absence is
normal.

### `external.QRCode`, `PerBooking`, `PerParticipant`, `Payload`

| Type | Fields |
| --- | --- |
| `external.QRCode` | `per_booking: PerBooking`, `per_participant[]: PerParticipant` |
| `PerBooking` | `url`, `supplier_ticket_id`, `payload: Payload` |
| `PerParticipant` | `url`, `unit_id` (string/int64), `unit_title`, `supplier_ticket_id`, `payload: Payload` |
| `Payload` | `format: QRCodeCodeType`, `data: string` |

Whether a product issues one code per booking or one per participant depends on the
supplier — handle both. `Payload.data` meaning depends on `format`: for `QRCODE` and
`BARCODE*` it is the scannable content; for `TEXT` it is a display string such as a
redemption code; for `HYPERLINK` it is a URL; for `SUPPLIER_QRCODE_URL` it is a
supplier-provided **image URL** with no scannable content available.

### `UnitPrice` and `unit.Unit`

`UnitPrice` is `{unit: unit.Unit, supplier_currency_price, payment_currency_price, display_currency_price}`.

`unit.Unit` is the internal unit record:

| Field | Type | Notes |
| --- | --- | --- |
| `unit_id` | string (int64) | Internal db id. |
| `source_unit_id` | string | Third-party id (CMS, Ctrip, Klook…). |
| `activity_id` / `plan_id` | string (int64) | Internal ids. |
| `source_activity_id` / `source_plan_id` | string | Third-party ids. |
| `type` | `UnitType` | |
| `name` | `Text` | |
| `range` | `UnitRange` | |
| `use_as_min_display_price` | boolean | Whether this unit's price drives the "from" price. |
| `include_in_capacity` | boolean | |
| `can_be_book_independently` | boolean | |
| `order_count` | int32 | Quantity ordered. |
| `custom_id` | string | **The API-facing unit id** — this is what matches `plan_unit_id`. |

Do not use `unit_id` externally; `custom_id` is the value that corresponds to
`plan_unit_id` elsewhere in the API.

### `external.CancelRefundDisplay` and `CancelRefundDisplay.Price`

| Field | Type |
| --- | --- |
| `supplier_currency_price` | `CancelRefundDisplay.Price` |
| `payment_currency_price` | `CancelRefundDisplay.Price` |
| `display_currency_price` | `CancelRefundDisplay.Price` |
| `refund_rule_type` | `RefundRuleType` |
| `refund_failed_reason` | string |
| `cancel_at` | string (RFC 3339) |

`CancelRefundDisplay.Price` extends the normal price with refund figures:

| Field | Type | Example |
| --- | --- | --- |
| `currency_code` | `CurrencyCode` | `JPY` |
| `net` | double | 2484 |
| `gross` | double | 2700 |
| `net_refund` | double | 2044 |
| `gross_refund` | double | 2260 |
| `cancel_fee` | double | 440 |

Refund your traveler from `gross_refund`; reconcile your own settlement from `net_refund`.

### `Result`

`{booking_id, status, failed_reason}`. `status` ∈ `CANCEL_SUCCEED` / `CANCEL_PENDING` /
`CANCEL_FAILED`; `failed_reason` only on failure.

### `ParentBooking` (bundle products)

`{booking_custom_id, activity_id (int64), plan_id (int64), plan_item_id (int64), activity_title, plan_title}`.
Its purpose is to point a bundle child booking back at its parent.

Caveat worth knowing: **no object in the published spec declares a field of this type** —
verified by searching the whole document for `#/definitions/ParentBooking`, which appears zero
times. `external.BookingInfo` and `GetBookingResponse` have no `parent_booking` property. So
the type is defined but genuinely unreachable through the documented responses. If you need
parent/child linkage for bundles, the documented path is the other direction:
`FinalCancelBookingResponse.children_results[]` on the parent. Ask Linktivity if you need the
child→parent link.

---

## Errors

### `rpc.Status`

The body of every `4xx` and `5xx`.

| Field | Type | Notes |
| --- | --- | --- |
| `code` | int32 | A [google.rpc.Code](https://cloud.google.com/apis/design/errors) numeric value, **not** the HTTP status. |
| `message` | string | Developer-facing, English. Not for end users. |
| `details[]` | `protobuf.Any` | Structured detail. **Read this first when debugging.** |

### `protobuf.Any`

`{"@type": "...", ...}` — the `@type` URL identifies the payload type and the remaining keys
are that type's fields, inlined. The one you will meet most is
`type.googleapis.com/google.rpc.ErrorInfo`, which carries a `reason`, a `domain`, and a
`metadata` map naming the offending field. `StartBooking` language validation, for example,
returns `ErrorInfo` metadata with `LANGUAGE_CODE`, `ALLOWED_LANGS`, and `ACTIVITY_ID`.

Log `details[]` verbatim. Discarding it and keeping only `message` is why most integration
tickets start with "it just says invalid argument".
