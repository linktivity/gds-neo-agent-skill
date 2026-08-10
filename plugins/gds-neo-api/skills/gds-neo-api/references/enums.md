# Enum reference

All enum values are sent and received as **strings matching the enum name**, not integers.
`UNDEFINED` (or `UNKNOWN`, or `*_UNSPECIFIED`) is a reserved zero value meaning
"unspecified" — as a query filter it means "no filter"; as a value you deliberately send it
is almost always a bug.

---

## `ConfirmationType` — how a product is sold

Default `UNDEFINED`. Determines booking behaviour; see `flow.md`.

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Undefined category. |
| `FREE_SALE` | Specific participation date, unlimited sales. |
| `FREE_SALE_OPEN_DATE` | No specific participation date required, unlimited sales. **`target_date` is not required on `start-booking`.** |
| `INVENTORY` | Specific participation date, with limited inventory. |
| `REQUEST` | Specific participation date, manual review required for sales. |

## `BookingType`

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Reserved. |
| `SINGLE` | Individual booking. |
| `BULK` | Bulk booking. |

## `BookingModel.Status` — booking status

Also the value set for the `booking_status` filter on `list-bookings`.

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Undefined. |
| `REQUEST_PENDING` | Awaiting supplier review (`REQUEST` products). |
| `REQUEST_REJECTED` | Supplier rejected the request. |
| `CONFIRMED` | Confirmed — covers approved requests and instant products. |
| `CANCELLED_BY_TRAVELER` | Cancelled from the traveler/OTA side. |
| `CANCELLED_BY_SUPPLIER` | Cancelled by the supplier. |
| `INVALID` | Invalid. |
| `CANCEL_FAILED` | Cancellation failed. |
| `CANCEL_PENDING` | Cancellation in progress at the supplier. |

## `IssuedStatus` — voucher redemption

| Value | Meaning |
| --- | --- |
| `DISABLE` | Initial or not-applicable state; voucher issuing disabled or irrelevant. |
| `NOT_ISSUED` | Booking succeeded, vouchers not yet issued. Initial state after booking. |
| `PARTIAL` | Some vouchers in the booking issued or used. Intermediate state. |
| `ISSUED` | All vouchers issued or used — may also mean expired and no longer usable. Final state. |

## `AvailabilityStatus`

`UNDEFINED`, `OK`, `NG`. `NG` means not available.

## `AllotmentType` — how to read `allotment_quantity`

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Reserved. |
| `PLAN_ITEM_SHARED` | Shared across plan items — 10:00 and 14:00 draw from the same inventory. |
| `UNIT_SHARED` | Shared across units — adult and child draw from the same inventory. |
| `PLAN_ITEM_AND_UNIT_SHARED` | Shared across both dimensions. |
| `INDEPENDENT` | This unit on this plan item has its own inventory. |

## `CancelCheckCode` — from `start-cancel-booking`

| Value | Meaning |
| --- | --- |
| `CAN_BE_CANCELLED` | Proceed to `final-cancel-booking`. |
| `ALREADY_CANCELLED` | Already cancelled. |
| `CAN_NOT_CANCEL` | Cannot cancel under policy. |
| `BOOKING_EXPIRED` | Voucher has expired. |
| `SHOULD_DECLINE_INSTEAD_OF_CANCEL` | A pending `REQUEST` booking — decline rather than cancel. |

## `CancelBookingStatus` — in `Result.status`

`CANCEL_SUCCEED` (default), `CANCEL_PENDING` (waiting for supplier response),
`CANCEL_FAILED`.

## `cancellation.CancelReason` — optional on `final-cancel-booking`

