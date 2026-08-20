# 3d-reconstruction

Modular internship project. Built piece by piece so each module can change later.

| # | Module | Status |
|---|--------|--------|
| 1 | **UI** (`ui/`) | Live — video upload + processing UI |
| 2 | **API** (`api/`) | Live — jobs + Hello World result |
| 3 | **Database** (`database/`) | Placeholder (jobs are in memory) |
| 4 | **Queuing** (`queueing/`) | Placeholder (background thread stub) |
| 5 | **Model + CLI** (`model/`) | Placeholder (returns Hello World) |

## Branches

| Branch | Contents |
|--------|----------|
| `feature/01-ui-api-hello` | Text Hello World |
| `feature/02-video-upload` | Video upload flow (this branch) |
| `main` | Final merge target |

## Current flow

1. User uploads a video (**&lt; 200 MB**)
2. UI shows **Video is processing** with progress
3. API returns **Hello World** (real 3D comes when Model is wired)

## Run (VS Code: two terminals)

```bash
cd ~/3d-reconstruction
source .venv/bin/activate
pip install -r requirements.txt

# terminal 1
uvicorn api.main:app --host 127.0.0.1 --port 8000

# terminal 2
streamlit run ui/app.py
```

- UI: http://localhost:8501
- API docs: http://127.0.0.1:8000/docs

## API

```http
GET  /health
POST /v1/jobs              # multipart field: video
GET  /v1/jobs/{job_id}     # status + result
```
