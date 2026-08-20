# 3d-reconstruction

Internship project: modular pipeline that will eventually turn indoor video into 3D output.

Built **module by module** so each piece can change without rewriting the whole app.

| # | Module | Status |
|---|--------|--------|
| 1 | **UI** (`ui/`) | Phase 1 — text input |
| 2 | **API** (`api/`) | Phase 1 — returns Hello World |
| 3 | **Database** (`database/`) | Placeholder |
| 4 | **Queuing** (`queueing/`) | Placeholder |
| 5 | **Model + CLI** (`model/`) | Placeholder |

## Phase 1

Prove UI ↔ API. User types text; API replies **Hello World**. No video yet.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# terminal 1
uvicorn api.main:app --host 127.0.0.1 --port 8000

# terminal 2
streamlit run ui/app.py
```

- UI: http://localhost:8501  
- API docs: http://127.0.0.1:8000/docs  