`UNKNOWN` (default), `PARTICIPANT_OR_DATE_CHANGE`, `SAME_SUPPLIER_ACTIVITY_CHANGE`,
`SEPARATE_SUPPLIER_ACTIVITY_CHANGE`, `BOOKED_BY_MISTAKE`, `DOUBLE_BOOKING`,
`FLIGHT_ISSUES`, `SICKNESS`, `FOUND_CHEAPER_RATE`, `OTHER`, `BAD_WEATHER`,
`TECHNICAL_DIFFICULTIES`, `PARTICIPANT_MINIMUM_NOT_MET`, `PRIVATE_BUYOUT`,
`OTA_CANCEL_WITHOUT_REASON`.

## `RefundRuleType`

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Reserved. |
| `FIXED` | Fixed-amount refund. |
| `PERCENTAGE` | Fixed-percentage refund. |
| `NOT_CANCELLATION` | Non-refundable. |
| `NOT_YET_CHARGED` | Not paid yet, so no refund is processed. |
| `FULL_REFUND` | Full refund. |
| `REFUND_FAILED` | Refund failed — reason in `refund_failed_reason`. |

## `AsyncFinalBookingStatus`

Schema-only; no path exposes it in the published spec. `ASYNC_FINAL_BOOKING_STATUS_`
prefixed: `UNSPECIFIED`, `ACCEPTED` (queued), `PROCESSING`, `COMPLETED` (`result`
populated), `FAILED` (see `error_message`).

---

## `Language`

Keys of `Text.i18n_text` use these exact names.

`UNDEFINED`, `ARABIC`, `GERMAN`, `ENGLISH`, `SPANISH`, `FRENCH`, `INDONESIAN`, `ITALIAN`,
`JAPANESE`, `KOREAN`, `PORTUGUESE`, `RUSSIAN`, `THAI`, `VIETNAMESE`, `SIMPLIFIED_CHINESE`,
`TRADITIONAL_CHINESE`.

Based on `golang.org/x/text/language`. There is no generic `CHINESE` — pick
`SIMPLIFIED_CHINESE` or `TRADITIONAL_CHINESE`.

## `TravelProductCategory`

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Undefined category |
| `RAILWAY_TICKET` | Railway ticket (e.g. JR, Subway) |
| `AIRPORT_TRANSPORTATION` | Airport transportation (pickup/drop-off) |
| `SHINKANSEN` | Shinkansen tickets |
| `EXPRESS_BUS` | Highway bus tickets |
| `BUS_TOUR` | Bus tour (1-day or multi-day) |
| `CRUISES` | Cruises |
| `RENTAL_CAR` | Rental car |
| `CHARTER` | Chartered vehicle (with driver) |
| `ATTRACTION` | Attraction ticket |
| `THEME_PARK` | Theme park (e.g. Disneyland, Universal Studios) |
| `MUSEUM_GALLERY` | Museum or art gallery |
| `AQUARIUM_ZOO` | Aquarium or zoo |
| `TEMPLES_SHINES` | Temple or shrine visit (note: spelling is `SHINES` in the API) |
| `TOWER_BUILDING` | Tower or landmark (e.g. Skytree, Tokyo Tower) |
| `JAPANESE_RESTAURANT` | Japanese restaurant |
| `WESTERN_RESTAURANT` | Western restaurant |
| `CHINESE_RESTAURANT` | Chinese restaurant |
| `OTHER_RESTAURANT` | Other restaurant |
| `DESSERT_BEVERAGE` | Dessert or beverage (cafe, ice cream) |
| `SIGHTSEEING_TOUR` | Sightseeing tour (walking, private guide) |
| `MARINE_SPORTS` | Marine sports (snorkeling, diving, speedboat) |
| `OUTDOOR_ACTIVITIES` | Outdoor activities (hiking, skiing, rafting) |
| `ONSEN` | Onsen (hot spring) experience |
| `SPA_MASSAGE` | Spa or massage service |
| `JAPANESE_CULTURAL_EXPERIENCE` | Cultural experience (kimono, tea ceremony) |
| `JAPANESE_CRAFT_EXPERIENCE` | Traditional craft experience (dyeing, pottery) |
| `JAPANESE_COOKING_EXPERIENCE` | Japanese cooking experience (sushi, ramen) |
| `OTHER_EXPERIENCE` | Other experience |
| `HOTEL` | Hotel |
| `RYOKAN` | Ryokan (Japanese-style inn) |
| `VACATION_RENTAL` | Vacation rental |
| `BUNDLE` | Bundled product (e.g. ticket + meal) |
| `PASS` | Pass |
| `OTHERS` | Others |

