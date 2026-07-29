# Question: Is SSE the right real-time transport?

The PRD chose Server-Sent Events (SSE) over WebSockets for real-time updates. Key considerations:

- **SSE:** Simpler implementation, server→client only (no client→server push needed), native FastAPI support, auto-reconnect
- **WebSocket:** Full duplex, better for bidirectional communication, more complex

Questions to investigate:
1. SSE vs WebSocket for our use case — we need server→client push (proactive alerts) and client→server (chat messages). Chat messages use HTTP POST, so SSE handles the push direction.
2. FastAPI SSE support — how robust is it? StreamingResponse?
3. Browser compatibility — SSE works in all modern browsers
4. Reliability — SSE auto-reconnect, WebSocket requires manual reconnection logic
5. Scaling — SSE connections vs WebSocket connections under load (100+ concurrent recruiters)

Resolve by comparing SSE and WebSocket for our specific needs (alerts + chat), considering the existing FastAPI stack.
