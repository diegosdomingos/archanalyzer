import httpx
from fastapi import APIRouter, File, UploadFile, HTTPException

from app.core.config import UPLOAD_SERVICE_URL, REPORT_SERVICE_URL

router = APIRouter()


@router.post("/upload")
async def upload_diagram(file: UploadFile = File(...)):
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(f"{UPLOAD_SERVICE_URL}/upload", files=files)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upload service error: {str(e)}")


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(f"{UPLOAD_SERVICE_URL}/status/{job_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upload service error: {str(e)}")


@router.get("/report/{job_id}")
async def get_report(job_id: str):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(f"{REPORT_SERVICE_URL}/report/{job_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Report service error: {str(e)}")