## `UnitType`

Participant type / unit-of-sale. Long list; grouped here for readability.

**Age and person categories:** `AGE_ADULT_AND_CHILD` (unified pricing), `AGE_ADULT`,
`AGE_YOUTH`, `AGE_CHILD` (typically 6–12), `AGE_SENIOR` (e.g. 65+), `AGE_INFANT` (0–2),
`AGE_STUDENT`, `AGE_HIGH_SCHOOL`, `AGE_INTERMEDIATE_SCHOOL`, `AGE_ELEMENTARY_SCHOOL`,
`AGE_COLLEGE`, `AGE_GRADUATE`, `AGE_OBSERVER`, `AGE_ADULT_OBSERVER`, `AGE_CHILD_OBSERVER`,
`AGE_RIDE_ALONG`, `AGE_ADULT_RIDE_ALONG`, `AGE_CHILD_RIDE_ALONG`, `AGE_DRIVER`,
`AGE_DISABLED_ADULT`, `AGE_DISABLED_YOUTH`, `AGE_DISABLED_CHILD`, `AGE_SUPPORTER_ADULT`,
`AGE_SUPPORTER_CHILD`, `AGE_ADULT_AND_CHILD_2` (shown as "General"), `AGE_CHILD_2`
(distinct child fare category).

**Physical criteria:** `TALL_CHILD`, `WEIGHT_ADULT` (kg), `WEIGHT_LBS_ADULT` (lb).

**Time-based, vehicles:** `MINUTES_VEHICLES`, `HOURS_VEHICLES`, `DAYS_VEHICLES`,
`WEEKS_VEHICLES`, `NIGHTS_VEHICLES`.

**Time-based, persons:** `MINUTES_PERSONS`, `HOURS_PERSONS`, `DAYS_PERSONS`,
`WEEKS_PERSONS`, `NIGHTS_PERSONS`.

**Bare time units:** `MINUTE`, `HOUR`, `DAY`, `WEEK`, `NIGHT`.

**Capacity units:** `ROOM`, `QUANTITY`, `CHARTER_SERVICE`, `BOAT`, `GROUP`, `PRINT`,
`CHARTER_VAR`, `GROUP_VAR`, `ROOM_VAR`, `BOAT_VAR` (the `*_VAR` variants are variable
configurations adjusted per situation).

**Pets:** `PET`, `PET_CAT`, `PET_DOG`, `PET_DOG_S`, `PET_DOG_M`, `PET_DOG_L`, `PET_DOG_XL`,
`PET_OTHER`.

**Add-ons:** `DRINK_STANDARD_SET`, `DRINK_CHAMPAGNE_SET`.

Plus `UNDEFINED`. Don't hardcode a mapping from `UnitType` to a display label — use the
unit's `title` / `name` `Text`, which is localised. `UnitType` is for categorisation and
business rules only.

## `PeriodUnit`

`UNDEFINED`, `DAY`, `MONTH`, `YEAR`.

## `Anchor` — for `TimePoint`

`BOOKING_CONFIRMED` (default) — relative to when the booking was confirmed.
`ACTIVITY_START` — relative to the activity start time.

## `VoucherExpirationPeriodType`

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Reserved. |
| `UNLIMITED` | Never expires. |
| `FROM_PURCHASE_DATE` | Expires a period after purchase. Read `after_purchase_date`. |
| `FROM_ACTIVITY_DATE` | Expires a period after the activity date. Read `after_activity_date`. |
| `FIXED_DATE` | Expires on a fixed date. Read `fixed_date`. |
| `RELATIVE_FIXED_DATE` | Expires on a fixed MM-DD each year, with a year-increment cutoff. Read `annual_fixed_date`. |

