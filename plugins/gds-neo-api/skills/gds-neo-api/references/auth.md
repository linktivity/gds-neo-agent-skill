# Authentication, headers, and environments

## Environments

| Environment | Base URL | Host value for signing |
| --- | --- | --- |
| Sandbox | `https://open-agent.gds-neo.link-dev.link` | `open-agent.gds-neo.link-dev.link` |
| Production | `https://open-agent.gds-neo.linktivity.io` | `open-agent.gds-neo.linktivity.io` |

Both are HTTPS-only. `Content-Type: application/json` for POST bodies; responses are
`application/json`.

Note the spec's `host` field is written as `https://open-agent.gds-neo.link-dev.link`
(with the scheme, which is unusual for Swagger 2.0). Generated clients sometimes end up
with a doubled scheme like `https://https//...`. If a client library produces a malformed
URL, strip the scheme from the host and set it separately. The **signing** host must
always be the bare hostname with no scheme and no trailing slash.

Sandbox and production credentials are different. Sandbox data is test data; bookings
made there are not real and vouchers are not valid for entry.

## The five headers

All five are required on every request. They are all `apiKey`-type headers in the spec's
`securityDefinitions`, and the spec applies them globally — there is no unauthenticated
endpoint.

| Header | Example | Meaning |
| --- | --- | --- |
| `ota-id` | `LINKTIVITY` | Your OTA identifier. Issued by Linktivity, use as-is. |
| `group-id` | `[default-group]:LINKTIVITY` | Group within the OTA. Issued by Linktivity, use as-is — the square brackets and colon are part of the value. |
| `api-key-id` | `VJgSBDVXXXXXXXXX` | Public identifier of your API key. Issued by Linktivity. |
| `timestamp` | `20260521T063324Z` | Current UTC time, `YYYYMMDDTHHMMSSZ`. Must be within ±5 minutes of server time. |
| `signature-key` | `3gjtSDLmvsr4M6RdQ9vY5sYPZ1Y7iVXXXXXXXXXXXXX=` | Per-request HMAC signature. See below. |

The **API key secret** is a sixth value that is never sent. It is paired with your
`api-key-id` and is issued out-of-band. It only ever appears as HMAC key material and
should live on your servers only — never in browser or mobile client code.

## Signature algorithm

`signature-key` is a chain of four HMAC-SHA256 operations, base64-url encoded with
padding retained.

```
k1 = HMAC-SHA256( key = "congaree" + apiKeySecret, msg = timestamp )
k2 = HMAC-SHA256( key = k1,                        msg = host      )
k3 = HMAC-SHA256( key = k2,                        msg = path      )
k  = HMAC-SHA256( key = k3,                        msg = "veltra"  )
signatureKey = base64url(k)        # keep the '=' padding
```

Each step's 32-byte raw digest becomes the **key** for the next step — not the hex string,
not the base64 string. Using a hex-encoded intermediate is the single most common cause of
`401 invalid signature`.

### Inputs

