import os
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists and mount it as static to serve uploaded images
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

@app.post("/barang")
async def create_barang(
    nama: str = Form(...),
    harga: float = Form(...),
    deskripsi: str = Form(...),
    kondisi: str = Form(...),  # 'baru' | 'bekas'
    kategori: str = Form(...),  # 'elektronik' | 'fashion' | 'makanan' | 'lainnya'
    gambar: UploadFile = File(...)
):
    # Basic validations
    if kondisi not in {"baru", "bekas"}:
        raise HTTPException(status_code=400, detail="Kondisi tidak valid")
    if kategori not in {"elektronik", "fashion", "makanan", "lainnya"}:
        raise HTTPException(status_code=400, detail="Kategori tidak valid")
    if harga < 0:
        raise HTTPException(status_code=400, detail="Harga tidak boleh negatif")

    # Validate file type and size (limit ~2MB by reading bytes length)
    allowed_mime = {"image/jpeg", "image/png", "image/gif"}
    if gambar.content_type not in allowed_mime:
        raise HTTPException(status_code=400, detail="Tipe file tidak valid. Hanya JPG/PNG/GIF")

    file_bytes = await gambar.read()
    if len(file_bytes) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 2MB")

    # Determine file extension safely
    ext = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif"
    }.get(gambar.content_type, "img")

    filename = f"img_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    image_url = f"/uploads/{filename}"

    return JSONResponse({
        "message": "Berhasil menyimpan barang",
        "data": {
            "nama": nama,
            "harga": harga,
            "deskripsi": deskripsi,
            "kondisi": kondisi,
            "kategori": kategori,
            "gambar_url": image_url
        }
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
