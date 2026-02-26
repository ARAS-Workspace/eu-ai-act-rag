# Privacy Notice — EU AI Act RAG Playground

**Last Updated:** February 2026

## Overview

EU AI Act RAG Playground is an open-source, experimental retrieval-augmented generation system for querying the EU Artificial Intelligence Act (Regulation 2024/1689). This notice explains what data is processed, how it flows through the system, and which third-party services are involved.

The entire source code, infrastructure configuration, and CI/CD pipelines are publicly available in this repository. Production deployments are triggered directly from the repository via GitHub Actions workflows.

## Architecture

The system consists of the following Cloudflare services:

| Service                            | Purpose                                                                        |
|------------------------------------|--------------------------------------------------------------------------------|
| **Cloudflare Workers**             | API backend — handles chat requests, rate limiting, and Turnstile verification |
| **Cloudflare Containers**          | Hosts the Streamlit playground UI                                              |
| **Cloudflare AI Search (AutoRAG)** | Vector search and LLM response generation over the EU AI Act corpus            |
| **Cloudflare Workers AI**          | Embedding, reranking, query rewriting, and text generation models              |
| **Cloudflare KV**                  | Temporary storage for rate limiting counters (auto-expires via TTL)            |
| **Cloudflare R2**                  | Object storage for the EU AI Act corpus documents                              |
| **Cloudflare Turnstile**           | Invisible bot protection (Invisible mode)                                      |

## What Data Is Processed?

### Data You Provide

| Data                    | Purpose                                               | Where It Goes                                              |
|-------------------------|-------------------------------------------------------|------------------------------------------------------------|
| **Chat messages**       | Sent to Cloudflare Workers AI for response generation | Processed in-memory by the Worker, not stored persistently |
| **Language preference** | Determines response language (English or Turkish)     | Sent as part of the API request                            |
| **Search options**      | Model selection, result count, score threshold        | Sent as part of the API request                            |

### Data Processed Automatically

| Data                           | Purpose                                                          | Retention                                                                           |
|--------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **IP address (rate limiting)** | Enforces per-IP rate limits (5/min, 30/hr, 100/day)              | Stored in Cloudflare KV with TTL — auto-deleted after expiry (60s / 3600s / 86400s) |
| **IP address (Turnstile)**     | Sent to Cloudflare Turnstile siteverify API for bot verification | Used only for verification, not stored by the Worker                                |
| **Turnstile token**            | Browser-generated challenge token for bot protection             | Validated server-side, discarded after verification                                 |

## What This System Does NOT Do

- **No persistent storage of conversations.** Chat messages are processed in-memory and not written to any database or log.
- **No user accounts or authentication.** The playground is publicly accessible without registration.
- **No analytics or telemetry.** Streamlit's built-in usage statistics are explicitly disabled (`gatherUsageStats = false`).
- **No tracking cookies or fingerprinting.** No third-party tracking scripts are loaded.
- **No IP address logging.** IP addresses are used only for rate limiting (temporary, auto-expiring) and Turnstile verification (transient).
- **No data sharing.** Your data is not shared with any party beyond the Cloudflare services listed above.

## Cloudflare Turnstile

The playground uses Cloudflare Turnstile in invisible mode for bot protection. Turnstile:

- Runs silently in the background without requiring user interaction in most cases
- Generates a challenge token verified server-side against Cloudflare's siteverify API
- Sends the client IP address to Cloudflare as part of verification
- Does not set tracking cookies — uses only functional cookies required for the challenge

For more information: [Cloudflare Turnstile Privacy](https://www.cloudflare.com/privacypolicy/)

## Rate Limiting

Rate limits are enforced per IP address using Cloudflare KV with automatic expiration:

| Window | Limit | TTL           |
|--------|-------|---------------|
| Minute | 5     | 60 seconds    |
| Hour   | 30    | 3600 seconds  |
| Day    | 100   | 86400 seconds |

Rate limiting counters are the **only** data stored by the Worker. They expire automatically and cannot be used to identify individuals.

## Open Source and Transparency

This is a fully open-source project. The entire codebase — including the Worker API, Streamlit playground, corpus builder pipeline, and all CI/CD workflows — is publicly available and auditable in this repository.

- **Every code change is traceable.** All updates are committed to the public repository.
- **No hidden deployments.** Production is built and deployed from the same source code you can inspect on GitHub.
- **Auditable pipelines.** Workflow configurations, Dockerfiles, and deployment scripts are part of the public repository.

## Third-Party Services

| Provider   | Service                                            | Data Processed                                                  | Privacy Policy                                                            |
|------------|----------------------------------------------------|-----------------------------------------------------------------|---------------------------------------------------------------------------|
| Cloudflare | Workers, Containers, AI Search, Workers AI, KV, R2 | Chat messages (in-memory), IP (rate limiting), Turnstile tokens | [cloudflare.com/privacypolicy](https://www.cloudflare.com/privacypolicy/) |
| Cloudflare | Turnstile                                          | IP address, browser challenge data                              | [cloudflare.com/privacypolicy](https://www.cloudflare.com/privacypolicy/) |

## Changes to This Notice

This privacy notice may be updated as the project evolves. Changes are reflected in this file with an updated date. Since the project is open-source, you can review the full history of changes via Git.

## Contact

For questions about this privacy notice or the EU AI Act RAG Playground:

**Rıza Emre ARAS** — [r.emrearas@proton.me](mailto:r.emrearas@proton.me)

**Artek İnovasyon Arge Sanayi ve Ticaret Ltd. Şti.** — [info@artek.tc](mailto:info@artek.tc)
