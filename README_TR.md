# EU AI Act RAG

## Pipeline

```mermaid
flowchart TD
    CLI["run.py --workflow workflows/eu-ai-act.yaml"]
    CONFIG["src/config.py<br/>load_config → PipelineConfig"]
    PIPELINE["src/pipeline.py<br/>run_pipeline"]

    CLI -->|"YAML parse"| CONFIG
    CONFIG -->|"PipelineConfig"| PIPELINE

    subgraph PHASE_1 ["Phase 1 — SPARQL"]
        S_LOOP["For each step in<br/>config.sparql.steps"]
        S_RENDER["src/sparql/queries.py<br/>render_step"]
        S_QUERY["src/sparql/client.py<br/>execute_query"]
        S_SCRIPT["src/sparql/processor.py<br/>execute_script"]
        S_CTX["context[step.name] = output"]

        S_LOOP --> S_RENDER
        S_RENDER -->|"SPARQL query string"| S_QUERY
        S_QUERY -->|"list&lt;Binding&gt;"| S_SCRIPT
        S_SCRIPT -->|"output"| S_CTX
        S_CTX -->|"next step"| S_LOOP
    end

    subgraph PHASE_2 ["Phase 2 — Fetch"]
        F_URI["select_uri<br/>uri_select_script from YAML"]
        F_DL["_download<br/>GET + Accept: application/zip"]
        F_ZIP["_extract_zip<br/>ZIP → *.fmx.xml to tmpdir"]

        F_URI -->|"manifestation URL"| F_DL
        F_DL -->|"bytes"| F_ZIP
    end

    subgraph PHASE_3 ["Phase 3 — Parse"]
        P_ACT["*.000101.fmx.xml<br/>Main ACT file"]
        P_ART["parse_articles<br/>DIVISION → ARTICLE → PARAG"]
        P_REC["parse_recitals<br/>PREAMBLE → CONSID → NP"]
        P_ANX["parse_annex<br/>*.01XXXX.fmx.xml × 13"]
        P_DOC["ParsedDocument<br/>articles + recitals + annexes"]

        P_ACT --> P_ART
        P_ACT --> P_REC
        P_ANX --> P_DOC
        P_ART --> P_DOC
        P_REC --> P_DOC
    end

    subgraph PHASE_4 ["Phase 4 — Convert + Postprocess"]
        C_FM["_build_frontmatter<br/>YAML frontmatter from templates"]
        C_BODY["_article_to_markdown<br/>Structured body text"]
        C_NORM["_normalize<br/>NBSP, ZWSP, BOM cleanup"]
        C_WRITE["write_text<br/>corpus/**/*.md"]

        C_FM --> C_NORM
        C_BODY --> C_NORM
        C_NORM --> C_WRITE
    end

    PIPELINE --> PHASE_1
    PHASE_1 -->|"context dict"| PHASE_2
    PHASE_2 -->|"tmpdir: Path"| PHASE_3
    PHASE_3 -->|"ParsedDocument"| PHASE_4

    PHASE_4 -->|"PipelineSummary"| SUMMARY["Pipeline Summary<br/>sparql: 4 ok | fetch: 1 ok<br/>articles: 113 | recitals: 180 | annexes: 13"]

    style PHASE_1 fill:#1a1a2e,stroke:#e94560,color:#fff
    style PHASE_2 fill:#1a1a2e,stroke:#0f3460,color:#fff
    style PHASE_3 fill:#1a1a2e,stroke:#16213e,color:#fff
    style PHASE_4 fill:#1a1a2e,stroke:#1a8a42,color:#fff
```

## Hızlı Başlangıç

```bash
pip install -r workflow-engine/requirements.txt
python run.py --workflow workflows/eu-ai-act.yaml
```

## Çıktı

| Bölüm    | Adet | Dizin                  |
|----------|------|------------------------|
| Maddeler | 113  | `corpus/articles/*.md` |
| Gerekçe  | 180  | `corpus/recitals/*.md` |
| Ekler    | 13   | `corpus/annexes/*.md`  |

## RAG Yapılandırması

| Parametre        | Değer                                      |
|------------------|--------------------------------------------|
| Embedding Model  | `@cf/qwen/qwen3-embedding-0.6b`            |
| Generation Model | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| Chunk Boyutu     | 512 token                                  |
| Chunk Örtüşme    | %10                                        |
| Vektör Deposu    | Cloudflare Vectorize (1024 boyut)          |
| Nesne Deposu     | Cloudflare R2                              |

### Cloudflare Belgeleri