## `FileType`

`UNDEFINED`, `PDF`, `IMAGE`, `VIDEO`, `HTML`.

## `QRCodeCodeType` (also `Payload.format`)

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Reserved. |
| `QRCODE` | 2D QR code; `data` is the scannable content. |
| `TEXT` | Plain text (redemption code, serial number) displayed directly, no barcode. |
| `HYPERLINK` | URL, render as a link (e.g. a redemption page). |
| `BARCODE128` | Code 128 — digits and letters; logistics and ticketing. |
| `BARCODE93` | Code 93 — more compact than Code 39. |
| `BARCODE39` | Code 39 — uppercase letters and digits only. |
| `BARCODE25` | Interleaved 2 of 5 — digits only. |
| `SUPPLIER_QRCODE_URL` | Supplier-provided QR **image URL** re-hosted by Linktivity. No scannable content available. |

## `CheckListItem.Type`

| Value | Meaning |
| --- | --- |
| `RESTRICTION` | A hard restriction on participation. |
| `REQUIRED_ITEM_TO_BRING_AND_ATTIRE` | Must bring / must wear. |
| `REQUIRED_OTHER` | Other requirement. |
| `REQUIRED_ADDITIONAL_NOTE` | Required note. |
| `NICE_TO_HAVE_ITEM_TO_BRING_AND_ATTIRE` | Optional item or attire. |
| `NICE_TO_HAVE_OTHER` | Other optional note. |
| `INCLUDED` | What the price includes. |

Surface `RESTRICTION` and the `REQUIRED_*` items before purchase — they are the ones that
cause denied entry at the venue.

## `CustomFieldType`

Value type for supplier-defined booking form fields.

| Value | Meaning |
| --- | --- |
| `UNDEFINED` | Reserved. |
| `DATE` | Date, past or future. |
| `DATE_ONLY_PAST` | Past date only. |
| `DATE_ONLY_FUTURE` | Future date only. |
| `TIME` | Time. |
| `YES_NO` | Yes/no switch. |
| `DROPDOWN` | Dropdown select. |
| `RADIO` | Radio button. |
| `CHECK` | Checkbox (multi-select). |
| `TEXT` | Single-line text. |
| `TEXT_ALPHANUMERIC` | Single-line, alphanumeric only. |
| `TEXT_PHONE` | Single-line phone number. |
| `TEXTAREA` | Multi-line text. |
| `TEXT_NUMERIC` | Single-line, numeric only. |

## `BookingForm.Type`

Value type for **standard** booking fields (as opposed to custom ones).

| Value | Meaning |
| --- | --- |
| `TYPE_UNSPECIFIED` | Reserved. |
| `STRING` | Free-text string. |
| `INTEGER` | Integer. |
| `BOOLEAN` | Boolean. |
| `DATE` | `YYYY-MM-DD`. |
| `TIME` | Local time `HH:mm`. |
| `EMAIL` | Email address. |
| `COUNTRY_CODE` | ISO 3166-1 alpha-3, i.e. a `CountryCode` value. |
| `LANGUAGE_CODE` | A `Language` enum value. |
| `ENUM` | Generic enum. |

## `Scope` — where a standard field lives in the payload

| Value | Path in `participant_info` |
| --- | --- |
| `SCOPE_UNSPECIFIED` | Reserved. |
| `REPRESENTATIVE` | `booking_representative_fields.<field>` |
| `OTHERS` | `others_information_fields.<field>` |
| `PER_PARTICIPANT` | `user_information_fields[].<field>` |

## `CustomScope` — where a custom field lives

