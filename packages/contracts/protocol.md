# IPC Protocol v1

## Scope

This document describes the wire format exchanged between the Tauri host
(Rust) and the Python Agent Runtime over the chosen IPC transport
(Accepted: stdio JSON Lines; see ADR-IPC-001).

Future iterations will add `decision.*`, `agent.*`, `model.*`, `tool.*`
endpoints following the same envelope.

## Transport

- One JSON object per line, terminated by `\n` (LF).
- The Python process's **stdout** carries protocol messages only.
  Diagnostics must be written to **stderr**.
- The Rust host owns the process lifecycle. It spawns the Python
  runtime on demand, manages a request timeout, and recycles the
  process on irrecoverable errors.

## Envelope

Every request and response is a JSON object with the following required
fields:

| field              | request   | success   | error     | notes                          |
|--------------------|-----------|-----------|-----------|--------------------------------|
| `protocol_version` | required  | required  | required  | integer, currently `1`         |
| `request_id`       | required  | required  | required  | echoed back unchanged          |
| `method`           | required  | absent    | absent    | e.g. `health/check`            |
| `params`           | optional  | absent    | absent    | method-specific input          |
| `ok`               | absent    | `true`    | `false`   | boolean                        |
| `result`           | absent    | required  | absent    | method-specific output         |
| `error`            | absent    | absent    | required  | `{code, message}`              |

## Error codes

Stable codes mapped from transport and protocol failures:

- `backend_unavailable` — the Python runtime is not running, exited
  unexpectedly, or its pipe is closed.
- `timeout` — the configured request timeout elapsed before a response
  was read.
- `invalid_protocol` — the response could not be parsed as a JSON
  object, or the envelope did not satisfy the schema (missing
  `protocol_version` / `request_id`, mismatched `request_id`, etc.).
- `unknown_method` — the request method is not implemented by the
  runtime.

The host MUST map a non-`ok` response from the runtime to the
appropriate code. A parse error on stdout is also `invalid_protocol`.

## Versioning

Breaking changes (new required fields, removed fields, semantic
changes) MUST increment `protocol_version`. The host and the runtime
reject envelopes whose `protocol_version` does not match the supported
version with `invalid_protocol`.

## Examples

See `examples/health.request.json`, `examples/health.success.json`,
`examples/health.error.json`. JSON Schemas live in `schemas/`.
