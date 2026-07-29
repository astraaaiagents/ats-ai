# Research: Is SSE the Right Real-Time Transport?

**Date:** 2026-07-26
**Context:** Agent-First AI-Native Recruiter Client Portal
**Decision:** PRD chose Server-Sent Events (SSE) over WebSockets

---

## 1. SSE vs WebSocket for This Use Case

### Architecture Fit

The portal has two real-time needs:

| Direction | Requirement | Best Fit |
|-----------|-------------|----------|
| Server -> Client | Proactive alerts (new candidate match, interview reminder, agent status) | **SSE** |
| Client -> Server | Chat messages, recruiter actions | **HTTP POST** |

This is a **predominantly server-push** pattern. SSE handles the server-to-client direction natively. Client-to-server traffic uses standard HTTP POST (REST), which is already the portal's primary communication pattern. There is no need for full-duplex communication over a single connection.

### Key Trade-offs

**SSE wins here because:**
- Chat messages are request-response (POST), not a streaming bidirectional channel.
- Alerts are inherently one-way (server pushes to client).
- SSE integrates naturally with the existing HTTP-based architecture.
- No need to manage a separate WebSocket protocol layer.

**WebSocket would only be needed if:**
- Chat required real-time bidirectional streaming (e.g., live typing indicators, concurrent message streams).
- The portal needed to send messages from client to server on the same persistent connection.
- Neither of these is a primary requirement.

**Verdict:** SSE is the right choice for the server->client direction. HTTP POST is the right choice for client->server. The PRD's direction is correct.

---

## 2. FastAPI SSE Support

FastAPI has first-class SSE support via two approaches:

**`EventSourceResponse`** (recommended):
- Dedicated SSE response class from `fastapi.responses`.
- Handles `text/event-stream` MIME type automatically.
- Supports async generators for clean streaming.
- Built-in SSE protocol compliance.

**`StreamingResponse`** (alternative):
- More generic, requires manual `text/event-stream` header.
- Must manually format SSE protocol (e.g., `data: {...}\n\n`).
- Works but is more error-prone.

### Production Robustness

`EventSourceResponse` is well-maintained and used in production FastAPI applications. Key considerations:

- **Async generators** work seamlessly with FastAPI's SSE support.
- **Nginx/proxy buffering** can interfere — must set `proxy_buffering off` and `proxy_cache off` for SSE endpoints.
- **Keep-alive comments** (`: ping\n\n`) should be sent periodically (every 15s) to prevent intermediate proxies from dropping idle connections.
- **Graceful shutdown** — FastAPI handles this well; the async generator stops cleanly.

**Verdict:** FastAPI's SSE support is robust for production use. `EventSourceResponse` is the preferred approach.

---

## 3. Browser Compatibility

SSE is supported across all modern browsers:

| Browser | Version Support |
|---------|----------------|
| Chrome | All versions (since 2010) |
| Firefox | All versions (since 2012) |
| Safari | All versions (since 2013) |
| Edge | All versions (Chromium-based) |
| Mobile Safari | iOS 6+ |
| Android Chrome | All versions |

MDN confirms SSE is a "widely available baseline feature" supported across all modern browsers since January 2020 (when Safari fully caught up).

**Caveat:** IE11 does not support SSE. If IE11 support is required, a WebSocket fallback is needed. For a modern AI-native portal targeting recruiters, IE11 support is unlikely to be a requirement.

**Verdict:** Browser compatibility is excellent for all modern use cases.

---

## 4. Reliability: Auto-Reconnect vs Manual Reconnection

### SSE Auto-Reconnect

The SSE specification includes built-in auto-reconnect:

- When the connection drops, the browser **automatically retries**.
- The server can control retry delay via the `retry:` field (milliseconds).
- Browsers may apply exponential backoff after repeated failures.
- The `id:` field enables at-least-once delivery — the browser sends `Last-Event-ID` on reconnect so the server can replay missed events.
- The standard states: "Once the user agent has failed the connection, it does not attempt to reconnect." (This is the terminal failure case after many retries.)

### WebSocket Reconnection

WebSocket requires **manual reconnection logic**:
- Application code must detect disconnection (`onerror`, `onclose`).
- Application code must implement retry logic, backoff, and event replay.
- No built-in message ordering or at-least-once delivery.