| Value | Path in `participant_info` |
| --- | --- |
| `CUSTOM_SCOPE_UNSPECIFIED` | Reserved. |
| `PER_BOOKING` | `per_booking_custom_reservation_fields[]` |
| `PER_PARTICIPANT_CUSTOM` | `user_information_fields[].per_participant_custom_reservation_fields[]` |

## `CollectingTiming`

`ON_BOOKING` (default), `BEFORE_ACTIVITY`, `OPTIONAL`. When the response must be collected.

## `CustomField.CollectingType`

`PER_BOOKING` (default), `PER_PARTICIPANT`. The legacy equivalent of `CustomScope`.

## `BookingField.Id` — legacy standard field ids

Deprecated in favour of `booking_field_specs`. Retained for backward compatibility.

`UNKNOWN`, `PARTICIPANT_EMAIL_ADDRESS`, `HOTEL_NAME`, `HOTEL_ADDRESS`,
`HOTEL_RESERVATION_LAST_NAME`, `HOTEL_RESERVATION_FIRST_NAME`, `HOTEL_TEL`, `ARRIVAL_DATE`,
`ARRIVAL_TIME`, `ARRIVAL_FLIGHT_NUMBER`, `DEPARTURE_DATE`, `DEPARTURE_TIME`,
`DEPARTURE_FLIGHT_NUMBER`, `DESTINATION_EMAIL`, `DESTINATION_TEL`,
`PARTICIPANT_RESIDENT_REGION`, `PARTICIPANT_LANGUAGE`.

Participant last name and first name are **always required** and are not part of this enum —
they are `participant_info.last_name` and `participant_info.first_name`.

## `ExtendedBookingField.Id` — legacy per-booking extended field ids

`UNKNOWN`, `PASSENGERS_QUANTITY`, `PREFERRED_START_TIME`, `PREFERRED_PICK_UP_LOCATION`,
`PREFERRED_DROP_OFF_LOCATION`, `PARTICIPANTS_QUANTITY`, `LUGGAGE_QUANTITY`,
`CHILDREN_WITHOUT_SEAT_QUANTITY`, `CHILD_SEAT_QUANTITY_PAID`, `CHILD_SEAT_QUANTITY_FREE`,
`PREFERRED_GUIDE_LANGUAGE_CODE`, `PREFERRED_DRIVER_LANGUAGE_CODE`.

These map onto `others_information_fields`.

## `ExtendedParticipantField.Id` — legacy per-participant extended field ids

`UNKNOWN`, `PASSPORT_FIRST_NAME`, `PASSPORT_LAST_NAME`, `PASSPORT_NATIONALITY`,
`PASSPORT_NUMBER`, `DATE_OF_BIRTH`, `AGE`, `GENDER`, `EYESIGHT`, `WEIGHT_KG`, `HEIGHT_CM`,
`SHOE_SIZE_CM`, `CLOTHES_SIZE`, `VEGETARIAN_MEALS`, `DIVING_EXPERIENCE_TIMES`,
`RENTAL_EQUIPMENTS_FREE`, `RENTAL_EQUIPMENTS_PAY_LOCALLY`.

These map onto `user_information_fields[]`.

---

## `CurrencyCode`

ISO 4217, plus some non-standard internal codes. Send the three-letter name.

