# CI/CD

| Workflow                | Trigger                      | Runner        | Output                 |
|-------------------------|------------------------------|---------------|------------------------|
| `build-corpus.yml`      | `workflows/**` push, manual  | ubuntu-latest | corpus artifact        |
| `build-gdpr-corpus.yml` | `workflows/**` push, manual  | ubuntu-latest | gdpr-corpus artifact   |
| `deploy-r2.yml`         | manual                       | self-hosted   | R2 bucket upload       |
| `deploy-worker.yml`     | `worker/**` push, manual     | self-hosted   | Cloudflare Worker      |
| `deploy-playground.yml` | `playground/**` push, manual | self-hosted   | Cloudflare Container   |
| `release-corpus.yml`    | manual (version input)       | ubuntu-latest | GitHub Release v-x.y.z |
| `auto-close-pr.yml`     | pull_request_target (opened) | ubuntu-latest | Close unauthorized PRs |