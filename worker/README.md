# EU AI Act RAG Worker — API Reference

## Endpoint

```
POST /api/v1/chat/completions
```

## Request

### Headers

| Header              | Required | Description                                                                 |
|---------------------|----------|-----------------------------------------------------------------------------|
| `Content-Type`      | yes      | Must be `application/json`.                                                 |
| `X-Turnstile-Token` | yes*     | Cloudflare Turnstile verification token. *Skipped in development mode.      |

### Body

```json
{
  "messages": [
    { "role": "user", "content": "What are the risk categories defined in the EU AI Act?" },
    { "role": "assistant", "content": "The EU AI Act defines four risk categories: unacceptable, high, limited, and minimal risk." },
    { "role": "user", "content": "Which AI systems fall under the high-risk category?" }
  ],
  "locale": "en"
}
```

| Field           | Type    | Required | Description                                                                                       |
|-----------------|---------|----------|---------------------------------------------------------------------------------------------------|
| `messages`      | array   | yes      | Conversation history. Each message has `role` (`"user"` or `"assistant"`) and `content` (string). |
| `locale`        | string  | no       | Response language: `"en"` (default) or `"tr"`.                                                    |
| `stream`        | boolean | no       | Reserved for future use.                                                                          |
| `searchOptions` | object  | no       | Override default AI Search parameters. See below.                                                 |

### searchOptions

```json
{
  "messages": [
    { "role": "user", "content": "What are the obligations for high-risk AI providers?" }
  ],
  "searchOptions": {
    "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "rewriteQuery": true,
    "reRanking": true,
    "maxResults": 10,
    "scoreThreshold": 0.5
  }
}
```

| Field            | Type    | Default                                    | Description                         |
|------------------|---------|--------------------------------------------|-------------------------------------|
| `model`          | string  | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Generation model.                   |
| `rewriteQuery`   | boolean | `true`                                     | Rewrite query for better retrieval. |
| `reRanking`      | boolean | `true`                                     | Semantic reranking of results.      |
| `maxResults`     | integer | `20`                                       | Max retrieved chunks (1–50).        |
| `scoreThreshold` | number  | `0.4`                                      | Min relevance score (0–1).          |

**Allowed models:**

- `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- `@cf/meta/llama-3.1-8b-instruct`
- `@cf/meta/llama-3.1-70b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@cf/google/gemma-7b-it`
- `@cf/qwen/qwen1.5-7b-chat-awq`

## Response

### 200 OK

```json
{
  "response": "Under the EU AI Act, high-risk AI systems include those used in critical infrastructure (e.g. transport, energy), education and vocational training (e.g. exam scoring), employment and worker management (e.g. CV screening), essential private and public services (e.g. credit scoring), law enforcement, migration and border control, and administration of justice. These systems must comply with strict requirements including risk management, data governance, technical documentation, transparency, human oversight, and robustness before being placed on the EU market.",
  "sources": [
    { "filename": "eu-ai-act-final-text/article-6.md", "score": 0.82, "content": "## Article 6 — Classification rules for high-risk AI systems\n\n1. Irrespective of whether an AI system is placed on the market..." },
    { "filename": "eu-ai-act-final-text/annex-III.md", "score": 0.76, "content": "## Annex III — High-risk AI systems referred to in Article 6(2)\n\n1. Biometrics, insofar as their use is permitted..." },
    { "filename": "eu-ai-act-final-text/article-9.md", "score": 0.61, "content": "## Article 9 — Risk management system\n\n1. A risk management system shall be established, implemented, documented..." }
  ],
  "metadata": {
    "search_query": "high-risk AI systems categories EU AI Act",
    "duration_ms": 1842,
    "timestamp": 1740500000000
  }
}
```

| Field                   | Type   | Description                                                                                       |
|-------------------------|--------|---------------------------------------------------------------------------------------------------|
| `response`              | string | Generation model-produced answer grounded in the retrieved EU AI Act sources.                     |
| `sources`               | array  | Matched document chunks. Each item contains `filename`, `score`, and `content`.                   |
| `sources[].filename`    | string | R2 object key of the matched document.                                                            |
| `sources[].score`       | number | Relevance score (0–1).                                                                            |
| `sources[].content`     | string | Retrieved chunk text used for generation.                                                         |
| `metadata.search_query` | string | The rewritten query used for vector retrieval.                                                    |
| `metadata.duration_ms`  | number | End-to-end processing time in milliseconds.                                                       |
| `metadata.timestamp`    | number | Unix epoch timestamp (ms) when the response was generated.                                        |

### 400 Bad Request

```json
{
  "error": {
    "type": "invalid_request",
    "message": "Validation failed: messages[0].content: Message content must not be empty"
  },
  "status": 400
}
```

### 403 Forbidden

```json
{
  "error": {
    "type": "forbidden",
    "message": "Security verification required"
  },
  "status": 403
}
```

### 429 Too Many Requests

```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please try again later."
  },
  "status": 429,
  "retryAfter": 60
}
```

### 502 Bad Gateway

```json
{
  "error": {
    "type": "bad_gateway",
    "message": "AI service error: upstream timeout"
  },
  "status": 502
}
```

## cURL

```bash
curl -X POST https://<worker-domain>/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Token: <turnstile-token>" \
  -d '{
    "messages": [
      { "role": "user", "content": "What obligations do providers of high-risk AI have?" }
    ],
    "locale": "en"
  }'
```

## Limits

### Validation

| Constraint               | Value      |
|--------------------------|------------|
| Max messages per request | 20         |
| Max message length       | 4096 chars |
| Max request body size    | 20 KB      |

### Rate Limiting (per IP)

| Window  | Limit |
|---------|-------|
| Minute  | 5     |
| Hour    | 30    |
| Day     | 100   |