`UNDEFINED`, `AED`, `AFN`, `ALL`, `AMD`, `ANG`, `AOA`, `ARS`, `AUD`, `AWG`, `AZN`, `BAM`,
`BBD`, `BDT`, `BGN`, `BHD`, `BIF`, `BMD`, `BND`, `BOB`, `BOV`, `BRL`, `BSD`, `BTN`, `BWP`,
`BYN`, `BYR`, `BZD`, `CAD`, `CDF`, `CHE`, `CHF`, `CHW`, `CLF`, `CLP`, `CNY`, `COP`, `COU`,
`CRC`, `CUC`, `CUP`, `CVE`, `CZK`, `DJF`, `DKK`, `DOP`, `DZD`, `EGP`, `ERN`, `ETB`, `EUR`,
`FJD`, `FKP`, `GBP`, `GEL`, `GHS`, `GIP`, `GMD`, `GNF`, `GTQ`, `GYD`, `HKD`, `HNL`, `HRK`,
`HTG`, `HUF`, `IDR`, `ILS`, `INR`, `IQD`, `IRR`, `ISK`, `JMD`, `JOD`, `JPY`, `KES`, `KGS`,
`KHR`, `KMF`, `KPW`, `KRW`, `KWD`, `KYD`, `KZT`, `LAK`, `LBP`, `LKR`, `LRD`, `LSL`, `LYD`,
`MAD`, `MDL`, `MGA`, `MKD`, `MMK`, `MNT`, `MOP`, `MRO`, `MUR`, `MVR`, `MWK`, `MXN`, `MXV`,
`MYR`, `MZN`, `NAD`, `NGN`, `NIO`, `NOK`, `NPR`, `NZD`, `OMR`, `PAB`, `PEN`, `PGK`, `PHP`,
`PKR`, `PLN`, `PYG`, `QAR`, `RON`, `RSD`, `RUB`, `RWF`, `SAR`, `SBD`, `SCR`, `SDG`, `SEK`,
`SGD`, `SHP`, `SLL`, `SOS`, `SRD`, `SSP`, `STD`, `SVC`, `SYP`, `SZL`, `THB`, `TJS`, `TMT`,
`TND`, `TOP`, `TRY`, `TTD`, `TWD`, `TZS`, `UAH`, `UGX`, `USD`, `USN`, `UYI`, `UYU`, `UZS`,
`VEF`, `VND`, `VUV`, `WST`, `XAF`, `XAG`, `XAU`, `XBA`, `XBB`, `XBC`, `XBD`, `XCD`, `XDR`,
`XOF`, `XPD`, `XPF`, `XPT`, `XSU`, `XTS`, `XUA`, `XXX`, `YER`, `ZAR`, `ZMW`, `ZWL`, `LTL`,
`JEP`, `ZWD`, `SPL`, `TVD`, `IMP`, `GGP`, `LVL`, `TMM`, `EEK`, `ZMK`, `VEB`, `XBT`.

The tail of the list (from `LTL` onward) includes retired and non-standard codes such as
`XBT` (Bitcoin) and `TVD`. In practice you will use `JPY`, plus your settlement and display
currencies.

## `CountryCode`

ISO 3166-1 **alpha-3** (three letters — `JPN`, not `JP`), plus a non-standard `UNIVERSAL`
for internal use.

