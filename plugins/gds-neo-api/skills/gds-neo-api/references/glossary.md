# Glossary — English / 中文 / 日本語

For answering questions in Chinese or Japanese, and for reading a supplier's or an
integrator's terminology back onto the API's field names. The API itself is English-only:
**always use the English field and enum names on the wire**, whatever language you answer in.

## Core objects

| API term | 中文 | 日本語 | What it is |
| --- | --- | --- | --- |
| OTA | 在线旅行社 | オンライン旅行会社 | You — the party integrating and reselling. |
| Supplier | 供应商 | サプライヤー / 仕入先 | The party operating the attraction or service. |
| Activity | 活动 / 产品 | アクティビティ / 商品 | The sellable product, e.g. "Tokyo Skytree admission". |
| Plan | 方案 / 套餐 | プラン | A variant under an activity, e.g. "ticket + shopping coupon". |
| Plan item | 场次 / 时段 | プランアイテム / 時間枠 | A bookable start time under a plan. |
| Unit | 票种 / 人数类型 | ユニット / 券種 | A participant type, e.g. adult, child, infant. |
| Allotment | 库存 / 配额 | 在庫 / アロットメント | Remaining sellable count. |
| Booking | 预订 | 予約 | A confirmed sale. |
| Reservation / session | 暂占 / 预占 | 仮予約 | An unconfirmed hold, identified by `session_id`. |
| Voucher | 凭证 / 兑换券 | バウチャー / 引換券 | The document the traveler presents. |
| Redemption | 兑换 / 核销 | 引換 / もぎり | Using the voucher at the venue. |
| Cancellation policy | 取消政策 | キャンセルポリシー | The fee schedule for cancelling. |
| Cancellation fee | 取消手续费 | キャンセル料 | `cancel_fee`. |
| Refund | 退款 | 返金 | `net_refund` / `gross_refund`. |
| Participant | 参加者 / 出行人 | 参加者 | One traveler. |
| Representative | 预订联系人 / 主联系人 | 予約代表者 | The booking contact — `first_name` / `last_name`. |
| Bundle | 打包产品 / 组合产品 | セット商品 / バンドル | A parent booking with child bookings. |

## IDs

| API field | 中文 | 日本語 | Note |
| --- | --- | --- | --- |
| `supplier_id` | 供应商 ID | サプライヤー ID | Use this, not the numeric `id`. |
| `activity_id` | 活动 ID | アクティビティ ID | |
| `plan_id` | 方案 ID | プラン ID | |
| `plan_item_id` | 场次 ID | プランアイテム ID | The start time. |
| `plan_unit_id` | 票种 ID | ユニット ID | Opaque; copy verbatim. |
| `session_id` / `booking_session_id` | 会话 ID / 暂占 ID | セッション ID | Pre-confirmation. Same value, two field names. |
| `booking_id` | 预订编号 | 予約番号 | Post-confirmation. |
| `agent_booking_id` | 我方订单号 | 代理店予約番号 | Your own reference. Always set it. |
| `supplier_booking_id` | 供应商订单号 | サプライヤー予約番号 | |
| `api-key-id` | API 密钥 ID | API キー ID | Public identifier, sent as a header. |
| API key secret | API 密钥 | API シークレット | Never sent. HMAC key material only. |
| `idempotent_key` | 幂等键 | 冪等キー | Max 64 chars, effective 24h. |

## Authentication

| Term | 中文 | 日本語 |
| --- | --- | --- |
| Signature | 签名 | 署名 |
| `signature-key` | 签名值 | 署名キー |
| `timestamp` | 时间戳 | タイムスタンプ |
| HMAC-SHA256 | HMAC-SHA256 哈希消息认证码 | HMAC-SHA256 |
| Base64-url encoding | URL 安全的 Base64 编码 | URL セーフ Base64 |
| Salt | 盐值 | ソルト |
| Clock skew | 时钟偏差 | 時刻ずれ |
| Sandbox | 测试环境 | サンドボックス / 検証環境 |
| Production | 生产环境 | 本番環境 |

## Flow

| Term | 中文 | 日本語 | Endpoint |
| --- | --- | --- | --- |
| Search activities | 搜索活动 | アクティビティ検索 | `search-activities` |
| Activity detail | 活动详情 | アクティビティ詳細 | `get-activity-detail` |
| Availability calendar | 库存日历 / 价格日历 | 在庫カレンダー | `get-price-and-availability-calendar` |
| Check availability and quote | 校验库存并计价 | 在庫確認・料金計算 | `check-availability-and-calculate-amount` |
| Reserve phase (hold) | 暂占阶段 | 仮予約 | `start-booking` |
| Confirm phase | 确认阶段 | 予約確定 | `final-booking` |
| Release a hold | 释放暂占 | 仮予約の解放 | `cancel-reservations` |
| Update participant info | 修改出行人信息 | 参加者情報の変更 | `update-booking-participant-info` |
| Cancellation quote | 取消试算 | キャンセル試算 | `start-cancel-booking` |
| Commit cancellation | 确认取消 | キャンセル確定 | `final-cancel-booking` |