- [AI Search](https://developers.cloudflare.com/ai-search/)
- [Vectorize](https://developers.cloudflare.com/vectorize/)
- [R2 Object Storage](https://developers.cloudflare.com/r2/)

## Proje Yapısı

```
eu-ai-act-rag/
├── run.py                          # Giriş noktası
├── workflows/
│   └── eu-ai-act.yaml             # Workflow tanımı
├── workflow-engine/
│   ├── requirements.in
│   ├── requirements.txt
│   └── src/
│       ├── config.py
│       ├── converter.py
│       ├── fetcher.py
│       ├── logger.py
│       ├── parser.py
│       ├── pipeline.py
│       ├── result.py
│       └── sparql/
│           ├── client.py
│           ├── processor.py
│           └── queries.py
├── worker/                         # Cloudflare Worker (AutoRAG API)
│   ├── wrangler.jsonc
│   ├── package.json
│   └── src/
│       ├── index.ts
│       ├── config.ts
│       ├── types.ts
│       ├── translations.ts
│       ├── ai/
│       │   ├── manager.ts
│       │   └── prompts/
│       │       └── system-prompt.md
│       ├── middleware/
│       │   └── ratelimit.ts
│       ├── validation/
│       │   ├── request.ts
│       │   └── schema.ts
│       └── utils/
│           ├── errors.ts
│           └── logging.ts
├── playground/                     # Streamlit - Cloudflare Containers
│   ├── wrangler.jsonc
│   ├── package.json
│   ├── Dockerfile
│   ├── start.sh
│   ├── src/
│   │   └── index.ts               # Hono reverse proxy
│   └── app/
│       ├── app.py
│       ├── translations.py
│       ├── export_utils.py
│       ├── locales/
│       │   ├── en.json
│       │   └── tr.json
│       └── .streamlit/
│           └── config.toml
└── dist/                           # Çıktı (gitignore)
```

## CI/CD

```mermaid
flowchart TD
    subgraph BUILD ["build-corpus.yml — Build Corpus"]
        direction TB
        B_TRIGGER["push main / pull_request / workflow_call"]
        B_CHECKOUT["actions/checkout@v4"]
        B_PYTHON["actions/setup-python@v5<br/>Python 3.12"]
        B_DEPS["pip install --require-hashes"]
        B_RUN["python run.py<br/>--workflow workflows/eu-ai-act.yaml"]
        B_ARTIFACT["actions/upload-artifact@v4<br/>name: corpus"]

        B_TRIGGER --> B_CHECKOUT --> B_PYTHON --> B_DEPS --> B_RUN --> B_ARTIFACT
    end

    subgraph DEPLOY_R2 ["deploy-r2.yml — Deploy Corpus R2"]
        direction TB
        D_TRIGGER["workflow_dispatch"]
        D_DOWNLOAD["actions/download-artifact@v4"]
        D_CLEAR["rclone delete r2:eu-ai-act-rag"]
        D_UPLOAD["rclone copy corpus/ r2:eu-ai-act-rag"]

        D_TRIGGER --> D_DOWNLOAD --> D_CLEAR --> D_UPLOAD
    end

    subgraph RELEASE ["release-corpus.yml — Release Corpus"]
        direction TB
        R_TRIGGER["workflow_dispatch<br/>input: version"]
        R_DOWNLOAD["actions/download-artifact@v4"]
        R_TAR["tar -czf corpus.tar.gz"]
        R_GH["softprops/action-gh-release@v2<br/>tag: v-{version}"]

        R_TRIGGER --> R_DOWNLOAD --> R_TAR --> R_GH
    end

    subgraph DEPLOY_WORKER ["deploy-worker.yml — Deploy Worker"]
        direction TB
        W_TRIGGER["workflow_dispatch"]
        W_CHECKOUT["actions/checkout@v4"]
        W_NODE["actions/setup-node@v4<br/>Node.js 22"]
        W_ENV["Create .env<br/>CLOUDFLARE_API_TOKEN<br/>CLOUDFLARE_ACCOUNT_ID"]
        W_INSTALL["npm install"]
        W_TYPEGEN["npm run cf-typegen"]
        W_DEPLOY["npm run deploy"]

        W_TRIGGER --> W_CHECKOUT --> W_NODE --> W_ENV --> W_INSTALL --> W_TYPEGEN --> W_DEPLOY
    end

    subgraph DEPLOY_PLAYGROUND ["deploy-playground.yml — Deploy Playground"]
        direction TB
        P_TRIGGER["workflow_dispatch"]
        P_CHECKOUT["actions/checkout@v4"]
        P_NODE["actions/setup-node@v4<br/>Node.js 22"]
        P_DOCKER["docker/setup-buildx-action@v3<br/>linux/amd64"]
        P_ENV["Create .env<br/>CLOUDFLARE_API_TOKEN<br/>CLOUDFLARE_ACCOUNT_ID"]
        P_INSTALL["npm install"]
        P_TYPEGEN["npm run cf-typegen"]
        P_DEPLOY["npm run deploy"]

        P_TRIGGER --> P_CHECKOUT --> P_NODE --> P_DOCKER --> P_ENV --> P_INSTALL --> P_TYPEGEN --> P_DEPLOY
    end

    BUILD -->|"corpus artifact"| DEPLOY_R2
    BUILD -->|"corpus artifact"| RELEASE

    style BUILD fill:#1a1a2e,stroke:#e94560,color:#fff
    style DEPLOY_R2 fill:#1a1a2e,stroke:#0f3460,color:#fff
    style RELEASE fill:#1a1a2e,stroke:#1a8a42,color:#fff
    style DEPLOY_WORKER fill:#1a1a2e,stroke:#f5a623,color:#fff
    style DEPLOY_PLAYGROUND fill:#1a1a2e,stroke:#7b68ee,color:#fff
```

| Workflow                 | Tetikleyici                | Runner        | Çıktı                  |
|--------------------------|----------------------------|---------------|------------------------|
| `build-corpus.yml`       | push, pull_request, manual | ubuntu-latest | corpus artifact        |
| `deploy-r2.yml`          | manual                     | self-hosted   | R2 bucket yüklemesi    |
| `deploy-worker.yml`      | manual                     | self-hosted   | Cloudflare Worker      |
| `deploy-playground.yml`  | manual                     | self-hosted   | Cloudflare Container   |
| `release-corpus.yml`     | manual (version input)     | ubuntu-latest | GitHub Release v-x.y.z |

## Lisans

MIT Lisansı — Telif Hakkı (C) 2026 Rıza Emre ARAS

Ayrıntılar için [LICENSE](LICENSE) ve [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) dosyalarına bakınız.