`UNDEFINED`, `ABW`, `AFG`, `AGO`, `AIA`, `ALA`, `ALB`, `AND`, `ARE`, `ARG`, `ARM`, `ASM`,
`ATA`, `ATF`, `ATG`, `AUS`, `AUT`, `AZE`, `BDI`, `BEL`, `BEN`, `BES`, `BFA`, `BGD`, `BGR`,
`BHR`, `BHS`, `BIH`, `BLM`, `BLR`, `BLZ`, `BMU`, `BOL`, `BRA`, `BRB`, `BRN`, `BTN`, `BVT`,
`BWA`, `CAF`, `CAN`, `CCK`, `CHE`, `CHL`, `CHN`, `CIV`, `CMR`, `COD`, `COG`, `COK`, `COL`,
`COM`, `CPV`, `CRI`, `CUB`, `CUW`, `CXR`, `CYM`, `CYP`, `CZE`, `DEU`, `DJI`, `DMA`, `DNK`,
`DOM`, `DZA`, `ECU`, `EGY`, `ERI`, `ESH`, `ESP`, `EST`, `ETH`, `FIN`, `FJI`, `FLK`, `FRA`,
`FRO`, `FSM`, `GAB`, `GBR`, `GEO`, `GGY`, `GHA`, `GIB`, `GIN`, `GLP`, `GMB`, `GNB`, `GNQ`,
`GRC`, `GRD`, `GRL`, `GTM`, `GUF`, `GUM`, `GUY`, `HKG`, `HMD`, `HND`, `HRV`, `HTI`, `HUN`,
`IDN`, `IMN`, `IND`, `IOT`, `IRL`, `IRN`, `IRQ`, `ISL`, `ISR`, `ITA`, `JAM`, `JEY`, `JOR`,
`JPN`, `KAZ`, `KEN`, `KGZ`, `KHM`, `KIR`, `KNA`, `KOR`, `KWT`, `LAO`, `LBN`, `LBR`, `LBY`,
`LCA`, `LIE`, `LKA`, `LSO`, `LTU`, `LUX`, `LVA`, `MAC`, `MAF`, `MAR`, `MCO`, `MDA`, `MDG`,
`MDV`, `MEX`, `MHL`, `MKD`, `MLI`, `MLT`, `MMR`, `MNE`, `MNG`, `MNP`, `MOZ`, `MRT`, `MSR`,
`MTQ`, `MUS`, `MWI`, `MYS`, `MYT`, `NAM`, `NCL`, `NER`, `NFK`, `NGA`, `NIC`, `NIU`, `NLD`,
`NOR`, `NPL`, `NRU`, `NZL`, `OMN`, `PAK`, `PAN`, `PCN`, `PER`, `PHL`, `PLW`, `PNG`, `POL`,
`PRI`, `PRK`, `PRT`, `PRY`, `PSE`, `PYF`, `QAT`, `REU`, `ROU`, `RUS`, `RWA`, `SAU`, `SDN`,
`SEN`, `SGP`, `SGS`, `SHN`, `SJM`, `SLB`, `SLE`, `SLV`, `SMR`, `SOM`, `SPM`, `SRB`, `SSD`,
`STP`, `SUR`, `SVK`, `SVN`, `SWE`, `SWZ`, `SXM`, `SYC`, `SYR`, `TCA`, `TCD`, `TGO`, `THA`,
`TJK`, `TKL`, `TKM`, `TLS`, `TON`, `TTO`, `TUN`, `TUR`, `TUV`, `TWN`, `TZA`, `UGA`, `UKR`,
`UMI`, `URY`, `USA`, `UZB`, `VAT`, `VCT`, `VEN`, `VGB`, `VIR`, `VNM`, `VUT`, `WLF`, `WSM`,
`YEM`, `ZAF`, `ZMB`, `ZWE`, `UNIVERSAL`.

## `Prefecture`

Japanese prefectures, north to south in the standard JIS order.

`UNDEFINED`, `HOKKAIDO`, `AOMORI`, `IWATE`, `MIYAGI`, `AKITA`, `YAMAGATA`, `FUKUSHIMA`,
`IBARAKI`, `TOCHIGI`, `GUNMA`, `SAITAMA`, `CHIBA`, `TOKYO`, `KANAGAWA`, `NIIGATA`, `TOYAMA`,
`ISHIKAWA`, `FUKUI`, `YAMANASHI`, `NAGANO`, `GIFU`, `SHIZUOKA`, `AICHI`, `MIE`, `SHIGA`,
`KYOTO`, `OSAKA`, `HYOGO`, `NARA`, `WAKAYAMA`, `TOTTORI`, `SHIMANE`, `OKAYAMA`, `HIROSHIMA`,
`YAMAGUCHI`, `TOKUSHIMA`, `KAGAWA`, `EHIME`, `KOCHI`, `FUKUOKA`, `SAGA`, `NAGASAKI`,
`KUMAMOTO`, `OITA`, `MIYAZAKI`, `KAGOSHIMA`, `OKINAWA`.

Spec quirk: the schema defines this enum under the misspelled name `Perfecture`, while the
`search-activities` query parameter is correctly named `prefecture`. The **values** are
identical, so this only matters if you are reading generated model class names.
