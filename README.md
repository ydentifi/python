<p align="center">
  <img src="https://raw.githubusercontent.com/ydentifi/python/main/.assets/ydentifi-logo.png" alt="Ydentifi" width="120">
</p>

<h1 align="center">Ydentifi Python Client</h1>

<p align="center">
  <a href="https://pypi.org/project/ydentifi"><img src="https://img.shields.io/badge/pypi-ydentifi-1BA1C0?style=flat-square" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.11%2B-1BA1C0?style=flat-square" alt="Python Version"></a>
  <a href="https://github.com/ydentifi/python/releases"><img src="https://img.shields.io/badge/release-v0.1.4-1BA1C0?style=flat-square" alt="Release"></a>
  <a href="https://ydentifi.io"><img src="https://img.shields.io/badge/ydentifi-identity%20server-1BA1C0?style=flat-square" alt="Ydentifi"></a>
</p>

The Python client of the [Ydentifi](https://ydentifi.io) identity server. A relying party uses it to create anonymous users, to enroll their phones, and to ask them to approve sign-ins and actions. The client speaks gRPC over mutual TLS. It comes in two forms: `Client`, which is synchronous, and `AsyncClient`, for asyncio.

```bash
pip install ydentifi
```

Python 3.11 or later is required. The SDK supports every CPython version the Python Software Foundation still supports, and drops each one at its end of life.

---

## Contents

- [Before the first call](#before-the-first-call)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Error handling](#error-handling)
- [Limits](#limits)
- [Deadlines and cancellation](#deadlines-and-cancellation)
- [Streams](#streams)
- [Concurrency](#concurrency)
- [API reference](#api-reference)
  - [Users](#users)
    - [create_user](#create_user) · [bulk_create_users](#bulk_create_users) · [get_user](#get_user) · [export_users](#export_users) · [update_user_status](#update_user_status) · [delete_user](#delete_user) · [unlock_user_request_limits](#unlock_user_request_limits)
  - [Devices](#devices)
    - [list_devices_for_user](#list_devices_for_user) · [revoke_device](#revoke_device) · [ban_device](#ban_device) · [unban_device](#unban_device)
  - [Challenges](#challenges)
    - [issue_auth_challenge](#issue_auth_challenge) · [await_challenge](#await_challenge) · [list_active_challenges](#list_active_challenges)
  - [TOTP](#totp)
    - [issue_user_totp_enrollment](#issue_user_totp_enrollment) · [verify_user_totp](#verify_user_totp)
  - [Enrollment and recovery](#enrollment-and-recovery)
    - [issue_enrollment_invite](#issue_enrollment_invite) · [issue_recovery_invite](#issue_recovery_invite)
- [Types](#types)
- [Version](#version)
- [Examples](#examples)

---

## Before the first call

The client calls a deployment of the Ydentifi server, which is self-hosted. The deployment's operator provides three inputs:

- **The server's address**: the host and port of its relying-party listener. The server listens on port 50051 unless its configuration sets another; a deployment behind a load balancer may publish another port, such as 443.
- **The relying party's certificate and private key**, issued by the deployment's certificate authority.
- **The deployment's CA bundle**, with which the client verifies the server.

The Ydentifi documentation describes how a deployment is run, in the [Quickstart](https://ydentifi.io/docs/quickstart); how relying-party certificates are issued, under [Certificates & PKI](https://ydentifi.io/docs/certificates); and how relying parties and users are managed, under [Manage RPs & users](https://ydentifi.io/docs/manage). The [documentation](https://ydentifi.io/docs) covers the rest, including the [limits and quotas](https://ydentifi.io/docs/limits).

---

## Quick start

```python
import ydentifi

with ydentifi.Client(
    server_addr="auth.example.com:443",
    cert_path="/etc/ydentifi/rp.crt",
    key_path="/etc/ydentifi/rp.key",
    ca_path="/etc/ydentifi/ca.pem",
) as client:
    opaque_id = client.create_user()
    print("created user:", opaque_id)
```

The asyncio client has the same methods, as coroutines and async generators:

```python
import asyncio

import ydentifi


async def main() -> None:
    async with ydentifi.AsyncClient(
        server_addr="auth.example.com:443",
        cert_path="/etc/ydentifi/rp.crt",
        key_path="/etc/ydentifi/rp.key",
        ca_path="/etc/ydentifi/ca.pem",
    ) as client:
        opaque_id = await client.create_user()
        print("created user:", opaque_id)


asyncio.run(main())
```

One client serves a whole application: it is built once, shared, and closed by its `with` block.

---

## Configuration

The keyword arguments give the configuration, and the environment supplies what they leave out. A file the environment names is read only when no argument gives that material.

**Required**

| Variable | Argument | Purpose |
|---|---|---|
| `YDFI_SERVER_ADDR` | `server_addr=` | The identity server's address: `host`, `host:port` or `[IPv6]:port` |
| `YDFI_TLS_CERT_PATH` | `cert_path=` or `cert_pem=` | The relying party's client certificate (PEM) |
| `YDFI_TLS_KEY_PATH` | `key_path=` or `key_pem=` | Its private key (PEM) |
| `YDFI_TLS_CA_PATH` | `ca_path=` or `ca_pem=` | The deployment's CA bundle that verifies the server (PEM) |

**Optional**

| Variable | Argument | Purpose |
|---|---|---|
| `YDFI_SERVER_NAME` | `server_name=` | The name the server's certificate is verified against. Required when the address's host is an IP address |
| — | `user_agent=` | Replaces the default user agent, `ydentifi-python/<version>` |
| — | `keepalive_time_seconds=` | The seconds between gRPC keepalive pings from the client |
| — | `keepalive_timeout_seconds=` | The seconds a keepalive answer is awaited |
| — | `channel_options=` | Further gRPC channel options, `[(name, value), ...]`. They follow the client's own options, which they cannot replace: the user agent, the verification name and keepalive |

The constructor raises `ConfigurationError` when:

- the address, the certificate and key, or the CA bundle are missing;
- a file cannot be read; the error names the file by its base name only, never its directory;
- the certificate, the key or the CA bundle does not parse, including any one certificate of a chain or bundle, or the key is not the certificate's;
- a CA bundle is given but holds no certificate;
- half a pair is given: `cert_path` without `key_path`, `cert_pem` without `key_pem`, or the other way round;
- the same material is given twice: `cert_path` with `cert_pem`, or `ca_path` with `ca_pem`;
- the address does not follow the address rule below;
- the address's host is an IP address and no `server_name` is given.

**The address rule.** An address is refused when it is empty, or when it holds any of `/ ? # @` or white space; this also refuses a URL scheme. It has one of three shapes: `[IPv6]:port`, `host:port` with exactly one colon, or a bare host with no colon. Anything else is refused: more than one colon outside brackets, a stray `[` or `]`, brackets that do not hold an IPv6 address, and an empty host. A port is ASCII decimal digits with a value from 1 to 65535; leading zeros are allowed, and an empty port is refused. When the host is an IP address, `server_name` is required and is the verification name. Otherwise the verification name is `server_name` when it is given, and the host, lower-cased, when it is not. Host shapes such as `127.1`, `0x7f.1` or `2130706433` are hostnames under this rule: certificate verification refuses them at the first call, with `UnavailableError`. The address is always resolved through DNS: `unix:443` names the host `unix`, never a local socket.

### What the three certificate inputs are for

Mutual TLS authenticates both ends of the connection. Three inputs serve it:

- **The client certificate** (`YDFI_TLS_CERT_PATH`, `cert_path`, `cert_pem`) identifies the relying party to the server. It names the relying party's ID, and the deployment's certificate authority issued it. The server accepts any certificate that authority issued for that ID until it expires. A renewed certificate therefore works beside the old one, and a leaked key works until its certificate expires.
- **The private key** (`YDFI_TLS_KEY_PATH`, `key_path`, `key_pem`) proves possession of that certificate. Its file is to be readable by the relying party's process only.
- **The CA bundle** (`YDFI_TLS_CA_PATH`, `ca_path`, `ca_pem`) works the other way: it lets the client check that it reached the real server. It is required, and the deployment's operator supplies it: the server's certificate comes from the deployment's own CA, and gRPC's bundled public roots, which would trust any server a public CA names for the host, are never used.

The server accepts TLS 1.3 only. gRPC's Python API sets no minimum version on the client's side, so the client would accept TLS 1.2 from a server that offered only that version and held a certificate the CA bundle trusts. The Go SDK sets TLS 1.3 as its minimum.

### Renewing the certificate

A certificate given as files (`cert_path` and `key_path`, or `YDFI_TLS_CERT_PATH` and `YDFI_TLS_KEY_PATH`) is read again at most once a minute, by the next call. When the certificate file holds a new certificate, inside its validity dates, with the key it was issued for, that call and every later one go on a new channel that presents it. The channel it replaces stays open, for the calls still in flight on it, until `close()`; each renewal therefore keeps one more channel until then.

Each file is best replaced atomically: a new file is written, then renamed over the old one. The certificates in the file are compared with those in use by their DER encoding; the same certificates, in any PEM layout or line ending, are not a renewal.

The read is made by one call at a time. `Client` holds a lock for it, so calls made meanwhile wait a few milliseconds. `AsyncClient` reads the files in a worker thread (`asyncio.to_thread`) under an `asyncio.Lock`, so the event loop does not wait; the read runs in the loop's default executor, and a call can run past its `timeout` when the application's own work holds every thread of that executor.

A new pair the client does not use is logged at `WARNING` on the `ydentifi._cert_files` logger, under `ydentifi`, once while the same problem lasts: a file that cannot be read, a pair that does not parse or does not match, or a certificate outside its validity dates. A pair whose two files are caught between their two renames does not match, and is read again a minute later. The log names files by their base name only.

A certificate given as `cert_pem` and `key_pem` is used for the client's lifetime. A new client is built to renew it.

---

## Error handling

A call the server refuses raises a subclass of `StatusError`. A refusal is caught by its kind:

```python
try:
    user = client.get_user(opaque_id)
except ydentifi.NotFoundError:
    ...  # no such user
```

or read in detail:

```python
try:
    user = client.get_user(opaque_id)
except ydentifi.StatusError as err:
    print(err.code, err.reason.name, err.trace_id, err.subject)
    if err.reason == ydentifi.ErrorReason.USER_LOCKED:
        ...  # the user is locked
```

### Error kinds

| Exception | gRPC code | What it means |
|---|---|---|
| `NotFoundError` | `NOT_FOUND` | The user, device or challenge does not exist for the calling relying party. Another relying party's gets the same answer |
| `AlreadyExistsError` | `ALREADY_EXISTS` | What the call would create already exists, as on a retry with the same `challenge_id` |
| `UnauthenticatedError` | `UNAUTHENTICATED` | The certificate passed the TLS handshake, but the server refused it: it names no relying party the server knows, or it expired after the connection opened |
| `PermissionDeniedError` | `PERMISSION_DENIED` | The deployment's operator has disabled the relying party |
| `ResourceExhaustedError` | `RESOURCE_EXHAUSTED` | A per-user limit is spent (reason `RATE_LIMIT_EXCEEDED`), or the relying party's user cap is reached (`MAX_USERS_REACHED`) |
| `ChallengeTooSoonError` | `RESOURCE_EXHAUSTED` | The user's newest challenge is still open and under 15 seconds old. A `ResourceExhaustedError` |
| `FailedPreconditionError` | `FAILED_PRECONDITION` | The call is valid, but the user or the deployment is not in a state that allows it. `reason` says which |
| `DeviceLimitReachedError` | `FAILED_PRECONDITION` | The user already has 3 active devices. A `FailedPreconditionError` |
| `TOTPLockedError` | `FAILED_PRECONDITION` | The user's TOTP codes are locked after 100 wrong codes in a row. A `FailedPreconditionError` |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | A request field failed the server's checks. `field` names it |
| `UnavailableError` | `UNAVAILABLE` | The server could not be reached, the TLS handshake failed, or the server refuses every call for the deployment's licence |
| `AbortedError` | `ABORTED` | A concurrent call on the same user, device or key held a lock too long. Nothing changed, and a retry may succeed |
| `DeadlineExceededError` | `DEADLINE_EXCEEDED` | The call ran past its `timeout` or past the server's own limit. Also the builtin `TimeoutError`; see [Deadlines and cancellation](#deadlines-and-cancellation) |
| `CancelledError` | `CANCELLED` | The call was made after `close()`, or a synchronous call was in flight when `close()` ran. Not `asyncio.CancelledError` |
| `InternalError` | `INTERNAL` | The server failed |
| `ConfigurationError` | — | The client could not be built. See [Configuration](#configuration). Not a `StatusError` |

Every exception here is a `YdentifiError`. The gRPC code decides the class. Three reasons narrow it: `MAX_DEVICES_REACHED` under `FAILED_PRECONDITION`, `TOTP_LOCKED` under `FAILED_PRECONDITION` and `CHALLENGE_TOO_SOON` under `RESOURCE_EXHAUSTED`. A code not in the table raises a plain `StatusError`.

An answer of the server that the client cannot read, such as a time that is not RFC 3339, raises `MalformedResponseError`, a `YdentifiError` that is not a `StatusError`. A server that keeps to its protocol never causes it.

### StatusError

- `code` is the gRPC status code, a `grpc.StatusCode`.
- `reason` is the server's reason, an `ErrorReason`, such as `ydentifi.ErrorReason.USER_NOT_FOUND`; `err.reason.name` gives its name. It is `ErrorReason.UNSPECIFIED` when the status carries no detail: a transport error, or a status gRPC raised itself, such as a passed deadline.
- `message` is the status message.
- `trace_id` is the call's W3C trace ID, 32 hex characters, when the server attached one. The deployment's operators find the call in the server's logs by it.
- `field` is the request field that failed a check.
- `subject` is what the call referred to, as the call named it: the opaque ID on `USER_NOT_FOUND`, the device ID on `DEVICE_NOT_FOUND`. On `RATE_LIMIT_EXCEEDED` from a per-user limit and on `CHALLENGE_TOO_SOON`, it is `<relying party ID>:<opaque ID>`; for the limit on `unlock_user_request_limits`, it is `unlock_guard:<relying party ID>:<opaque ID>`.
- `auto_expires_at` is set on `RATE_LIMIT_EXCEEDED` from a per-user limit and on `CHALLENGE_TOO_SOON`: the UTC `datetime` from which the call is admitted again. A retry before then is refused. It is `None` when the server attached none.

`str(err)` is the message, followed by the trace ID when there is one. A `StatusError` survives `pickle`, so it can cross a process boundary.

### Errors any call can return

The tables under each method list that method's own errors. Any call can also raise these:

| Exception | Reason | When |
|---|---|---|
| `UnavailableError` | — | The server cannot be reached, or the TLS handshake refused the certificate: a CA the deployment does not use issued it, or it has expired. The handshake fails before any gRPC status exists, so there is no reason |
| `UnavailableError` | `LICENSE_USER_CAP_REACHED` | The deployment holds over 110% of its licensed seats. Every call is refused until its operator acts |
| `UnavailableError` | `SERVER_UNAVAILABLE` | The server cannot read its own seat counts, so it refuses rather than guess |
| `UnavailableError` | `SERVER_UNAVAILABLE` | The server's database did not answer in time, as when it is overloaded. Retry with backoff |
| `UnauthenticatedError` | `MTLS_CERT_REFUSED` | The certificate passed the handshake but names no relying party the server knows |
| `UnauthenticatedError` | `MTLS_CERT_EXPIRED` | The certificate expired after the connection opened. See [Renewing the certificate](#renewing-the-certificate) |
| `PermissionDeniedError` | `PERMISSION_DENIED` | The deployment's operator has disabled the relying party |
| `FailedPreconditionError` | `LICENSE_EXPIRED` | The deployment's licence expired more than 30 days ago |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | An ID is malformed: an opaque ID that is not 64 lowercase hex characters, a device ID that is not a UUID, a permanent ID over 256 bytes or not printable ASCII. `field` names it |
| `AbortedError` | `SERVER_UNAVAILABLE` | A concurrent call on the same user, device or key held a lock for over 5 seconds. Nothing changed, and a retry may succeed |
| `DeadlineExceededError` | — | The call ran past its `timeout`, or past 30 seconds, the server's limit for a call that is not a stream |
| `CancelledError` | — | The call was made after `close()`, or a synchronous call was in flight when `close()` ran |
| `InternalError` | — | The server failed. The message carries the trace ID: `YDFI_ERROR_SERVER_INTERNAL [<trace ID>]` |
| `InternalError` | `SERVER_INTERNAL` | The server could not read the relying party's record to authenticate the call |

The SDK never retries a call itself.

Some errors are Python's own, raised before any request is sent:

- A `str` argument holding a lone surrogate, which has no UTF-8 encoding, raises the `UnicodeEncodeError` that protobuf raises. Under asyncio, and for the streaming methods, it is raised when the call starts.
- A call that reaches the channel while `close()` closes it, on another thread, may raise the `ValueError` gRPC raises for a closed channel.

---

## Limits

Each user has limits of its own on the calls that reach the user's phone or test the user's codes. A call that finds a limit spent raises `ResourceExhaustedError` with reason `RATE_LIMIT_EXCEEDED`, and `auto_expires_at` says when it is admitted again.

Each limit holds a number of tries and earns them back one at a time. The deployment's operator chooses the relying party's plan; it is Standard unless the operator sets another.

| Call | Standard | Conservative | Permissive |
|---|---|---|---|
| `issue_auth_challenge` | 10, one back every 4 h | 3, one back every 24 h | 20, one back every hour |
| `verify_user_totp` (wrong codes and some refusals) | 5, one back every 15 min | 5, one back every 30 min | 10, one back every 5 min |
| `issue_enrollment_invite` | 5, one back every hour | 3, one back every 4 h | 10, one back every 30 min |
| `issue_recovery_invite` | 2, one back every 6 h | 2, one back every 24 h | 5, one back every 2 h |
| `issue_user_totp_enrollment` | 10, one back every hour | the same | the same |
| `unlock_user_request_limits` | 3, one back every 10 min | the same | the same |

- A limit that runs out refuses for at least 30 minutes, or until it has earned a try back if that takes longer.
- An approved challenge gives the user's challenge tries back in full. A denial, a dismissal or an expiry does not.
- `issue_auth_challenge` raises `ChallengeTooSoonError` while the user's newest challenge is still open and under 15 seconds old. That costs no try. An answer or an expiry admits the next challenge at once.
- A request that fails the server's checks (`INVALID_ARGUMENT`) costs no try on any call.
- `unlock_user_request_limits` gives a user all the user's tries back. It has a limit of its own, per user.
- There is no limit on the relying party as a whole.

Other bounds:

| What | Bound |
|---|---|
| Active devices per user | 3 |
| Users per relying party | Set by the deployment's operator (`MAX_USERS_REACHED`) |
| Challenge lifetime (`ttl_seconds`) | 30 to 300 seconds; 0 means 60 |
| Invite lifetime (`ttl_seconds`) | 60 to 600 seconds; 0 means 300 |
| Challenge context | 16 to 256 bytes; see [issue_auth_challenge](#issue_auth_challenge) |
| Invite context | Up to 256 bytes |
| Geofence radius | 50 to 500,000 meters |
| Match code | 0 (off) or 10 to 99 |
| `bulk_create_users` count | 1 to 1,000,000 |
| `bulk_create_users` idempotency key | 1 to 255 bytes of UTF-8, no NUL; at most 1,000 keys per relying party, each held for 30 days |
| `ban_device` reason | Up to 512 bytes of UTF-8, no NUL |
| A request message | 64 KiB; a larger one is refused with `ResourceExhaustedError`, reason `UNSPECIFIED` |
| Duration of a call that is not a stream | 30 seconds |

---

## Deadlines and cancellation

Every method takes a keyword-only `timeout`, in seconds. A call still running when it passes raises `DeadlineExceededError`, which is also the builtin `TimeoutError`.

- A call that is not a stream defaults to 30 seconds, the server's own limit.
- `export_users`, `bulk_create_users` and `await_challenge` default to `None`: no limit of the client's own. The server ends a wait on a challenge 5 seconds after the challenge expires.
- On a stream, the `timeout` covers the whole stream, from its start to its last item, not each item.
- `None` means no limit. A negative `timeout` is a deadline already passed, and the call fails with `DeadlineExceededError` before it is sent. A `timeout` of 0 sets the deadline to the moment the call starts: gRPC may then still send the call and return its answer.

```python
with contextlib.closing(client.await_challenge(challenge_id, timeout=70)) as frames:
    result = next(f for f in frames if f.status.is_terminal)
```

Under asyncio, `asyncio.timeout` and `asyncio.wait_for` bound a call too; on timeout they raise the builtin `TimeoutError`, not a `StatusError`. A task cancelled during a call raises `asyncio.CancelledError`, which the SDK does not rewrite, and the call is cancelled on the server. A call that is in flight when `AsyncClient.close()` runs also raises `asyncio.CancelledError` in the task that awaits it; the task itself was not cancelled, and inside a `TaskGroup` the group then exits without an error.

---

## Streams

Three methods read a server stream, and each is a generator (an async generator on `AsyncClient`):

- `export_users` yields users;
- `bulk_create_users` yields opaque IDs;
- `await_challenge` yields the frames of a challenge.

The call starts at the first iteration, and each new generator is a new call. A generator releases its stream when it is exhausted, when it raises, or when it is closed. Leaving a loop with `break` does not close it; `contextlib.closing` closes it at the end of a `with` block, and `contextlib.aclosing` at the end of an `async with` block:

```python
with contextlib.closing(client.export_users()) as users:
    for user in users:
        print(user.opaque_id)
```

```python
async with contextlib.aclosing(client.export_users()) as users:
    async for user in users:
        print(user.opaque_id)
```

A generator that is left open holds its stream until it is garbage-collected. After an error, a generator is finished: the next iteration ends it.

---

## Concurrency

`Client` is safe to share between threads, and `AsyncClient` between the tasks of one event loop. One instance per identity server is enough; one gRPC channel carries every call. `close()` may be called more than once: the first call closes the channel, and the channels renewals replaced. A call made after `close()` raises `CancelledError`.

An `AsyncClient` belongs to the event loop that runs when it is built, so it is built inside a coroutine of that loop. Built where no event loop runs, such as before `asyncio.run`, it raises `RuntimeError`, on every supported Python version.

A generator is read by one thread or task at a time.

---

## API reference

The signatures show `Client`. `AsyncClient` has the same methods: coroutines that are awaited, and async generators where `Client` has generators.

IDs:

- An **opaque ID** names a user: 64 lowercase hex characters. It is the only handle the server keeps for a user, so the relying party stores it against its own user record. It carries no meaning.
- A **device ID** names one enrollment of one phone: a UUID.
- A **permanent ID** names the phone itself. It is the same under every relying party and every deployment.
- A **challenge ID** names a challenge: a 26-character ULID.

### Users

#### create_user

Creates an anonymous user of the relying party.

```python
def create_user(self, *, timeout: float | None = 30.0) -> str: ...
```

**Returns** the new user's opaque ID.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `ResourceExhaustedError` | `MAX_USERS_REACHED` | The relying party has as many users as the operator allows. Deleting a user frees a place at once |

**Behavior**

- Every call creates a new user. There is no upsert.
- The server runs at most 4 `create_user` calls at once for one relying party. The rest wait, and a call that waits past 30 seconds raises `DeadlineExceededError`. Many users are created with `bulk_create_users`.

---

#### bulk_create_users

Creates many users in one streamed call, as when an existing user base moves onto Ydentifi.

```python
def bulk_create_users(
    self, count: int, idempotency_key: str, *, timeout: float | None = None
) -> Generator[str, None, None]: ...
```

**Parameters**

- `count` — how many users to create: 1 to 1,000,000.
- `idempotency_key` — a name for the batch, 1 to 255 bytes. A call again with the same key never creates twice. The same key always carries the same `count`.

**Returns** a generator of opaque IDs; an async generator on `AsyncClient`.

```python
with contextlib.closing(client.bulk_create_users(1000, "migration-2026-01")) as ids:
    created = set(ids)
print(len(created), "of 1000")
```

**Errors**, raised while iterating:

| Exception | Reason | When |
|---|---|---|
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `count` is out of range, the key is empty, too long or holds NUL, or the key was used before with another `count`. `field` is `count` when `count` is out of range, and `idempotency_key` otherwise |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | A new key while the relying party already holds 1,000 keys. `field` is `idempotency_key`, and there is no retry time: each key is held for 30 days from its first user. A key the relying party already holds is never refused |
| `AbortedError` | `SERVER_UNAVAILABLE` | Another call under the same key got there first. A call again with the same key resumes |

**Behavior**

- Users are created in chunks of 500.
- A call again with the same key first yields the IDs the key already created that still exist, including any an interrupted call created but never delivered. Then it creates what is missing. An ID can therefore arrive in more than one call, and the IDs are best kept as a set.
- Reaching the relying party's user cap is not an error. The iteration ends normally with fewer IDs than `count`. Once the operator raises the cap, a call again with the same key creates the rest.

---

#### get_user

Returns one user.

```python
def get_user(self, opaque_id: str, *, timeout: float | None = 30.0) -> User: ...
```

**Returns** the [`User`](#user).

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. Another relying party's user gets the same answer. `subject` is the opaque ID sent |

---

#### export_users

Streams every user of the relying party, 500 to a page, for exports and for reconciliation with the relying party's own records.

```python
def export_users(
    self, start_after_id: str = "", *, timeout: float | None = None
) -> Generator[User, None, None]: ...
```

**Parameters**

- `start_after_id` — where to resume. Empty starts from the beginning; an opaque ID the export returned continues after it.

**Returns** a generator of [`User`](#user)s; an async generator on `AsyncClient`.

**Errors**, raised while iterating:

| Exception | Reason | When |
|---|---|---|
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `start_after_id` names no user of the relying party, including one deleted since the export returned it. The export resumes from the ID before it, or starts again from the beginning |

**Behavior**

- The order is not specified.
- The server checks the certificate again before every page, so `UnauthenticatedError` or `PermissionDeniedError` can arrive mid-stream.

---

#### update_user_status

Locks or unlocks a user.

```python
def update_user_status(
    self, opaque_id: str, status: UserStatus, *, timeout: float | None = 30.0
) -> None: ...
```

**Parameters**

- `status` — `UserStatus.LOCKED` or `UserStatus.ACTIVE`. A locked user is refused challenges, TOTP checks and invites (`USER_LOCKED`).

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `status` is neither `ACTIVE` nor `LOCKED` |
| `AbortedError` | `SERVER_UNAVAILABLE` | A status change or TOTP enrollment for the same user is in flight. A retry may succeed |

**Behavior**

- Locking a user ends every open challenge of the user as `EXPIRED`, and revokes the user's live invites. Unlocking brings neither back.
- Setting the status the user already has succeeds and changes nothing.

---

#### delete_user

Deletes a user, with the user's devices and challenges.

```python
def delete_user(self, opaque_id: str, *, timeout: float | None = 30.0) -> None: ...
```

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |

**Behavior**

- The user's bans stay. `unban_device` with the phone's `permanent_id` lifts one later.
- A wait in progress on one of the user's challenges is not woken by the deletion: it ends with an `EXPIRED` frame when the challenge expires, up to 5 seconds later.
- An opaque ID is never reused.

---

#### unlock_user_request_limits

Gives a user back every try of every [per-user limit](#limits).

```python
def unlock_user_request_limits(self, opaque_id: str, *, timeout: float | None = 30.0) -> None: ...
```

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | This user's unlocks are spent: 3, then one back every 10 minutes, on every plan. `subject` is `unlock_guard:<relying party ID>:<opaque ID>` |

**Behavior**

- It belongs after a completed recovery. A lost phone may have spent the user's challenge tries on sign-ins it could not answer, and enrolling the new phone does not give them back.
- It does not belong before one: the limit on unanswered challenges is what stops a flood of approval requests.
- It does not unlock TOTP codes locked after 100 wrong codes (`TOTPLockedError`). Only a new secret does.

---

### Devices

A user may have 3 active devices. No call returns a device's history; the deployment's server logs hold it.

#### list_devices_for_user

Lists a user's devices.

```python
def list_devices_for_user(
    self, opaque_id: str, *, timeout: float | None = 30.0
) -> list[Device]: ...
```

**Returns** the user's [`Device`](#device)s, in every status: active, inactive and banned. The list is empty for a user with no device.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |

**Behavior**

- Each device carries its phone's permanent ID. It is the same under every relying party and every deployment, so relying parties that compare their lists can link one phone's users.

---

#### revoke_device

Revokes one device. It can no longer sign in or approve, and the user's open challenges end if the device was active.

```python
def revoke_device(
    self, opaque_id: str, device_id: str, *, timeout: float | None = 30.0
) -> None: ...
```

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `DEVICE_NOT_FOUND` | The user has no device with that ID under the relying party. An unknown opaque ID, another user's device and another relying party's device all get the same answer. `subject` is the device ID sent |

**Behavior**

- The device goes to `DeviceStatus.INACTIVE`. The phone is enrolled again to be used again.
- Revoking a device that is not active succeeds and changes nothing.
- The user's TOTP secret is not replaced: the device's copy keeps giving valid codes. `issue_user_totp_enrollment` with `reuse_existing=False`, called **after** the revocation, takes it away. A new secret goes to every device the user still has.

---

#### ban_device

Bans a phone from the relying party: it cannot enroll again under any of the relying party's users.

```python
def ban_device(
    self, opaque_id: str, device_id: str, reason: str, *, timeout: float | None = 30.0
) -> int: ...
```

**Parameters**

- `device_id` — one of the user's devices. The ban falls on its phone.
- `reason` — a note on why, up to 512 bytes, such as `"reported stolen"`.

**Returns** how many active devices on that phone the ban moved to `DeviceStatus.BANNED`: 0 or 1, since a phone is active under one of the relying party's users at a time.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `DEVICE_NOT_FOUND` | As for `revoke_device` |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `reason` is over 512 bytes or holds NUL |

**Behavior**

- The ban is on the phone's permanent ID, not on one enrollment.
- Banning a phone that is already banned succeeds and changes nothing.
- A ban applies to the relying party that made it only.
- The user's TOTP secret is not replaced, as for `revoke_device`; the secret is replaced after the ban, not before.

---

#### unban_device

Lifts the ban on a phone, named by one of its device IDs or by its permanent ID.

```python
def unban_device(
    self,
    opaque_id: str,
    *,
    device_id: str = "",
    permanent_id: str = "",
    timeout: float | None = 30.0,
) -> None: ...
```

**Parameters**

- `device_id` — one of the user's devices; the ban on its phone is lifted.
- `permanent_id` — the phone's permanent ID, as `list_devices_for_user` returned it: up to 256 bytes of printable ASCII. With a permanent ID the server does not look the user up, but `opaque_id` must still be well formed.

Exactly one of the two is given. The SDK sends what it is given, and the server refuses both and neither with `InvalidArgumentError`, `field` `device_id`; a malformed permanent ID is refused with `field` `permanent_id` (see [Errors any call can return](#errors-any-call-can-return)).

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `DEVICE_NOT_FOUND` | With `device_id`: as for `revoke_device` |

**Behavior**

- The banned devices on that phone go to `DeviceStatus.INACTIVE`, not active: the user enrolls the phone again.
- Unbanning a phone that is not banned succeeds and changes nothing.
- Deleting a user deletes the user's devices but keeps the ban, so after `delete_user` no device ID is left: the permanent ID names the phone.

---

### Challenges

A challenge asks the user to approve something on the user's phone. `issue_auth_challenge` issues it, and `await_challenge` reads the answer.

#### issue_auth_challenge

Issues a challenge to the user's phones.

```python
def issue_auth_challenge(
    self, req: IssueAuthChallengeRequest, *, timeout: float | None = 30.0
) -> Challenge: ...
```

**Parameters**, in `IssueAuthChallengeRequest`, passed by keyword:

- `opaque_id: str` — the user.
- `context: bytes` — **required.** What the user is asked to approve, as UTF-8 text the phone shows: 16 to 256 bytes, such as `"Approve a transfer of $1,000 to ACME Corp".encode()`. The user's signature covers it. [The challenge text](#the-challenge-text) lists what is refused.
- `min_strength: AuthStrength` — **required.** The weakest unlock an approval may use: `AuthStrength.DEVICE_ACCESS` (biometric or passcode) or `AuthStrength.BIOMETRIC` (biometric only). An approval always meets it; a decline is not held to it.
- `ttl_seconds: int = 0` — how long the challenge stays open: 30 to 300 seconds. 0 means 60.
- `match_code: int = 0` — optional number matching. The relying party shows this number, 10 to 99, on its own screen, and the user types it on the phone before approving. 0 turns it off.
- `location_constraint: LocationConstraint | None = None` — an optional geofence; see [LocationConstraint](#locationconstraint).
- `challenge_id: str = ""` — an optional ULID chosen before the call, so that a retry after a lost response cannot create a second challenge. Empty lets the server create the ID.

**Returns** a [`Challenge`](#challenge). `qr_encoded` is a link to the challenge, rendered as a QR code exactly as given; a phone that scans it opens the challenge. The user's enrolled phones also receive the challenge without a scan.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `NotFoundError` | `NO_ACTIVE_DEVICE_FOR_USER` | The user has no active device |
| `FailedPreconditionError` | `USER_LOCKED` | The user is locked |
| `FailedPreconditionError` | `DEVICE_INCAPABLE` | None of the user's active devices can meet `min_strength`, as when a biometric is asked for and no phone has one set up |
| `InvalidArgumentError` | `MIN_STRENGTH_REQUIRED` | `min_strength` is `AuthStrength.UNSPECIFIED` |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | A field is out of bounds or malformed: `context` (see below), `ttl_seconds`, `match_code`, the geofence, or a `challenge_id` that is not an uppercase ULID. Or `challenge_id` was already used for a different request. `field` names it |
| `AlreadyExistsError` | `CHALLENGE_ALREADY_EXISTS` | `challenge_id` was already used for this same request: the retry found the challenge issued before |
| `ChallengeTooSoonError` | `CHALLENGE_TOO_SOON` | The user's newest challenge is still open and under 15 seconds old. No try was spent. A retry succeeds after `auto_expires_at`, or once the user answers |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | The user's challenge tries are spent; see [Limits](#limits) |

Each challenge issued costs one of the user's tries. So do these refusals: `USER_LOCKED`, `DEVICE_INCAPABLE`, and a reused `challenge_id` (`CHALLENGE_ALREADY_EXISTS`, or `INVALID_ARGUMENT` for a different request). An unknown user, a user with no active device, and `ChallengeTooSoonError` cost none.

**Behavior**

- A reused `challenge_id` is the same request when the user, `context`, `min_strength`, `match_code` and geofence are the same; `ttl_seconds` is not compared.
- A phone that reports only a biometric can answer `DEVICE_ACCESS` challenges only by biometric; when every active phone reports so, `DEVICE_ACCESS` is refused with `DEVICE_INCAPABLE` too. A phone whose report is older than 24 hours is not held to it.
- An approval with a weaker unlock than `min_strength` is refused at the phone. The challenge stays open until another answer or its expiry.
- Only the phones active when the challenge was issued can answer it.

**Accessibility.** `AuthStrength.BIOMETRIC` accepts a biometric only, with no passcode. Some people cannot use one, for medical or physical reasons, or for a while after an injury. A relying party that keeps a flag on its own user record can ask those users for `AuthStrength.DEVICE_ACCESS`, which accepts the passcode. Ydentifi never sees the flag.

##### The challenge text

`context` is shown to the user, and the user's signature commits to its bytes. The server therefore refuses text a phone might show as something other than its bytes. It must hold 16 to 256 bytes, not counting white space and characters that draw a blank, and at least one letter, digit or emoji. Judged against Unicode 17.0, it is refused if it holds:

- bytes that are not UTF-8, or text not in Unicode NFC;
- a control character, tabs and line breaks included, or U+2028 or U+2029;
- white space at either end or two in a row, or any space but U+0020, U+00A0, U+202F and U+3000;
- a private-use, noncharacter or unassigned code point, or U+FFFC;
- a bidirectional formatting character: the embeddings, overrides and isolates, and the marks U+200E, U+200F and U+061C;
- a zero-width joiner or non-joiner outside an emoji sequence Unicode recommends or the words of a script it shapes;
- a variation selector outside a sequence that selects a glyph, or any ideographic variation selector (U+E0100–U+E01EF);
- a tag character outside the flags of England, Scotland and Wales, or a regional indicator outside a recommended flag;
- any other invisible or formatting character;
- a character that draws a blank though it is not a space (U+2800, U+303F, U+1D159, U+13441, U+13442, U+1DA7F, U+1DA80, U+16FE4);
- a combining mark with nothing to mark, or more than six on one character;
- an overlay or enclosing mark (canonical combining class 1, such as the strokes U+0334–U+0338, and general category Me, such as U+20DD–U+20E0), which can strike out an amount the signature still commits to. U+20E3 at the end of a keycap emoji Unicode recommends is allowed.

The refusal names the character and its byte offset.

Real text uses some of what is refused, so it is normalized or stripped before the challenge is issued (`unicodedata.normalize("NFC", text)` handles the normalization):

- an emoji selector after an emoji that already shows as one (a star or check mark followed by U+FE0F), and a keycap without its U+FE0F;
- soft hyphens, and the zero-width space Thai, Khmer and Shan put between words;
- a zero-width non-joiner where it breaks no join (Persian after alef, Sorani at a word's end);
- right-to-left marks and isolates around numbers and names;
- ideographic variation selectors in Japanese names;
- the Bassa Vah tone marks, some Vedic accents and the Church Slavonic number signs;
- tabs, line breaks, and doubled, leading or trailing spaces, and other space characters;
- the blank Braille pattern between Braille words, where a space belongs instead;
- text not in NFC: decomposed letters, marks in another order (such as Arabic shadda before its vowel, or pointed Hebrew), and Devanagari, Bengali, Gurmukhi and Oriya letters in their precomposed nukta forms.

The check is partial. It lets through:

- a space or a no-break space in each gap between words (about one bit a gap);
- a joiner after a virama in scripts whose fonts draw the same either way, such as Tamil and Sinhala (about 51 bits in 256 bytes);
- standardized variation selectors on CJK ideographs (about 42 bits), and the selector that gives a Myanmar letter its dotted form (about one bit a letter);
- up to six marks on each letter;
- emoji sequences newer than a phone's fonts, which it shows as their parts;
- look-alike letters from other scripts.

Text that mixes right-to-left and left-to-right writing can display in another order than its bytes even without any of these characters, and nothing refuses that.

---

#### await_challenge

Streams a challenge's frames until the challenge ends.

```python
def await_challenge(
    self, challenge_id: str, *, timeout: float | None = None
) -> Generator[ChallengeResult, None, None]: ...
```

**Returns** a generator of [`ChallengeResult`](#challengeresult) frames; an async generator on `AsyncClient`. The first frame is the challenge's state when the stream opens: `PENDING`, `DELIVERED`, or already its outcome. The last frame is the first one whose status ends the challenge (`status.is_terminal`): `APPROVED`, `DENIED`, `REJECTED`, `EXPIRED`, `SUPERSEDED` or `DISMISSED`. The server then ends the stream, and the iteration ends.

```python
with contextlib.closing(client.await_challenge(challenge.challenge_id, timeout=70)) as frames:
    for frame in frames:
        print("status:", frame.status.name)
```

**Errors**, raised while iterating:

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `CHALLENGE_NOT_FOUND` | The relying party has no challenge with that ID. `subject` is the ID sent |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `challenge_id` is not a ULID |

**Behavior**

- A bound on the wait is advisable; see [Deadlines and cancellation](#deadlines-and-cancellation). The server holds the stream until the challenge expires plus 5 seconds, then sends `EXPIRED`, so the challenge's lifetime plus a margin is enough: 70 seconds for the default 60.
- The wait may start before or after the user answers. An answer given before the stream opened arrives as its first frame.
- A delivery to the phone after the stream opened is not reported: a stream that opened on `PENDING` goes from it to the outcome. A new stream opens on `DELIVERED`.
- A second wait on the same challenge, served by the same server, ends the first with `SUPERSEDED`.
- If the user is deleted during the wait, the wait ends `EXPIRED` when the challenge expires, up to 5 seconds later.
- A challenge ID in lowercase is not refused here, as `issue_auth_challenge` refuses it: it names no challenge, and the wait raises `CHALLENGE_NOT_FOUND`.
- `signature` is the phone's signature over the challenge. The server checked it before declaring `APPROVED`. No call returns the phone's key, so the signature cannot be checked by the relying party; it is kept as a record.

---

#### list_active_challenges

Lists a user's open challenges: those pending or delivered, not yet ended.

```python
def list_active_challenges(
    self, opaque_id: str, *, timeout: float | None = 30.0
) -> list[ActiveChallenge]: ...
```

**Returns** the user's [`ActiveChallenge`](#activechallenge)s, possibly none.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |

**Behavior**

- A challenge past its expiry that nothing had ended yet is ended as `EXPIRED` by the listing, and is not listed.

---

### TOTP

Every user has a TOTP secret from the moment the user is created, and the user's enrolled phones receive it. Codes are 6 digits, a new one every 30 seconds, SHA-1. The secret can also be given to a standard authenticator app.

#### issue_user_totp_enrollment

Returns the user's TOTP secret, or replaces it with a new one.

```python
def issue_user_totp_enrollment(
    self, opaque_id: str, *, reuse_existing: bool, timeout: float | None = 30.0
) -> TOTPEnrollment: ...
```

**Parameters**

- `reuse_existing` — **required**, by keyword. `True` returns the current secret. `False` replaces it with a new one, which also unlocks codes locked after 100 wrong codes.

**Returns** a [`TOTPEnrollment`](#totpenrollment): the secret in base32, its `otpauth://` URL, and that URL as a 255×255 QR code PNG. The URL's label may be changed, for example to show the user's name in the authenticator app.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `FailedPreconditionError` | `USER_LOCKED` | The user is locked |
| `FailedPreconditionError` | `TOTP_SECRET_KEY_UNAVAILABLE` | `reuse_existing` is `True` and the stored secret cannot be read. A call with `False` issues a new one |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | The user's enrollment tries are spent: 10, then one back every hour. Every call spends one |
| `AbortedError` | `SERVER_UNAVAILABLE` | A status change or TOTP enrollment for the same user is in flight. A retry may succeed |

**Behavior**

- A new secret goes to every device the user still has.
- A secret is taken away from a phone in this order: the phone is removed (`revoke_device`, `ban_device` or `issue_recovery_invite`); this method is called with `reuse_existing=False`; the user is then locked, if a lock is wanted. A phone removed after the new secret was issued may already hold it. Until this call, the old secret's codes still work, so the calls follow one another at once. A locked user is refused, which is why the lock comes last.

---

#### verify_user_totp

Checks a TOTP code the user typed.

```python
def verify_user_totp(self, opaque_id: str, code: str, *, timeout: float | None = 30.0) -> bool: ...
```

**Parameters**

- `code` — exactly 6 ASCII digits.

**Returns** `True` when the code is right. A code is accepted for the current 30-second step or the steps on either side, and only when its step is later than the step of the last code accepted for the same secret. **A code works once:** a code already accepted returns `False` and spends an attempt, as a wrong code does, and so does an unused code of a step no later than the last accepted one.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `code` is not 6 ASCII digits |
| `FailedPreconditionError` | `USER_LOCKED` | The user is locked. The refusal spends an attempt |
| `TOTPLockedError` | `TOTP_LOCKED` | The user's codes are locked after 100 wrong codes in a row |
| `FailedPreconditionError` | `TOTP_SECRET_KEY_UNAVAILABLE` | The stored secret cannot be read. `issue_user_totp_enrollment` issues a new one |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | The user's tries for wrong codes are spent; see [Limits](#limits) |
| `AbortedError` | `SERVER_UNAVAILABLE` | Another `verify_user_totp` for the same user is in flight. A retry may succeed |

**Behavior**

- A wrong code returns `False` and spends a try. So do the `USER_LOCKED` and `TOTP_SECRET_KEY_UNAVAILABLE` refusals. A right code spends none.
- 100 wrong codes in a row lock the user's codes. The 100th is checked and charged like any other, and raises `TOTPLockedError`. Every code after it raises `TOTPLockedError` without being checked, a right one too. A right code before the 100th starts the count again.
- Only codes lock. The user stays active, and challenges still work. `User.totp_locked` shows the lock. Only `issue_user_totp_enrollment` with `reuse_existing=False` unlocks it.

---

### Enrollment and recovery

A user has one live invite at a time. Issuing an invite, of either kind, revokes the user's previous one.

#### issue_enrollment_invite

Issues an invite that the user scans with the Ydentifi app to enroll a phone.

```python
def issue_enrollment_invite(
    self, req: IssueEnrollmentInviteRequest, *, timeout: float | None = 30.0
) -> EnrollmentInvite: ...
```

**Parameters**, in `IssueEnrollmentInviteRequest`, passed by keyword:

- `opaque_id: str` — the user.
- `ttl_seconds: int = 0` — how long the invite can be scanned: 60 to 600 seconds. 0 means 300.
- `context: bytes = b""` — optional, up to 256 bytes. The phone does not show it, and the enrollment does not sign it.

**Returns** an [`EnrollmentInvite`](#enrollmentinvite--recoveryinvite). `qr_payload` is shown as a QR code.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `FailedPreconditionError` | `USER_LOCKED` | The user is locked. The refusal spends a try |
| `DeviceLimitReachedError` | `MAX_DEVICES_REACHED` | The user already has 3 active devices. No invite was issued, and a try was spent. Once the user is authenticated, the user chooses a device to revoke from `list_devices_for_user`, and an invite is issued again |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `ttl_seconds` or `context` is out of bounds |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | The user's invite tries are spent; see [Limits](#limits) |

**Behavior**

- An invite enrolls one phone, once.
- Once the phone has claimed the invite, it has 2 more minutes to finish enrolling, even past the invite's expiry.

---

#### issue_recovery_invite

Revokes all of a user's active devices and issues an invite to enroll a new phone, as when the user has lost the phone.

```python
def issue_recovery_invite(
    self, req: IssueRecoveryInviteRequest, *, timeout: float | None = 30.0
) -> RecoveryInvite: ...
```

**Parameters**, in `IssueRecoveryInviteRequest`: the same as for `issue_enrollment_invite`.

**Returns** a [`RecoveryInvite`](#enrollmentinvite--recoveryinvite): an invite, and `revoked_device_count`, how many devices the call revoked.

**Errors**

| Exception | Reason | When |
|---|---|---|
| `NotFoundError` | `USER_NOT_FOUND` | No user of the relying party has that opaque ID. `subject` is the opaque ID sent |
| `FailedPreconditionError` | `USER_LOCKED` | The user is locked |
| `InvalidArgumentError` | `INVALID_ARGUMENT` | `ttl_seconds` or `context` is out of bounds |
| `ResourceExhaustedError` | `RATE_LIMIT_EXCEEDED` | The user's recovery tries are spent; see [Limits](#limits) |

**Behavior**

- **It revokes every active device of the user,** in the same step as issuing the invite. None of them can sign in or approve again, and every open challenge of the user ends as `EXPIRED`.
- **The server takes the call as the authority.** The person is verified to be the user, out of band, before the call.
- The revoked phones keep their copy of the TOTP secret, and the new phone receives the same secret. When a lost phone may be in someone else's hands, `issue_user_totp_enrollment` with `reuse_existing=False` follows this call.
- After the recovery completes, `unlock_user_request_limits` gives back the challenge tries the lost phone spent.

---

## Types

Every type is a frozen dataclass. Times are timezone-aware `datetime`s in UTC.

Every enum is an `IntEnum`. A value newer than this SDK arrives as a member named `UNKNOWN_<n>` that equals its number, instead of raising.

### User

```python
@dataclass(frozen=True)
class User:
    opaque_id: str
    status: UserStatus
    created_at: datetime
    last_authenticated_at: datetime | None = None  # a UTC day, at midnight; None until the first
    last_activity_at: datetime | None = None  # a UTC day, at midnight; None until the first
    totp_locked: bool = False  # codes locked after 100 wrong codes in a row
```

`last_authenticated_at` and `last_activity_at` hold the day only, not the time.

### UserStatus

```python
class UserStatus(IntEnum):
    UNSPECIFIED = 0
    ACTIVE = 1
    LOCKED = 2
```

### Device

```python
@dataclass(frozen=True)
class Device:
    device_id: str  # one enrollment of one phone: for revoke, ban and unban
    permanent_id: str  # the phone itself, across enrollments: for unban_device after delete_user
    platform: DevicePlatform
    status: DeviceStatus
    created_at: datetime
    last_authenticated_at: datetime | None = None  # a UTC day, at midnight; None until the first
    name: str = ""
    model: str = ""  # what the phone said it is, such as "iPhone17,4"; unchecked
```

### DevicePlatform

```python
class DevicePlatform(IntEnum):
    UNSPECIFIED = 0
    IOS = 1
    ANDROID = 2
```

### DeviceStatus

```python
class DeviceStatus(IntEnum):
    UNSPECIFIED = 0
    ACTIVE = 1
    INACTIVE = 3  # revoked or replaced
    BANNED = 4
```

### Challenge

```python
@dataclass(frozen=True)
class Challenge:
    challenge_id: str
    qr_encoded: str  # rendered as a QR code, exactly as given
    expires_at: datetime
```

### ChallengeResult

```python
@dataclass(frozen=True)
class ChallengeResult:
    status: ChallengeStatus  # what happened
    expression: ChallengeExpression = ChallengeExpression.UNSPECIFIED  # what the user said
    signature: bytes = b""  # set on APPROVED, DENIED and REJECTED
    decline_reason: DeclineReason = DeclineReason.UNSPECIFIED  # set only on DENIED
    verification_failure: VerificationFailure = (
        VerificationFailure.UNSPECIFIED
    )  # set only on REJECTED
    location_result: LocationResult | None = None  # set only when the phone reported a location
    emitted_at: datetime | None = None
    auth_strength: AuthStrength = (
        AuthStrength.UNSPECIFIED
    )  # the unlock used; meets min_strength only on APPROVED
```

`location_result` is set when the phone reported a location with its approval, whether or not the challenge had a `LocationConstraint`. It is not set on a decline or a dismissal, nor when the phone reported no location.

### ChallengeStatus

```python
class ChallengeStatus(IntEnum):
    UNSPECIFIED = 0
    PENDING = 1
    DELIVERED = 2
    APPROVED = 3  # ends the challenge
    DENIED = 4  # ends it: the user refused
    EXPIRED = 5  # ends it
    SUPERSEDED = 6  # ends it
    DISMISSED = 7  # ends it
    REJECTED = 8  # ends it: the user agreed, a check refused
```

`status.is_terminal` says whether a status ends the challenge.

### ChallengeExpression / DeclineReason / VerificationFailure

```python
class ChallengeExpression(IntEnum):
    UNSPECIFIED = 0
    APPROVED = 1
    DECLINED = 2
    DISMISSED = 3


class DeclineReason(IntEnum):
    UNSPECIFIED = 0
    NOT_ME = 1
    SECURITY_CONCERN = 2
    WRONG_DETAILS = 3
    CANCELLED = 4


class VerificationFailure(IntEnum):
    UNSPECIFIED = 0
    LOCATION_MISMATCH = 1
    WRONG_MATCH_CODE = 2
```

### Telling a refusal from a failed check

`status` is what happened. `expression` is what the user said. They are usually the same, and come apart in one case: the user approves and a check refuses the approval. That arrives as `REJECTED`, with expression `APPROVED`.

```python
if result.status is ChallengeStatus.APPROVED:
    ...  # the user is let in
elif result.status is ChallengeStatus.DENIED:
    log(result.decline_reason)  # the reason the user gave
elif result.status is ChallengeStatus.REJECTED:
    log(result.verification_failure)  # the check that refused
```

Only `APPROVED` lets anyone in, so branching on `status` alone is safe. The other fields give an accurate record.

`REJECTED` with `WRONG_MATCH_CODE` is the one to act on. A user who approves and types a number that was not on the relying party's screen is what an approval driven from someone else's session looks like, which is what number matching is there to catch. Logging it as a decline records the opposite of what happened. An approval that fails both the match code and the geofence ends `REJECTED` with `WRONG_MATCH_CODE`.

### AuthStrength

```python
class AuthStrength(IntEnum):
    UNSPECIFIED = 0  # refused as a min_strength
    DEVICE_ACCESS = 1  # biometric or passcode
    BIOMETRIC = 2  # biometric only
```

### ActiveChallenge

```python
@dataclass(frozen=True)
class ActiveChallenge:
    challenge_id: str
    status: ChallengeStatus  # PENDING or DELIVERED
    context: bytes
    location_constraint: LocationConstraint | None
    issued_at: datetime
    expires_at: datetime
    delivered_at: datetime | None = None  # None until delivered
```

### LocationConstraint

```python
@dataclass(frozen=True, kw_only=True)
class LocationConstraint:
    latitude: float  # -90 to 90
    longitude: float  # -180 to 180
    radius_meters: int  # 50 to 500,000
    enforcement: LocationEnforcement  # required


class LocationEnforcement(IntEnum):
    UNSPECIFIED = 0  # refused
    ADVISORY = 1  # reported, not enforced
    REQUIRED = 2  # outside it, an approval is REJECTED
```

`enforcement` has no default: the server refuses `LocationEnforcement.UNSPECIFIED`.

### LocationResult

```python
@dataclass(frozen=True)
class LocationResult:
    bucket: LocationBucket
    accuracy: LocationAccuracy


class LocationBucket(IntEnum):
    UNSPECIFIED = 0
    WITHIN_RADIUS = 1
    NEAR = 2
    FAR = 3
    UNAVAILABLE = 4
    DENIED_BY_USER = 5


class LocationAccuracy(IntEnum):
    UNSPECIFIED = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
```

The phone checks the constraint itself and reports only a bucket and an accuracy class. The result carries no coordinates.

### EnrollmentInvite / RecoveryInvite

```python
@dataclass(frozen=True)
class EnrollmentInvite:
    invite_token: bytes  # left out of repr
    qr_payload: bytes  # shown as a QR code; left out of repr
    expires_at: datetime


@dataclass(frozen=True)
class RecoveryInvite:
    invite_token: bytes  # left out of repr
    qr_payload: bytes  # left out of repr
    expires_at: datetime
    revoked_device_count: int
```

`invite_token` and `qr_payload` are secrets: whoever holds them can enroll a phone for the user. `repr()` and `str()` leave them out; the fields read as normal.

### TOTPEnrollment

```python
@dataclass(frozen=True)
class TOTPEnrollment:
    qr_code_png_base64: str  # the otpauth:// URL as a QR code, a base64 PNG
    totp_url: str  # otpauth://totp/...
    secret_base32: str  # for manual entry
```

All three fields carry the TOTP secret, so they are kept out of logs and are not stored in plain text. `repr()` and `str()` leave all three out; the fields read as normal.

### StatusError

```python
class StatusError(YdentifiError):
    code: grpc.StatusCode
    reason: ErrorReason
    message: str
    trace_id: str
    field: str
    subject: str
    auto_expires_at: datetime | None
```

See [StatusError](#statuserror) under Error handling. `ydentifi.ErrorReason` is an `IntEnum` with a member for every reason the server sends; a reason newer than this SDK is `UNKNOWN_<n>`. Its names are the ones every Ydentifi SDK prints.

---

## Version

```python
ydentifi.__version__  # "0.1.4"
```

Versions are 0.x: a minor version may change the API.

---

## Examples

The [`examples/`](https://github.com/ydentifi/python/tree/main/examples) directory holds a script for every method, and [`status_error.py`](https://github.com/ydentifi/python/blob/main/examples/status_error.py) reads an error's reason and trace ID. Three use the asyncio client: [`async_export_users.py`](https://github.com/ydentifi/python/blob/main/examples/async_export_users.py), [`async_bulk_create_users.py`](https://github.com/ydentifi/python/blob/main/examples/async_bulk_create_users.py) and [`async_await_challenge.py`](https://github.com/ydentifi/python/blob/main/examples/async_await_challenge.py).
