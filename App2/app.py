"""
CCD Welding Quality Control App - FastAPI Version

A FastAPI application for browsing computer vision quality control
inspection images from manufacturing production lines.

Designed to run on Databricks Apps.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import quote

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()

from services.warehouse import Warehouse
from services.lakebase import Lakebase
from databricks.sdk import WorkspaceClient

# Initialize FastAPI app
app = FastAPI(
    title="Quality Control Cockpit",
    description="OP Mobility Manufacturing Intelligence Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Volume path configuration
ALLOWED_PREFIX = "/Volumes/serverless_opm_catalog/opm/quality/images-highres/"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/factories")
async def get_factories():
    """Get list of all factories"""
    try:
        rows = Lakebase.query("SELECT factory_id, region, cameras FROM opm.hellooo")
        factories = []
        for row in rows:
            factory = {
                "factory_id": row.get("factory_id"),
                "region": row.get("region"),
                "cameras": row.get("cameras") or []
            }
            factories.append(factory)
        return {"factories": factories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load factories: {str(e)}")


@app.get("/api/filter-options")
async def get_filter_options():
    """Get all possible filter values (defect types, etc.) for the entire dataset"""
    try:
        # Get all unique defect types from the entire inspections table
        defect_query = """
            SELECT DISTINCT defect_type
            FROM serverless_opm_catalog.opm.inspections
            WHERE defect_type IS NOT NULL
            ORDER BY defect_type
        """
        
        defect_rows = Warehouse.query(defect_query)
        
        # Extract defect types (handle different case variations)
        defect_types = []
        for row in defect_rows:
            value = row.get("defect_type") or row.get("DEFECT_TYPE") or row.get("DefectType")
            if value:
                defect_types.append(value)
        
        return {
            "defect_types": defect_types
        }
    except Exception as e:
        print(f"[ERROR] Failed to load filter options: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Failed to load filter options: {str(e)}")


@app.get("/api/inspections")
async def get_inspections(
    region: Optional[str] = Query(None),
    factory: Optional[str] = Query(None),
    camera: Optional[str] = Query(None),
    prediction: Optional[str] = Query(None),
    defect_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(8, ge=1, le=100)
):
    """
    Get paginated inspection records with filters
    
    Query parameters:
    - region: Filter by region
    - factory: Filter by factory_id
    - camera: Filter by camera_id
    - prediction: Filter by prediction (OK/KO)
    - defect_type: Filter by defect type
    - search: Search in inspection_id
    - date_from: Filter by date from (YYYY-MM-DD)
    - date_to: Filter by date to (YYYY-MM-DD)
    - page: Page number (default 1)
    - per_page: Items per page (default 12, max 100)
    """
    try:
        # Build WHERE clauses
        where_clauses = []
        
        if factory:
            where_clauses.append(f"factory_id = '{factory}'")
        
        if camera:
            where_clauses.append(f"camera_id = '{camera}'")
        
        if prediction:
            where_clauses.append(f"prediction = '{prediction}'")
        
        if defect_type and defect_type != "All":
            where_clauses.append(f"defect_type = '{defect_type}'")
        
        if search:
            where_clauses.append(f"inspection_id LIKE '%{search}%'")
        
        if date_from:
            where_clauses.append(f"date >= '{date_from}'")
        
        if date_to:
            where_clauses.append(f"date <= '{date_to}'")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as count
            FROM serverless_opm_catalog.opm.inspections
            WHERE {where_sql}
        """
        count_result = Warehouse.query(count_query)
        total_count = int(count_result[0].get("count", 0)) if count_result else 0
        
        # Get paginated data
        offset = (page - 1) * per_page
        data_query = f"""
            SELECT 
                inspection_id,
                factory_id,
                camera_id,
                timestamp,
                image_path,
                prediction,
                confidence_score,
                defect_type,
                inference_time_ms,
                model_version,
                date
            FROM serverless_opm_catalog.opm.inspections
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT {per_page} OFFSET {offset}
        """
        
        rows = Warehouse.query(data_query)
        
        # Format inspections
        inspections = []
        for row in rows:
            # Convert timestamp to string
            timestamp = row.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp) if timestamp else ""
            
            # Convert date to string
            date_val = row.get("date")
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val) if date_val else ""
            
            inspection = {
                "inspection_id": row.get("inspection_id"),
                "factory_id": row.get("factory_id"),
                "camera_id": row.get("camera_id"),
                "timestamp": timestamp_str,
                "image_path": row.get("image_path"),
                "prediction": row.get("prediction"),
                "confidence_score": float(row.get("confidence_score", 0)),
                "defect_type": row.get("defect_type"),
                "inference_time_ms": int(row.get("inference_time_ms", 0)),
                "model_version": row.get("model_version"),
                "date": date_str
            }
            inspections.append(inspection)
        
        # Calculate stats
        if region:
            # Filter by region (need to join with factories)
            stats_query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN i.prediction = 'OK' THEN 1 ELSE 0 END) as ok_count,
                    SUM(CASE WHEN i.prediction = 'KO' THEN 1 ELSE 0 END) as ko_count
                FROM serverless_opm_catalog.opm.inspections i
                JOIN serverless_opm_catalog.opm.factories f ON i.factory_id = f.factory_id
                WHERE f.region = '{region}' AND {where_sql}
            """
        else:
            stats_query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN prediction = 'OK' THEN 1 ELSE 0 END) as ok_count,
                    SUM(CASE WHEN prediction = 'KO' THEN 1 ELSE 0 END) as ko_count
                FROM serverless_opm_catalog.opm.inspections
                WHERE {where_sql}
            """
        
        stats_result = Warehouse.query(stats_query)
        stats = stats_result[0] if stats_result else {"total": 0, "ok_count": 0, "ko_count": 0}
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            "inspections": inspections,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages
            },
            "stats": {
                "total": int(stats.get("total", 0)),
                "filtered": total_count,
                "ok_count": int(stats.get("ok_count", 0)),
                "ko_count": int(stats.get("ko_count", 0))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load inspections: {str(e)}")


@app.get("/api/image")
async def stream_image(path: str = Query(..., description="Volume path to image file")):
    """
    Stream an image from Databricks Volume
    
    Parameters:
    - path: Full volume path (e.g., /Volumes/catalog/schema/volume/file.jpg)
    """
    # Validate path
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    
    if not path.startswith(ALLOWED_PREFIX):
        raise HTTPException(status_code=400, detail=f"path must start with {ALLOWED_PREFIX}")
    
    try:
        # Stream file from Databricks Volume using SDK
        w = WorkspaceClient()
        response = w.files.download(path)
        
        # Determine content type from file extension
        ext = Path(path).suffix.lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        
        # Stream in chunks
        def iter_content():
            while True:
                chunk = response.contents.read(8192)
                if not chunk:
                    break
                yield chunk
        
        return StreamingResponse(
            iter_content(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Accept-Ranges": "bytes"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream image: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
