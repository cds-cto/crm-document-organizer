# CRM Document Organizer

A batch job that classifies and organizes **unmapped documents** in SSICRM.

For each unmapped document, the job downloads the file, sends it to the
[CDS Zone 2](https://cdszone2.com) organizer service for classification, and writes the
resulting title, category, profile, and liability back into SSICRM. Documents that fail
anywhere in the pipeline are returned to the unmapped queue so they can be retried on a
later run.

The job processes every unmapped document it finds and then exits — it is designed to be
run on a schedule (e.g. a cron job or a Cloud Run / Kubernetes scheduled task), not as a
long-running service.

## How it works

```
SSICRM                          CDS Zone 2                     SSICRM
  │                                 │                             │
  ├─ search unmapped documents      │                             │
  │                                 │                             │
  └─ for each document:             │                             │
        ├─ mark as "pending" ───────┼──────────────────────────► │
        ├─ get preview/download URL │                             │
        ├─ download file            │                             │
        ├─ POST file ───────────────► classify (title, category,  │
        │                              profileId, liabilityId)     │
        ├─ save classification ──────┼──────────────────────────► │
        └─ on failure: clear pending ┼──────────────────────────► │ (back to queue)
```

Pipeline steps (`DocumentProcessingFlow.process_all_unmapped`):

1. **Search** – `POST /UnMappedDocument/search` returns up to 300 documents with `status = 0`.
2. **Mark pending** – each document is set to `status = 1` (pending) before processing so it
   is not picked up by a concurrent run.
3. **Preview** – `POST /UnMappedDocument/{id}/preview` returns a temporary download URL.
4. **Download** – the file is streamed into memory; filename and MIME type are derived from
   the response headers (falling back to the URL path / `mimetypes`).
5. **Classify** – the file is posted as multipart `file` to the CDS organizer endpoint with
   HTTP Basic Auth. CDS returns `status`, `title`, `category_uuid`, `ProfileId`, and
   `LiabilityId`.
6. **Save** – when CDS returns HTTP 200, the normalized fields are written back via
   `PUT /UnMappedDocument/{id}`.
7. **Recover** – if CDS fails or the save fails, the document's pending flag is cleared so it
   returns to the unmapped queue for a future run.

A short configurable sleep (`PER_DOC_SLEEP_SECS`, default `0.8s`) is applied between
documents to avoid hammering the upstream services.

## Project structure

```
crm-document-organizer/
├── src/
│   ├── main.py                              # Entry point: login + process all unmapped
│   ├── config/
│   │   └── config.ini                       # Local config (gitignored)
│   └── services/
│       ├── __init__.py                      # Re-exports the public service classes
│       ├── crm_service.py                   # SSICRMService – SSICRM REST client
│       ├── cdszone_services.py              # CDSZone2Service – CDS organizer client
│       ├── crm_organizer_scheduler.py       # DocumentProcessingFlow – orchestration
│       └── config_loader_services.py        # ConfigLoader – config.ini + env resolution
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Configuration

Configuration is resolved by `ConfigLoader` in this order:

1. A matching `[section] key` in `config.ini`
2. The named environment variable
3. A built-in default

`config.ini` is searched for (in order) at the path in `CONFIG_INI_PATH`, then
`src/config.ini`, `src/config/config.ini`, `src/services/config.ini`, and
`src/services/config/config.ini`. The actual file used is `src/config/config.ini`, which is
**gitignored** — create it locally and never commit credentials.

### `config.ini` example

```ini
[ssicrm]
base_url = https://ssiapi.com/api
username = your-ssicrm-user
password = your-ssicrm-password

[cdszone2]
base_url = https://api.cdszone2.com/api/organizer/process
username = your-cds-user
password = your-cds-password
```

### Settings reference

| Setting    | `config.ini`            | Environment variable | Default                                              |
| ---------- | ----------------------- | -------------------- | ---------------------------------------------------- |
| SSICRM URL | `[ssicrm] base_url`     | `SSICRM_MAIN_URL`    | `https://ssiapi.com/api`                             |
| SSICRM user| `[ssicrm] username`     | `SSICRM_USER`        | _(empty)_                                            |
| SSICRM pass| `[ssicrm] password`     | `SSICRM_PASS`        | _(empty)_                                            |
| CDS URL    | `[cdszone2] base_url`   | `CDS_URL`            | `https://api.cdszone2.com/api/organizer/process`     |
| CDS user   | `[cdszone2] username`   | `CDS_USER`           | _(empty)_                                            |
| CDS pass   | `[cdszone2] password`   | `CDS_PASS`           | _(empty)_                                            |
| Config path| —                       | `CONFIG_INI_PATH`    | _(auto-discovered)_                                  |
| Per-doc delay | —                    | `PER_DOC_SLEEP_SECS` | `0.8` (seconds)                                      |

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.12
- [pip](https://pip.pypa.io/en/stable/installation/)
- Network access to SSICRM and CDS Zone 2, plus valid credentials for both
- (Optional) [Docker](https://docs.docker.com/get-docker/) for containerized runs

## Running locally

```bash
# 1. Install dependencies (use a virtual environment)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt

# 2. Provide configuration
#    Create src/config/config.ini (see example above) OR export the env vars:
#    SSICRM_USER, SSICRM_PASS, CDS_USER, CDS_PASS

# 3. Run the job
python src/main.py
```

The job prints a per-document progress log and finally a JSON summary of every processed
document (preview URL, filename, CDS HTTP status, CDS payload, and save result).

## Running with Docker

```bash
# Build and run; the container exits when the run completes
docker-compose up --build
```

The image is built for `linux/amd64` on `python:3.12.7` and runs `python ./src/main.py`.
Port `5679` is exposed for remote debugging via `debugpy` (see below).

## Deployment

The image is published to Google Artifact Registry:

```bash
docker build -t crm-document-organizer .
docker tag crm-document-organizer us-west2-docker.pkg.dev/polling-apps/core/crm-document-organizer:latest
docker push us-west2-docker.pkg.dev/polling-apps/core/crm-document-organizer:latest
```

Run the pushed image on a scheduler (e.g. Cloud Run Jobs / Kubernetes CronJob) with the
SSICRM and CDS credentials supplied as environment variables.

## Remote debugging

`debugpy` is bundled and the container exposes port `5679`. To debug:

1. Uncomment the `debugpy.listen(...)` / `wait_for_client()` lines in `src/main.py`.
2. Start the container (`docker-compose up --build`).
3. Attach using the **"Python: Remote Attach"** configuration in `.vscode/launch.json`.
