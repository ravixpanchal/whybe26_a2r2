# Phase 10: OpenRouter Integration

OpenRouter is used only to translate an already-computed assessment into
plain-language educational text. It cannot change the probability, category,
class mapping, feature contributions, or reliability level.

## Configuration

Set these backend environment variables:

```text
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TIMEOUT_SECONDS=8
```

The API key must remain in the backend environment. It is not sent to the
frontend, included in response bodies, or copied into the prompt.

## Safety behavior

`POST /api/assessment/explanation` sends only structured prediction data,
top feature contributions, and reliability reasons. It does not send the raw
borrower request. The service uses a strict timeout and retries one transient
HTTP/network failure with a short backoff.

The response is accepted only when it:

- mentions the model's existing risk category;
- does not mention a contradictory risk category;
- does not claim approval, rejection, certainty, a new prediction, or a
  guaranteed outcome.

Otherwise a deterministic fallback explanation is returned. The fallback is
also used when no API key is configured or OpenRouter is unavailable.
