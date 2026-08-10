# `booking_form` and `participant_info`

This is where most integration time is spent, so it gets its own file. The short version:
**`booking_form` on the plan tells you what to collect; `participant_info` on
`start-booking` is where you put it.** Every field in `booking_form` carries the JSON path
of where its value belongs, so you don't have to guess the mapping.

## The two halves

`get-activity-detail` → `activity.plans[].booking_form` is an `external.BookingForm`:

| Field | Type | Use |
| --- | --- | --- |
| `booking_field_specs[]` | `BookingFieldSpec` | **Preferred.** Standard fields, self-describing. |
| `custom_field_specs[]` | `CustomFieldSpec` | **Preferred.** Supplier-defined fields, self-describing. |
| everything else | enum-id arrays and `custom_fields[]` | **Deprecated legacy.** See "Legacy fields" below. |

Drive your form off `booking_field_specs` and `custom_field_specs`. The legacy lists are
retained only for existing integrations and will be removed in a future major version.

## `BookingFieldSpec` — standard fields

```json
{
  "field_id": "PARTICIPANT_EMAIL_ADDRESS",
  "scope": "REPRESENTATIVE",
  "type": "EMAIL",
  "request_path": "participant_info.booking_representative_fields.participant_email_address",
  "required": true,
  "format_hint": ""
}
```

| Field | Meaning |
| --- | --- |
| `field_id` | Well-known id, matching the `BookingField.Id` / `ExtendedBookingField.Id` / `ExtendedParticipantField.Id` enum names — e.g. `PARTICIPANT_EMAIL_ADDRESS`, `ARRIVAL_DATE`, `WEIGHT_KG`. |
| `scope` | Which sub-object of `participant_info` the value goes in. See `Scope` in `enums.md`. |
| `type` | Value type, a `BookingForm.Type` — `STRING`, `INTEGER`, `BOOLEAN`, `DATE`, `TIME`, `EMAIL`, `COUNTRY_CODE`, `LANGUAGE_CODE`, `ENUM`. |
| `request_path` | **The literal JSON path to write to.** Follow it exactly. |
| `required` | `true` = must be provided. `false` = may be omitted or empty. |
| `format_hint` | Human-readable format, e.g. `YYYY-MM-DD`, `HH:mm`, `ISO 3166-1 alpha-3`, `decimal number`. Empty when not applicable. |

`request_path` is authoritative. A `[]` in the path (e.g.
`participant_info.user_information_fields[].weight_kg`) means one value **per participant**,
so the field appears once in each `user_information_fields[]` element.

The three scopes map to three places:

| `scope` | Object | Cardinality |
| --- | --- | --- |
| `REPRESENTATIVE` | `participant_info.booking_representative_fields` | Once per booking |
| `OTHERS` | `participant_info.others_information_fields` | Once per booking |
| `PER_PARTICIPANT` | `participant_info.user_information_fields[]` | Once per participant |

## `CustomFieldSpec` — supplier-defined fields

