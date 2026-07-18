from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data.db"
UPLOAD_DIR = BASE_DIR / "uploads"
DIARY_DIR = UPLOAD_DIR / "diary"
GALLERY_DIR = UPLOAD_DIR / "gallery"

DIARY_DIR.mkdir(parents=True, exist_ok=True)
GALLERY_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="my-footprints-api")

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


class MessageIn(BaseModel):
    nickname: str
    content: str


class DiaryIn(BaseModel):
    year: int
    month: int
    day: int
    content: str
    image_url: str = ""


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
    # 避免文件名重复奇怪字符，简单处理
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    save_path = DIARY_DIR / safe_name

    content = await file.read()
    save_path.write_bytes(content)

    return {"url": f"/uploads/diary/{safe_name}"}


@app.delete("/api/diary/image")
def delete_diary_image(url: str, year: int, month: int, day: int):
    # url 形如 /uploads/diary/xxx.jpg
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