### Comparison

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| Auto-reconnect | Built-in | Manual |
| Message replay | `id:` + `Last-Event-ID` header | Application-level |
| Connection state | Managed by browser | Application-level |
| Error handling | `onerror` event | `onerror` + `onclose` |
| Terminal failure | After many retries | Application must handle |

**Verdict:** SSE has a significant reliability advantage. The built-in auto-reconnect with `Last-Event-ID` replay is a protocol-level feature that WebSocket lacks entirely. This matters for a recruiter portal where missing an alert (e.g., "new candidate matched") is a real business cost.

---

## 5. Scaling: SSE vs WebSocket Under Load (100+ Concurrent Recruiters)

### HTTP/1.1 Connection Limits

This is SSE's biggest scaling concern:

- **HTTP/1.1:** Browsers enforce a hard limit of **6 open connections per domain**. Each SSE connection counts as one. With 100+ recruiters, each recruiter would need a single SSE connection, so 6 connections per recruiter is not an issue — each recruiter uses 1 SSE connection.
- **HTTP/2:** Eliminates this concern entirely. HTTP/2 multiplexes streams over a single TCP connection. Default max streams is 100 per connection. SSE runs over HTTP/2 without connection limit issues.

### Resource Usage

| Metric | SSE (HTTP/1.1) | SSE (HTTP/2) | WebSocket |
|--------|----------------|--------------|-----------|
| Connections per client | 1 | 1 (multiplexed) | 1 |
| TCP overhead | Higher (persistent) | Lower (shared) | Lower (persistent) |
| Server memory per conn | ~5-10 KB | ~5-10 KB | ~10-20 KB |
| Proxy compatibility | Good (with config) | Excellent | Good |
| Load balancer support | Standard HTTP | Standard HTTP | Requires sticky sessions |

### At 100+ Concurrent Recruiters

- **100 SSE connections** is trivial for any modern server. Nginx handles 10K+ concurrent connections easily.
- **Gunicorn/Uvicorn:** With async workers, 100 SSE connections consume minimal resources. A single Uvicorn worker can handle thousands of SSE connections.
- **Nginx proxy:** Must configure `proxy_buffering off` and `proxy_read_timeout` appropriately. This is well-documented and straightforward.
- **Load balancer:** SSE works with standard HTTP load balancers. No sticky sessions needed (unlike WebSocket, which often requires connection affinity).

### Scaling Verdict

At 100+ concurrent recruiters, SSE scales comfortably. The connection count is linear with user count (1 SSE connection per user), and each connection is lightweight. HTTP/2 eliminates any browser connection limit concerns.

---

## Final Recommendation: CONFIRM the PRD's Choice of SSE

**The PRD is correct to choose SSE.** Here is the summary:

### Why SSE is the Right Choice

1. **Architecture match:** Server-push alerts + HTTP POST chat = SSE + REST. No need for full-duplex.
2. **Built-in reliability:** Auto-reconnect with `Last-Event-ID` replay is a protocol-level feature that reduces application complexity and prevents missed alerts.
3. **FastAPI support:** `EventSourceResponse` is production-ready and well-integrated.
4. **Browser compatibility:** Universal support across all modern browsers.
5. **Scaling:** 100+ concurrent SSE connections is trivial. HTTP/2 eliminates browser connection limits.
6. **Infrastructure simplicity:** Works with standard HTTP load balancers. No sticky sessions needed.

### Trade-offs to Acknowledge

- **No client-to-server on the same connection:** Chat must use HTTP POST (which is already the plan). This is not a drawback for this use case.
- **HTTP/1.1 connection limits:** Only matters if a single client opens many SSE connections simultaneously. Not an issue for 1 connection per recruiter.
- **Proxy configuration:** Nginx requires `proxy_buffering off` for SSE endpoints. This is a one-time configuration, not a scaling concern.
- **No binary support:** SSE only sends text. Not relevant for alert/chat use case.

### When to Reconsider WebSocket

Only if future requirements include:
- Real-time bidirectional streaming on a single connection.
- Live typing indicators or concurrent multi-stream communication.
- Game-like real-time interaction patterns.

None of these are in scope for the recruiter portal.

---

## Sources

- MDN: Server-Sent Events — Using Server-Sent Events
- WHATWG HTML Spec: Server-Sent Events specification
- FastAPI documentation: SSE/StreamingResponse reference
- Browser compatibility data from MDN compatibility tables