| Name | Value |
| --- | --- |
| `apiKeySecret` | The secret paired with your `api-key-id`. Issued out-of-band. |
| `timestamp` | Byte-for-byte the same string as the `timestamp` header, e.g. `20260521T063324Z`. |
| `host` | Bare request host, e.g. `open-agent.gds-neo.link-dev.link`. No scheme, no trailing slash. (The documented input is the hostname; since neither environment uses a non-default port this doesn't normally arise. If yours does, try without the port first.) |
| `path` | Request path only, e.g. `/v1/activity/search-activities`. Leading slash, no query string, no fragment. Sign the path **exactly as it appears in the request line** — including a trailing slash if your client sends one. |

The two literals `"congaree"` and `"veltra"` are fixed salts, lowercase, no padding or
separators. `"congaree"` is prefixed directly onto the secret with no delimiter.

### Encoding

The output is **URL-safe base64 with padding**: `+` → `-`, `/` → `_`, and the trailing
`=` characters are kept. Go's `base64.URLEncoding.EncodeToString` and Python's
`base64.urlsafe_b64encode` both produce exactly this. In languages without a URL-safe
variant, standard-base64-then-translate is correct — do not strip the padding.

### The request body is not signed

Only timestamp, host, and path go into the signature. Two POSTs to the same path within
the same second produce the same signature, which is expected. There is no body digest,
so retrying a request with a modified body does not require a new signature — but a new
`timestamp` does.

The consequence worth being explicit about: because the body is unsigned and the timestamp
window is ±5 minutes, a `signature-key` is a bearer credential for **any** body sent to that
path for up to five minutes. TLS is what protects it in transit. So don't log signature
headers, don't put them in URLs or client-side code, and don't relay a signed request through
an untrusted intermediary. The API key secret itself must never leave your servers.

## Reference implementations

These are the implementations published in the API documentation.

### Go

```go
func signatureKey(apiKeySecret, timestamp, host, path string) string {
    h := func(key, msg []byte) []byte {
        m := hmac.New(sha256.New, key)
        m.Write(msg)
        return m.Sum(nil)
    }
    k1 := h([]byte("congaree"+apiKeySecret), []byte(timestamp))
    k2 := h(k1, []byte(host))
    k3 := h(k2, []byte(path))
    k := h(k3, []byte("veltra"))
    return base64.URLEncoding.EncodeToString(k)
}

// timestamp: time.Now().UTC().Format("20060102T150405Z")
```

### Python

```python
import base64, hashlib, hmac, time

def signature_key(api_key: str, timestamp: str, host: str, path: str) -> str:
    def h(key: bytes, msg: bytes) -> bytes:
        return hmac.new(key, msg, hashlib.sha256).digest()
    k1 = h(b"congaree" + api_key.encode(), timestamp.encode())
    k2 = h(k1, host.encode())
    k3 = h(k2, path.encode())
    k  = h(k3, b"veltra")
    return base64.urlsafe_b64encode(k).decode()

timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
```

### Java

```java
static String signatureKey(String apiKey, String timestamp, String host, String path) throws Exception {
    byte[] k1 = hmacSha256(("congaree" + apiKey).getBytes(UTF_8), timestamp.getBytes(UTF_8));
    byte[] k2 = hmacSha256(k1, host.getBytes(UTF_8));
    byte[] k3 = hmacSha256(k2, path.getBytes(UTF_8));
    byte[] k  = hmacSha256(k3, "veltra".getBytes(UTF_8));
    return Base64.getUrlEncoder().encodeToString(k);
}

private static byte[] hmacSha256(byte[] key, byte[] msg) throws Exception {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key, "HmacSHA256"));
    return mac.doFinal(msg);
}

// timestamp: DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC).format(Instant.now())
```

Note `Base64.getUrlEncoder()` keeps padding; `getUrlEncoder().withoutPadding()` would break it.

### PHP

```php
function signatureKey(string $apiKey, string $timestamp, string $host, string $path): string {
    $h = fn($key, $msg) => hash_hmac('sha256', $msg, $key, true);   // true = raw output
    $k1 = $h('congaree' . $apiKey, $timestamp);
    $k2 = $h($k1, $host);
    $k3 = $h($k2, $path);
    $k  = $h($k3, 'veltra');
    return strtr(base64_encode($k), '+/', '-_');
}

$timestamp = gmdate('Ymd\THis\Z');
```

The `true` fourth argument to `hash_hmac` is essential — without it you get a hex string
and every subsequent step is wrong.

### JavaScript (Postman pre-request script)

```js
const apiKey = "YOUR_API_KEY";

const host = pm.variables.replaceIn(pm.request.url.getHost()).replace(/^https?:\/\//i, "");
const path = pm.variables.replaceIn("/" + pm.request.url.getPath()).replace(/\/+/g, "/");
const timestamp = new Date().toISOString().replace(/[-:]|\.\d+/g, "");

const hmac = (key, msg) => CryptoJS.HmacSHA256(msg, key);
const k1 = hmac("congaree" + apiKey, timestamp);
const k2 = hmac(k1, host);
const k3 = hmac(k2, path);
const k  = hmac(k3, "veltra");

const signature = CryptoJS.enc.Base64.stringify(k).replace(/\+/g, "-").replace(/\//g, "_");

pm.request.headers.upsert({ key: "timestamp",     value: timestamp });
pm.request.headers.upsert({ key: "signature-key", value: signature });
```

CryptoJS passes `WordArray` objects between steps, which preserves the raw bytes — this is
why the chaining works without explicit encoding. In Node.js with the built-in `crypto`
module, pass `Buffer`s and use `.digest()` with no encoding argument.

## Canonical request

```bash
curl 'https://open-agent.gds-neo.link-dev.link/v1/activity/search-activities?page_size=20' \
  --header 'ota-id: LINKTIVITY' \
  --header 'group-id: [default-group]:LINKTIVITY' \
  --header 'api-key-id: VJgSBDVxxxxxxxxx' \
  --header 'timestamp: 20260521T063324Z' \
  --header 'signature-key: 3gjtSDLmvsr4M6RdQ9vY5sYPZ1Y7iV...='
```

Signed inputs for this request: `timestamp=20260521T063324Z`,
`host=open-agent.gds-neo.link-dev.link`, `path=/v1/activity/search-activities`.
The `?page_size=20` is deliberately absent from the signature.

## Authentication errors

| HTTP | Message | Cause and fix |
| --- | --- | --- |
| 401 | `invalid api-key-id` | Header missing, or the value is unknown to this environment. Check you are not sending sandbox credentials to production. |
| 401 | `invalid signature` | HMAC mismatch. Work through the checklist below. |
| 401 | `timestamp out of range` | Your clock is more than ±5 minutes off. Sync to NTP. Also check you are generating UTC, not local time — a `+09:00` machine formatting local time will be exactly 9 hours out. |

### Signature debugging checklist

Work top to bottom; these are ordered by how often each is the culprit.

1. **Hex vs raw bytes between chain steps.** Each intermediate must be the 32 raw digest
   bytes. In PHP that means `hash_hmac(..., true)`; in Node, `.digest()` with no argument.
2. **`api-key-id` used as the HMAC secret.** These are two different values: `api-key-id` is
   the public identifier you send as a header, and the API key **secret** is the separate
   value you never send. Every reference implementation names its parameter `apiKey` /
   `api_key`, which invites exactly this mix-up. If the secret and the `api-key-id` look
   similar in length, check which one your config is actually loading.
3. **`$msg` and `$key` transposed.** PHP is `hash_hmac($algo, $data, $key)` — data first.
   Python is `hmac.new(key, msg, ...)` — key first. Go's `hmac.New(sha256.New, key)` then
   `Write(msg)`. CryptoJS is `HmacSHA256(message, key)` — message first. Porting between
   languages and keeping the argument order is a silent, total failure.
4. **Host includes the scheme.** Must be `open-agent.gds-neo.link-dev.link`, not
   `https://open-agent.gds-neo.link-dev.link`.
5. **Query string included in `path`.** Sign `/v1/activity/search-activities` only.
6. **Timestamp regenerated between signing and sending.** Compute it once, use the same
   string in both places.
7. **Padding stripped from the base64 output.** Keep the `=`.
8. **Standard base64 instead of URL-safe.** `+` and `/` must become `-` and `_`.
9. **Path mismatch between the signature and the request line.** A trailing slash, a
   different case, or different percent-encoding on one side but not the other. Sign the
   exact string you send.
10. **Wrong environment's secret**, or a secret with copy-paste whitespace around it.

`scripts/gds_sign.py` isolates this: feed it the secret, timestamp, host, and path and
compare its output against what the client produced. If they match, the problem is
elsewhere in the request; if they don't, one of the steps above is the reason.
