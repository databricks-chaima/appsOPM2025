"""
Quality Control Image Gallery - Streamlit App

A Streamlit application for browsing computer vision quality control
inspection images from manufacturing production lines.

Designed to run on Databricks Apps with Streamlit.
"""

import os
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
import time
from threading import Thread

# Import services from local services folder
from services.warehouse import Warehouse
from services.lakebase import Lakebase

# Load .env from streamlit_app directory (same directory as app.py)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
ALLOWED_PREFIX = "/Volumes/serverless_opm_catalog/opm/quality/images-highres/"
ITEMS_PER_PAGE = 8

# Page configuration
st.set_page_config(
    page_title="Quality Control Cockpit - OP Mobility",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main header styling - inspired by OPmobility.com */
    .main-header {
        background: linear-gradient(to right, #ffffff 0%, #f8f9fa 100%);
        padding: 0;
        margin-bottom: 2rem;
        border-bottom: 3px solid #0055A4;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .header-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 2.5rem;
        max-width: 100%;
    }
    
    .header-left {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    
    .header-brand {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .header-brand h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: #0055A4;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    
    .header-brand .subtitle {
        margin: 0;
        font-size: 0.875rem;
        color: #6c757d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .header-divider {
        width: 2px;
        height: 50px;
        background: linear-gradient(to bottom, transparent, #0055A4, transparent);
    }
    
    .header-title {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .header-title h2 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #212529;
        line-height: 1.3;
    }
    
    .header-title .tagline {
        margin: 0;
        font-size: 0.875rem;
        color: #6c757d;
        font-weight: 400;
    }
    
    /* Stats cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0066B3;
        margin-bottom: 0.5rem;
    }
    
    .stat-value-ok {
        color: #00A651;
    }
    
    .stat-value-ko {
        color: #E31937;
    }
    
    .stat-label {
        font-size: 0.875rem;
        color: #666;
        font-weight: 500;
    }
    
    /* Image card styling */
    .image-card {
        border: 3px solid #ddd;
        border-radius: 12px;
        padding: 1rem;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .image-card.ok {
        border-color: #00A651;
    }
    
    .image-card.ko {
        border-color: #E31937;
    }
    
    /* Uniform image sizing - force consistent dimensions */
    [data-testid="stImage"] {
        border-radius: 8px;
        overflow: hidden;
        height: 280px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: #f0f0f0;
    }
    
    [data-testid="stImage"] img {
        width: 100% !important;
        height: 280px !important;
        object-fit: cover !important;
        object-position: center !important;
        display: block !important;
    }
    
    /* Alternative selector for older Streamlit versions */
    .stImage, .stImage > div {
        height: 280px !important;
    }
    
    .stImage img {
        width: 100% !important;
        height: 280px !important;
        object-fit: cover !important;
        object-position: center !important;
    }
    
    .inspection-id {
        font-weight: 700;
        font-size: 1rem;
        margin: 0.75rem 0 0.5rem 0;
        color: #333;
    }
    
    .meta-row {
        display: flex;
        justify-content: space-between;
        padding: 0.25rem 0;
        font-size: 0.875rem;
    }
    
    .meta-label {
        color: #666;
        font-weight: 500;
    }
    
    .meta-value {
        color: #333;
        font-weight: 600;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
    }
    
    .status-badge.ok {
        background: #00A651;
        color: white;
    }
    
    .status-badge.ko {
        background: #E31937;
        color: white;
    }
    
    .defect-badge {
        display: inline-block;
        background: #FFA500;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_factories() -> List[Dict[str, Any]]:
    """Load factory data from Lakebase (cached for 5 minutes)"""
    try:
        rows = Lakebase.query("SELECT factory_id, region, cameras FROM opm.factories_synched")
        return rows
    except Exception as e:
        st.error(f"Failed to load factories: {str(e)}")
        return []


@st.cache_data(ttl=300)
def load_filter_options() -> List[str]:
    """Load defect types for filtering (cached for 5 minutes)"""
    try:
        query = """
            SELECT DISTINCT defect_type
            FROM serverless_opm_catalog.opm.inspections
            WHERE defect_type IS NOT NULL
            ORDER BY defect_type
        """
        rows = Warehouse.query(query)
        return [row.get("defect_type") or row.get("DEFECT_TYPE") or row.get("DefectType") 
                for row in rows if row.get("defect_type") or row.get("DEFECT_TYPE") or row.get("DefectType")]
    except Exception as e:
        st.error(f"Failed to load filter options: {str(e)}")
        return []


def load_inspections(
    factory: Optional[str] = None,
    camera: Optional[str] = None,
    prediction: Optional[str] = None,
    defect_type: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    per_page: int = ITEMS_PER_PAGE
) -> Dict[str, Any]:
    """Load inspections with filters and pagination"""
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
        st.error(f"Failed to load inspections: {str(e)}")
        return {
            "inspections": [],
            "pagination": {"page": 1, "per_page": per_page, "total_count": 0, "total_pages": 0},
            "stats": {"total": 0, "filtered": 0, "ok_count": 0, "ko_count": 0}
        }


@st.cache_data(ttl=3600)
def load_image_from_volume(image_path: str) -> Optional[bytes]:
    """Load image from Databricks Volume (cached for 1 hour)"""
    if not image_path:
        return None
    
    if not image_path.startswith(ALLOWED_PREFIX):
        return None
    
    try:
        w = WorkspaceClient()
        response = w.files.download(image_path)
        
        # Read all content into memory
        image_bytes = response.contents.read()
        return image_bytes
    except Exception as e:
        return None


class ImageLoaderThread(Thread):
    """Worker thread to load images in background"""
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
        self.image_bytes = None
        self.error = None
    
    def run(self):
        """Load image in background thread"""
        try:
            self.image_bytes = load_image_from_volume(self.image_path)
        except Exception as e:
            self.error = str(e)


def main():
    """Main application logic"""
    
    # Header - inspired by OPmobility.com visual identity
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <div class="header-left">
                <div class="header-brand">
                    <h1>OPmobility</h1>
                    <span class="subtitle">Quality Control</span>
                </div>
                <div class="header-divider"></div>
                <div class="header-title">
                    <h2>Inspection Gallery</h2>
                    <span class="tagline">Manufacturing Intelligence Platform</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    factories = load_factories()
    defect_types = load_filter_options()
    
    # Extract regions and cameras
    regions = sorted(list(set(f.get("region") for f in factories if f.get("region"))))
    all_cameras = []
    for f in factories:
        cameras = f.get("cameras") or []
        all_cameras.extend(cameras)
    cameras = sorted(list(set(all_cameras)))
    
    # Initialize filter tracking in session state
    if 'last_filters' not in st.session_state:
        st.session_state.last_filters = {}
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Factory selection
        st.subheader("Location")
        selected_region = st.selectbox("Region", ["All"] + regions, key="region")
        
        # Filter factories by region
        if selected_region != "All":
            filtered_factories = [f for f in factories if f.get("region") == selected_region]
        else:
            filtered_factories = factories
        
        factory_ids = sorted([f.get("factory_id") for f in filtered_factories if f.get("factory_id")])
        selected_factory = st.selectbox("Factory", ["All"] + factory_ids, key="factory")
        
        selected_camera = st.selectbox("Camera", ["All"] + cameras, key="camera")
        
        # Prediction filters
        st.subheader("Quality Status")
        selected_prediction = st.selectbox("Prediction", ["All", "OK", "KO"], key="prediction")
        selected_defect = st.selectbox("Defect Type", ["All"] + defect_types, key="defect")
        
        # Search
        st.subheader("Search")
        search_query = st.text_input("Inspection ID", key="search", placeholder="INSP-2025-...")
        
        # Date filters
        st.subheader("Date Range")
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("From", value=None, key="date_from")
        with col2:
            date_to = st.date_input("To", value=None, key="date_to")
        
        # Apply filters button
        apply_filters = st.button("🔄 Apply Filters", use_container_width=True, type="primary")
        reset_filters = st.button("🔁 Reset", use_container_width=True)
    
    # Create current filter state
    current_filters = {
        'region': selected_region,
        'factory': selected_factory,
        'camera': selected_camera,
        'prediction': selected_prediction,
        'defect': selected_defect,
        'search': search_query,
        'date_from': str(date_from) if date_from else None,
        'date_to': str(date_to) if date_to else None
    }
    
    # Use query params for pagination to avoid double-load
    query_params = st.query_params
    current_page = int(query_params.get("page", 1))
    
    # Check if any filter changed - reset to page 1 if so
    filters_changed = current_filters != st.session_state.last_filters
    
    if filters_changed and st.session_state.last_filters:  # Don't reset on first load
        current_page = 1
        st.query_params["page"] = 1
    
    # Update last filters
    st.session_state.last_filters = current_filters.copy()
    
    # Reset everything if reset button clicked
    if reset_filters:
        current_page = 1
        st.query_params.clear()
        st.query_params["page"] = 1
        st.session_state.last_filters = {}
        st.rerun()
    
    # Convert filters
    factory_filter = None if selected_factory == "All" else selected_factory
    camera_filter = None if selected_camera == "All" else selected_camera
    prediction_filter = None if selected_prediction == "All" else selected_prediction
    defect_filter = None if selected_defect == "All" else selected_defect
    date_from_str = date_from.strftime("%Y-%m-%d") if date_from else None
    date_to_str = date_to.strftime("%Y-%m-%d") if date_to else None
    
    # Load inspections
    with st.spinner("Loading inspections..."):
        data = load_inspections(
            factory=factory_filter,
            camera=camera_filter,
            prediction=prediction_filter,
            defect_type=defect_filter,
            search=search_query if search_query else None,
            date_from=date_from_str,
            date_to=date_to_str,
            page=current_page,
            per_page=ITEMS_PER_PAGE
        )
    
    # Display stats
    stats = data["stats"]
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{stats["total"]}</div>
            <div class="stat-label">Total Inspections</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{stats["filtered"]}</div>
            <div class="stat-label">Filtered Results</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value stat-value-ok">{stats["ok_count"]}</div>
            <div class="stat-label">OK</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value stat-value-ko">{stats["ko_count"]}</div>
            <div class="stat-label">KO</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display inspections
    inspections = data["inspections"]
    pagination = data["pagination"]
    
    if not inspections:
        st.info("No inspections found matching your filters.")
    else:
        # Step 1: Start all image loading threads in parallel
        with st.spinner("Loading images..."):
            threads = []
            for inspection in inspections:
                thread = ImageLoaderThread(inspection["image_path"])
                thread.start()
                threads.append(thread)
            
            # Step 2: Wait for all threads to complete (parallel loading)
            for thread in threads:
                thread.join(timeout=10)  # 10 second timeout per image
        
        # Step 3: Display everything once (single render, no double-load)
        for i in range(0, len(inspections), 4):
            cols = st.columns(4)
            
            for j, col in enumerate(cols):
                if i + j < len(inspections):
                    inspection = inspections[i + j]
                    thread = threads[i + j]
                    
                    with col:
                        # Display image (already loaded)
                        if thread.image_bytes:
                            st.image(thread.image_bytes, use_column_width=True)
                        else:
                            st.error("❌ Image not available")
                        
                        # Status badge
                        status_class = "ok" if inspection["prediction"] == "OK" else "ko"
                        status_html = f'<div class="status-badge {status_class}">{inspection["prediction"]}</div>'
                        if inspection["defect_type"]:
                            status_html += f'<span class="defect-badge">{inspection["defect_type"]}</span>'
                        st.markdown(status_html, unsafe_allow_html=True)
                        
                        # Inspection details
                        st.markdown(f'<div class="inspection-id">{inspection["inspection_id"]}</div>', unsafe_allow_html=True)
                        
                        # Metadata
                        confidence = (inspection["confidence_score"] * 100)
                        st.markdown(f"""
                        <div class="meta-row">
                            <span class="meta-label">Factory</span>
                            <span class="meta-value">{inspection["factory_id"]}</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta-label">Camera</span>
                            <span class="meta-value">{inspection["camera_id"]}</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta-label">Timestamp</span>
                            <span class="meta-value">{inspection["timestamp"]}</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta-label">Confidence</span>
                            <span class="meta-value">{confidence:.1f}%</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta-label">Inference</span>
                            <span class="meta-value">{inspection["inference_time_ms"]}ms</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta-label">Model</span>
                            <span class="meta-value">{inspection["model_version"]}</span>
                        </div>
                        """, unsafe_allow_html=True)
        
        # If current page exceeds total pages (due to filters), reset to page 1
        if pagination["page"] > pagination["total_pages"] and pagination["total_pages"] > 0:
            st.query_params["page"] = 1
            st.rerun()
        
        # Pagination using links to avoid double-load
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        prev_page = max(1, pagination["page"] - 1)
        next_page = min(pagination["total_pages"], pagination["page"] + 1)
        
        with col1:
            if pagination["page"] > 1:
                st.markdown(f'<a href="?page={prev_page}" target="_self"><button style="width: 100%; padding: 0.5rem; background: #0055A4; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">⬅️ Previous</button></a>', unsafe_allow_html=True)
            else:
                st.markdown('<button style="width: 100%; padding: 0.5rem; background: #e0e0e0; color: #999; border: none; border-radius: 4px; cursor: not-allowed; font-weight: 600;" disabled>⬅️ Previous</button>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Page {pagination['page']} of {pagination['total_pages']}</strong></div>", unsafe_allow_html=True)
        
        with col3:
            if pagination["page"] < pagination["total_pages"]:
                st.markdown(f'<a href="?page={next_page}" target="_self"><button style="width: 100%; padding: 0.5rem; background: #0055A4; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">Next ➡️</button></a>', unsafe_allow_html=True)
            else:
                st.markdown('<button style="width: 100%; padding: 0.5rem; background: #e0e0e0; color: #999; border: none; border-radius: 4px; cursor: not-allowed; font-weight: 600;" disabled>Next ➡️</button>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

