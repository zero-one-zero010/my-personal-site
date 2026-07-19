from datetime import datetime, timezone
from pathlib import Path
import json
import os
import sqlite3

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data.db"
UPLOAD_DIR = BASE_DIR / "uploads"
DIARY_DIR = UPLOAD_DIR / "diary"
GALLERY_DIR = UPLOAD_DIR / "gallery"

DIARY_DIR.mkdir(parents=True, exist_ok=True)
GALLERY_DIR.mkdir(parents=True, exist_ok=True)


def load_env_file():
    """Load backend/.env into process env (does not override existing vars)."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

app = FastAPI(title="my-footprints-api")


def get_deepseek_client() -> OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="未配置 DEEPSEEK_API_KEY")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_chat_table():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


ensure_chat_table()


class MessageIn(BaseModel):
    nickname: str
    content: str


class DiaryIn(BaseModel):
    year: int
    month: int
    day: int
    content: str
    image_url: str = ""


class ChatIn(BaseModel):
    content: str


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/footprints")
def list_footprints():
    conn = get_db()
    rows = conn.execute(
        "SELECT name, temp, sunrise, sunset FROM footprints"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/messages")
def list_messages():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, nickname, content, created_at FROM messages ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/messages")
def create_message(body: MessageIn):
    nickname = body.nickname.strip()
    content = body.content.strip()
    if not nickname or not content:
        raise HTTPException(status_code=400, detail="昵称和内容不能为空")

    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO messages (nickname, content, created_at) VALUES (?, ?, ?)",
        (nickname, content, now),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, nickname, content, created_at FROM messages WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/diary")
def list_diary(year: int, month: int):
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, year, month, day, content, image_url, created_at, updated_at
        FROM diary
        WHERE year = ? AND month = ?
        ORDER BY day
        """,
        (year, month),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/diary")
def save_diary(body: DiaryIn):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    existing = conn.execute(
        "SELECT id, image_url FROM diary WHERE year = ? AND month = ? AND day = ?",
        (body.year, body.month, body.day),
    ).fetchone()

    image_url = body.image_url or (existing["image_url"] if existing else "")

    if existing:
        conn.execute(
            """
            UPDATE diary
            SET content = ?, image_url = ?, updated_at = ?
            WHERE id = ?
            """,
            (body.content, image_url, now, existing["id"]),
        )
        diary_id = existing["id"]
    else:
        cur = conn.execute(
            """
            INSERT INTO diary (year, month, day, content, image_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (body.year, body.month, body.day, body.content, image_url, now, now),
        )
        diary_id = cur.lastrowid

    conn.commit()
    row = conn.execute(
        """
        SELECT id, year, month, day, content, image_url, created_at, updated_at
        FROM diary WHERE id = ?
        """,
        (diary_id,),
    ).fetchone()
    conn.close()
    return dict(row)


@app.post("/api/diary/image")
async def upload_diary_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "img.jpg").suffix or ".jpg"
    name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename or 'img'}{suffix}"
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    save_path = DIARY_DIR / safe_name

    content = await file.read()
    save_path.write_bytes(content)

    return {"url": f"/uploads/diary/{safe_name}"}


@app.delete("/api/diary/image")
def delete_diary_image(url: str, year: int, month: int, day: int):
    filename = url.rstrip("/").split("/")[-1]
    file_path = DIARY_DIR / filename
    if file_path.exists():
        file_path.unlink()

    conn = get_db()
    conn.execute(
        """
        UPDATE diary SET image_url = '', updated_at = ?
        WHERE year = ? AND month = ? AND day = ?
        """,
        (datetime.now(timezone.utc).isoformat(), year, month, day),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/gallery")
def list_gallery():
    exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    files = [
        f"/uploads/gallery/{p.name}"
        for p in sorted(GALLERY_DIR.iterdir())
        if p.is_file() and p.suffix.lower() in exts
    ]
    return {"images": files}


@app.get("/api/chat/history")
def chat_history():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, role, content, created_at
        FROM chat_messages
        ORDER BY id ASC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.delete("/api/chat/history")
def clear_chat_history():
    conn = get_db()
    conn.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/chat")
def chat(body: ChatIn):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")

    if not os.getenv("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=500, detail="未配置 DEEPSEEK_API_KEY")

    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()

    history_rows = conn.execute(
        """
        SELECT role, content FROM chat_messages
        ORDER BY id ASC
        """
    ).fetchall()
    history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

    conn.execute(
        "INSERT INTO chat_messages (role, content, created_at) VALUES (?, ?, ?)",
        ("user", content, now),
    )
    conn.commit()
    conn.close()

    context = (history + [{"role": "user", "content": content}])[-40:]
    messages_payload = [
        {
            "role": "system",
            "content": "你是个人站点助手，回答简洁友好，使用中文。",
        },
        *context,
    ]
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def event_stream():
        full_parts = []
        try:
            client = get_deepseek_client()
            stream = client.chat.completions.create(
                model=model,
                messages=messages_payload,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue
                full_parts.append(delta)
                yield f"data: {json.dumps({'type': 'delta', 'content': delta}, ensure_ascii=False)}\n\n"

            reply = "".join(full_parts)
            reply_time = datetime.now(timezone.utc).isoformat()
            db = get_db()
            cur = db.execute(
                "INSERT INTO chat_messages (role, content, created_at) VALUES (?, ?, ?)",
                ("assistant", reply, reply_time),
            )
            db.commit()
            assistant_id = cur.lastrowid
            db.close()

            yield f"data: {json.dumps({'type': 'done', 'id': assistant_id, 'content': reply, 'created_at': reply_time}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