## Confirmation types

| Value | 中文 | 日本語 |
| --- | --- | --- |
| `FREE_SALE` | 指定日期，不限量销售 | 日付指定・在庫無制限 |
| `FREE_SALE_OPEN_DATE` | 不指定日期，不限量销售（open ticket） | 日付指定なし・在庫無制限（オープン券） |
| `INVENTORY` | 指定日期，限量库存 | 日付指定・在庫あり |
| `REQUEST` | 指定日期，需人工审核 | 日付指定・リクエスト（要確認） |

## Booking statuses

| Value | 中文 | 日本語 |
| --- | --- | --- |
| `REQUEST_PENDING` | 待供应商确认 | リクエスト確認中 |
| `REQUEST_REJECTED` | 供应商拒绝 | リクエスト却下 |
| `CONFIRMED` | 已确认 | 予約確定 |
| `CANCELLED_BY_TRAVELER` | 旅客/OTA 取消 | 旅客都合によるキャンセル |
| `CANCELLED_BY_SUPPLIER` | 供应商取消 | サプライヤー都合によるキャンセル |
| `CANCEL_PENDING` | 取消处理中 | キャンセル処理中 |
| `CANCEL_FAILED` | 取消失败 | キャンセル失敗 |
| `INVALID` | 无效 | 無効 |

## Voucher / redemption statuses

| Value | 中文 | 日本語 |
| --- | --- | --- |
| `DISABLE` | 不适用 / 未启用 | 対象外 |
| `NOT_ISSUED` | 未出票 | 未発券 |
| `PARTIAL` | 部分已核销 | 一部引換済み |
| `ISSUED` | 全部已核销（或已过期） | 全て引換済み（または期限切れ） |

## Prices

| Field | 中文 | 日本語 | Use |
| --- | --- | --- | --- |
| `supplier_currency_price` | 供应商币种价格 | サプライヤー通貨の料金 | Authoritative original amount. |
| `payment_currency_price` | 结算币种价格 | 決済通貨の料金 | **Reconcile against this.** |
| `display_currency_price` | 展示币种价格 | 表示通貨の料金 | Traveler display only. |
| `net` | 净价 / 成本价 | ネット価格 / 仕入値 | Your cost. |
| `gross` | 含税零售价 | グロス価格 / 販売価格 | Retail. |
| `cancel_fee` | 取消手续费 | キャンセル料 | |
| `net_refund` | 净退款额 | ネット返金額 | Your settlement. |
| `gross_refund` | 零售退款额 | グロス返金額 | What the traveler gets back. |

## Booking form

| Term | 中文 | 日本語 |
| --- | --- | --- |
| `booking_form` | 预订表单定义 | 予約フォーム定義 |
| `booking_field_specs` | 标准字段定义 | 標準項目定義 |
| `custom_field_specs` | 自定义字段定义 | カスタム項目定義 |
| `participant_info` | 出行人信息 | 参加者情報 |
| `booking_representative_fields` | 预订联系人字段 | 予約代表者項目 |
| `others_information_fields` | 其他信息字段 | その他情報項目 |
| `user_information_fields` | 每位出行人字段 | 参加者ごとの項目 |
| `per_booking_custom_reservation_fields` | 订单级自定义字段 | 予約単位カスタム項目 |
| `per_participant_custom_reservation_fields` | 出行人级自定义字段 | 参加者単位カスタム項目 |
| `responses` | 填写值 | 回答値 |
| `choices` | 可选项 | 選択肢 |
| `required` | 必填 | 必須 |
| `optional` | 选填 | 任意 |
| `format_hint` | 格式提示 | 書式ヒント |
| `unit_index` | 出行人序号 | 参加者番号 |

## Common integrator phrasings

Recognise these and map them to the right thing.

| They say | 中文 | They mean |
| --- | --- | --- |
| "签名报错 401" | | `401 invalid signature` — go to the checklist in `auth.md`. |
| "时间戳超范围" | | `401 timestamp out of range` — UTC and clock sync. |
| "暂占没释放" / "仮予約が残る" | | Orphaned sessions — `list-reservations` + `cancel-reservations`. |
| "下单成功但状态不是已确认" | | A `REQUEST` product returning `REQUEST_PENDING`. |
| "库存对不上" / "在庫が合わない" | | `allotment_type` shared-pool semantics. |
| "退款金额和试算不一致" | | Fee recomputed server-side at cancel time. |
| "返回内容太大" | | `language_code` omitted. |
| "改了信息之后凭证还是旧的" | | Re-issue from the new `voucher_urls`. |
| "改一个字段其他都没了" | | `update-booking-participant-info` overwrites — send the full object. |
| "日期差一天" | | Activity timezone vs your timezone. |
| "多值参数不生效" | | `collectionFormat: multi` — repeat the parameter. |