```json
{
  "field_id": "a",
  "scope": "PER_BOOKING",
  "type": "DROPDOWN",
  "request_path": "participant_info.per_booking_custom_reservation_fields[id=a].responses",
  "required": true,
  "collecting_timing": "ON_BOOKING",
  "title":       { "text": "Do you need a guide?", "i18n_text": { "JAPANESE": "ガイドは必要ですか？" } },
  "description": { "text": "...", "i18n_text": {} },
  "choices": [
    { "text": "Yes", "i18n_text": { "JAPANESE": "はい" } },
    { "text": "No",  "i18n_text": { "JAPANESE": "いいえ" } }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `field_id` | Supplier-defined id, used as the array element key. Often short and opaque (`"a"`, `"b"`, `"1"`, `"2"`). |
| `scope` | `CustomScope`: `PER_BOOKING` or `PER_PARTICIPANT_CUSTOM`. |
| `type` | `CustomFieldType` — `DATE`, `TIME`, `YES_NO`, `DROPDOWN`, `RADIO`, `CHECK`, `TEXT`, `TEXTAREA`, `TEXT_NUMERIC`, etc. |
| `request_path` | Path including the id selector, e.g. `...[id=<field_id>].responses`. |
| `required` | The spec says "always true today; kept for forward compatibility" — so it does not discriminate. Use `collecting_timing` instead (below). |
| `collecting_timing` | `ON_BOOKING`, `BEFORE_ACTIVITY`, or `OPTIONAL`. |
| `title` / `description` | `Text` — show these to the traveler. |
| `choices[]` | `Text`, populated for choice-typed fields (`DROPDOWN`, `RADIO`, `CHECK`, `YES_NO`) and empty otherwise. |

**`required` and `collecting_timing` appear to disagree, and `collecting_timing` is the one
to act on.** `required` is hardcoded `true` on every spec today, so it tells you nothing;
`collecting_timing` is what varies. Treat `ON_BOOKING` as "must be present in the
`start-booking` payload"; `BEFORE_ACTIVITY` and `OPTIONAL` describe values collected later or
not at all. If a field with `collecting_timing: BEFORE_ACTIVITY` is rejected as missing at
`start-booking`, that is worth raising with Linktivity rather than working around — the two
fields genuinely conflict in the published schema.

**The critical detail about `choices`:** the value you submit in `responses` is the **label
string** — verbatim spec wording — not an index and not the `field_id`. Since each choice is
a `Text` (with a `text` and an `i18n_text` map), which string to send needs a rule:

> Request `get-activity-detail` with the **same `language_code`** you will send on
> `start-booking`, then submit `choices[n].i18n_text[<that language>]` if present, falling
> back to `choices[n].text`.

That is the only reading consistent with the documented examples, where a `JAPANESE` booking
submits `"responses": ["はい"]` against a choice whose Japanese label is `はい`. Do not mix
languages — submitting an English label on a Japanese booking is a rejection waiting to
happen. If you are matching choices in your own UI, key them by array position and translate
back to the label at submit time.

`CHECK` is multi-select, which is why `responses` is an array. Single-value types still use
an array, with one element.

## `participant_info` structure

```
participant_info
├── first_name                                  (representative, always required)
├── last_name                                   (representative, always required)
├── booking_representative_fields               (Scope: REPRESENTATIVE)
├── others_information_fields                   (Scope: OTHERS)
├── user_information_fields[]                   (Scope: PER_PARTICIPANT)
│   ├── plan_unit_id
│   ├── unit_index
│   ├── <standard per-participant fields>
│   └── per_participant_custom_reservation_fields[]   (CustomScope: PER_PARTICIPANT_CUSTOM)
│       ├── id
│       └── responses[]
└── per_booking_custom_reservation_fields[]      (CustomScope: PER_BOOKING)
    ├── id
    └── responses[]
```

`first_name` and `last_name` are the booking representative's name and are **always
required** whenever `participant_info` is sent, regardless of what `booking_form` says —
they are not in the `BookingField.Id` enum for that reason.

`participant_info` itself is marked optional on `StartBookingRequest`, which is only
meaningful for a plan whose `booking_form` asks for nothing at all. In practice, send it: if
you send the object, the representative's name must be in it, and any plan with a non-empty
`booking_form` requires it. Treat it as conditional, not optional.

### `booking_representative_fields`

Contact and trip context, collected once per booking.

| Field | Type | Notes |
| --- | --- | --- |
| `participant_email_address` | string | |
| `hotel_name` | string | |
| `hotel_address` | string | |
| `hotel_reservation_last_name` | string | The name the hotel booking is under — may differ from the traveler. |
| `hotel_reservation_first_name` | string | |
| `hotel_tel` | string | |
| `arrival_date` | string | Local arrival date. |
| `arrival_time` | string | |
| `arrival_flight_number` | string | |
| `departure_date` | string | |
| `departure_time` | string | |
| `departure_flight_number` | string | |
| `destination_email` | string | Local contact email while travelling. |
| `destination_tel` | string | Local contact phone while travelling. |
| `participant_resident_region` | `CountryCode` | Alpha-3, e.g. `CHN`. |
| `participant_language` | `Language` | e.g. `SIMPLIFIED_CHINESE`. |

Hotel and flight fields are typically required for pickup/transfer products
(`AIRPORT_TRANSPORTATION`, `CHARTER`) and absent for simple attraction tickets. Let
`booking_form` decide — don't collect all of them speculatively.

### `others_information_fields`

Trip logistics, collected once per booking. Mostly relevant to transport and tour products.

| Field | Type |
| --- | --- |
| `passengers_quantity` | int32 |
| `preferred_start_time` | string |
| `preferred_pick_up_location` | string |
| `preferred_drop_off_location` | string |
| `participants_quantity` | int32 |
| `luggage_quantity` | int32 (total suitcases) |
| `children_without_seat_quantity` | int32 (infants without a seat) |
| `child_seat_quantity_paid` | int32 (pay locally) |
| `child_seat_quantity_free` | int32 |
| `preferred_guide_language_code` | `Language` |
| `preferred_driver_language_code` | `Language` |

These are *preferences*, not guarantees — `preferred_start_time` does not override the
`plan_item_id` you booked.

### `user_information_fields[]` — one element per participant

| Field | Type | Notes |
| --- | --- | --- |
| `plan_unit_id` | string | Which unit this participant is. **From `get-activity-detail`.** |
| `unit_index` | int32 | Participant index: 1, 2, 3… |
| `unit_title` | `Text` | Response-side only. |
| `supplier_ticket_id` | string | Response-side only — assigned by the booking adapter, shown on the voucher. Do not send. |
| `per_participant_custom_reservation_fields[]` | `PerParticipantCustomReservationFields` | |
| `has_any_field` | boolean | "Whether any optional field is set" — a derived boolean about your own payload. Omit it; nothing depends on you sending it. |
| `passport_first_name` | string | Romanized as on the passport. |
| `passport_last_name` | string | Romanized as on the passport. |
| `passport_nationality` | `CountryCode` | Alpha-3. |
| `passport_number` | string | |
| `date_of_birth` | string | |
| `age` | int32 | |
| `gender` | string | **Must be exactly `"male"`, `"female"`, or `"other"`** — lowercase, free-string typed but validated by value. |
| `eyesight` | string | e.g. `"3.0"`. |
| `weight_kg` | string | **String, not number** — e.g. `"55"`. |
| `height_cm` | string | String — e.g. `"180"`. |
| `shoe_size_cm` | string | String — e.g. `"25"`. |
| `clothes_size` | string | e.g. `"XL"`. |
| `vegetarian_meals` | boolean | |
| `diving_experience_times` | int32 | |
| `rental_equipments_free` | boolean | |
| `rental_equipments_pay_locally` | boolean | |

Two traps here. **`weight_kg`, `height_cm`, `shoe_size_cm` and `eyesight` are strings**,
while `age` and `diving_experience_times` are integers — sending `"weight_kg": 55` as a
number will be rejected by strict clients. And **`gender` is a free-form string with a
constrained value set**; `"Male"` or `"M"` will not do.

### `unit_index` and how the array lines up with `plan_unit_items`

The number of `user_information_fields[]` elements must equal the total participant count
across `plan_unit_items[]`, and the `plan_unit_id` distribution must match.

Booking 2 adults and 1 child:

```json
"plan_unit_items": [
  { "id": "EggKAggSEgIIQQ==", "count": 2 },
  { "id": "CAMSBgoAEgIIEg==", "count": 1 }
]
```

means `user_information_fields[]` has three elements — two with
`plan_unit_id: "EggKAggSEgIIQQ=="` and one with `plan_unit_id: "CAMSBgoAEgIIEg=="` — and
`unit_index` runs 1, 2, 3 across the whole array:

```json
"user_information_fields": [
  { "plan_unit_id": "EggKAggSEgIIQQ==", "unit_index": 1, "passport_last_name": "Wang", "passport_first_name": "Yi" },
  { "plan_unit_id": "EggKAggSEgIIQQ==", "unit_index": 2, "passport_last_name": "Wang", "passport_first_name": "Er" },
  { "plan_unit_id": "CAMSBgoAEgIIEg==", "unit_index": 3, "passport_last_name": "Wang", "passport_first_name": "San" }
]
```

`unit_index` is a global 1-based sequence across the array, not a per-unit counter: the
documented examples run 1, 2, 3 continuing across a unit boundary. Note this is read off the
examples rather than stated as a rule in the spec, and the field name reads like it could be
per-unit — so if a multi-unit booking is rejected with a participant-mismatch error and
everything else checks out, trying a per-unit numbering is a reasonable second attempt, and
worth confirming with Linktivity.

One qualification on "one element per participant": that holds for person-typed units. Some
`UnitType` values are not people — `ROOM`, `GROUP`, `BOAT`, `CHARTER_SERVICE`, `PRINT`,
`HOURS_VEHICLES` and the `*_VAR` variants sell a thing or a duration, so a `count` of 1 may
carry several travelers. The spec does not say how `user_information_fields[]` should be
populated for those, and `min/max_capacity_inclusive` are described in terms of "booking
units", not people. For non-person units, take the field requirements from `booking_form` and
confirm the participant-row expectation with Linktivity rather than assuming one row per
`count`.

Note that `plan_unit_id` values are often base64-looking opaque strings (e.g.
`EggKAggSEgIIQQ==`) because they encode internal identifiers. Treat them as opaque: copy
them verbatim from `get-activity-detail`, don't decode or normalise them, and be careful
that URL-encoding doesn't mangle the `=` padding if you ever put one in a query string.

### Where `plan_unit_items[].id` actually comes from

The authoritative source is `get-activity-detail` →
`activity.plans[].units[].plan_unit_id`. Equivalently, in `StartBookingResponse.unit_prices[]`,
it is `unit.custom_id` — the field the spec describes as the "custom id for api usage".
`unit.Unit.unit_id` is an internal database id and is **not** the value to send.

Be aware of a discrepancy in the published examples. The `StartBookingRequest` example shows
`plan_unit_items` ids in the form `LINKTIVITY-1QCOC-1-1` / `LINKTIVITY-1QCOC-1-2`, where the
first value is identical to that example's `plan_item_id` — which looks like a copy-paste
slip. Every other example in the spec, including `user_information_fields[].plan_unit_id` and
`unit.custom_id`, uses the opaque base64 form (`EggKAggSEgIIQQ==`, `CAMSBgoAEgIIEg==`).

The safe rule: **read the value out of `get-activity-detail` and send it back unchanged**,
whatever shape it has. Do not construct a `plan_unit_id` by pattern-matching on
`plan_item_id`, and do not assume a format — it varies by supplier. If a booking is rejected
with an unknown-unit error, this is the first thing to check.

### Custom reservation field elements

`PerBookingCustomReservationFields` and `PerParticipantCustomReservationFields` have the
same shape:

| Field | Send it? | Notes |
| --- | --- | --- |
| `id` | **Required** | The `field_id` from `CustomFieldSpec`. |
| `responses[]` | **Required** | String array. For choice types, the choice **label**. |
| `title_supplier_lang` | No | Ignored in the request. |
| `title_activity_lang` | No | Ignored in the request. |
| `type` | No | Ignored in the request. |
| `choices[]` | No | Ignored in the request. |

The spec is explicit that `title_supplier_lang`, `title_activity_lang`, `type` and
`choices` are **ignored on the request — omit them**. The published `StartBookingRequest`
examples do include a `title` and `type` on these elements, which is harmless but pointless.
Send only `id` and `responses`.

Minimal correct form:

```json
"per_booking_custom_reservation_fields": [
  { "id": "a", "responses": ["はい"] },
  { "id": "b", "responses": ["a for apple(ja)"] }
]
```

For a `CHECK` (multi-select) field, list every selected label:

```json
{ "id": "c", "responses": ["Vegetarian", "No nuts"] }
```

Custom fields have no `format_hint` (that is a `BookingFieldSpec` field only), so the `type`
is your only format signal. For date-ish types (`DATE`, `DATE_ONLY_PAST`,
`DATE_ONLY_FUTURE`) use `YYYY-MM-DD`, and for `TIME` use `HH:mm`, matching the conventions
`BookingForm.Type` documents for standard fields:

```json
{ "id": "c", "responses": ["2026-02-26"] }
```

`Choice` and `LocalizedValue` appear on the response side of these elements.
`Choice` is `{text, localized_values[]}` and `LocalizedValue` is `{language_code, text}`
where `language_code` is a lowercase tag like `"ja-jp"` or `"zh-hant"` — **not** the
`Language` enum names used by `Text.i18n_text`. Two localisation conventions coexist in this
API; don't mix them up.

## Worked example

Given a plan whose `booking_form` returns:

```json
{
  "booking_field_specs": [
    { "field_id": "PARTICIPANT_EMAIL_ADDRESS", "scope": "REPRESENTATIVE", "type": "EMAIL",
      "request_path": "participant_info.booking_representative_fields.participant_email_address",
      "required": true, "format_hint": "" },
    { "field_id": "ARRIVAL_DATE", "scope": "REPRESENTATIVE", "type": "DATE",
      "request_path": "participant_info.booking_representative_fields.arrival_date",
      "required": true, "format_hint": "YYYY-MM-DD" },
    { "field_id": "LUGGAGE_QUANTITY", "scope": "OTHERS", "type": "INTEGER",
      "request_path": "participant_info.others_information_fields.luggage_quantity",
      "required": false, "format_hint": "" },
    { "field_id": "PASSPORT_NUMBER", "scope": "PER_PARTICIPANT", "type": "STRING",
      "request_path": "participant_info.user_information_fields[].passport_number",
      "required": true, "format_hint": "" }
  ],
  "custom_field_specs": [
    { "field_id": "a", "scope": "PER_BOOKING", "type": "DROPDOWN",
      "request_path": "participant_info.per_booking_custom_reservation_fields[id=a].responses",
      "required": true, "collecting_timing": "ON_BOOKING",
      "title": { "text": "Need a guide?", "i18n_text": { "ENGLISH": "Need a guide?" } },
      "choices": [
        { "text": "Yes", "i18n_text": { "ENGLISH": "Yes" } },
        { "text": "No",  "i18n_text": { "ENGLISH": "No" } }
      ] }
  ]
}
```

…and booking 2 adults with `language_code: ENGLISH`, the correct `participant_info` is:

```json
{
  "first_name": "San",
  "last_name": "Zhang",
  "booking_representative_fields": {
    "participant_email_address": "traveler@example.com",
    "arrival_date": "2026-08-11"
  },
  "others_information_fields": {
    "luggage_quantity": 2
  },
  "user_information_fields": [
    { "plan_unit_id": "EggKAggSEgIIQQ==", "unit_index": 1, "passport_number": "AB1234567" },
    { "plan_unit_id": "EggKAggSEgIIQQ==", "unit_index": 2, "passport_number": "CD7654321" }
  ],
  "per_booking_custom_reservation_fields": [
    { "id": "a", "responses": ["Yes"] }
  ]
}
```

Note what is *absent*: no fields the form didn't ask for, no `title`/`type` echoed back on
the custom field, no `supplier_ticket_id`, no `unit_title`.

## Legacy fields

`external.BookingForm` also carries these, all deprecated, all kept only for backward
compatibility with existing OTA integrations:

`required_booking_fields[]`, `optional_booking_fields[]`, `voucher_hidden_fields[]`,
`booking_details_hidden_fields[]` (all `BookingField.Id`);
`required_extended_booking_fields[]`, `optional_extended_booking_fields[]`,
`voucher_hidden_extended_fields[]`, `booking_details_hidden_extended_fields[]` (all
`ExtendedBookingField.Id`);
`required_participant_fields[]`, `optional_participant_fields[]`,
`voucher_hidden_participant_fields[]`, `booking_details_hidden_participant_fields[]` (all
`ExtendedParticipantField.Id`);
and `custom_fields[]` of `CustomField`.

The `voucher_hidden_*` and `booking_details_hidden_*` lists indicate fields that should be
collected but **not displayed** on the voucher or the booking detail view respectively.
There is no equivalent flag on the new `*_specs` objects, so if you rely on hiding
behaviour you currently still need to read the legacy lists.

Legacy `CustomField` is `{field_id, type, title, description, collecting_type, collecting_timing, choices[], hide_from_voucher}`
— note `collecting_type` is `CustomField.CollectingType` (`PER_BOOKING` / `PER_PARTICIPANT`)
rather than `CustomScope`, and `hide_from_voucher` is the per-field hiding flag.

New integrations: read `booking_field_specs` and `custom_field_specs`, plus the
`voucher_hidden_*` legacy lists if you need voucher-hiding behaviour. Ignore the rest.

## `update-booking-participant-info` overwrites

The same `ParticipantInfo` object is used to correct details after confirmation, and it
**completely replaces** what's stored. There is no merge and no patch semantics. Always:

1. `get-booking` to read the current `participant_info`.
2. Apply your change to that object in full.
3. Send the whole thing back.

Sending only the field you changed will erase everything else. After a successful update,
new `voucher_urls` come back in the response — the old voucher documents are stale, so
re-issue them to the traveler.
