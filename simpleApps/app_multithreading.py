import streamlit as st
import os
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from pathlib import Path
from threading import Thread

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

st.set_page_config(page_title="Photo Gallery", page_icon="📸", layout="wide")

def query_database(sql_query: str):
    """Query Databricks SQL Warehouse"""
    w = WorkspaceClient()
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_query,
        wait_timeout="30s"
    )
    
    rows = []
    if result.result and result.result.data_array:
        columns = [col.name for col in result.manifest.schema.columns]
        for row_array in result.result.data_array:
            rows.append({columns[i]: row_array[i] for i in range(len(columns))})
    
    return rows

def load_photo(photo_path: str):
    """Load photo from Databricks Volume"""
    w = WorkspaceClient()
    response = w.files.download(photo_path)
    return response.contents.read()

class PhotoLoader(Thread):
    """Background thread to load photo"""
    def __init__(self, photo_path: str):
        super().__init__()
        self.photo_path = photo_path
        self.photo_bytes = None
        self.error = None
    
    def run(self):
        try:
            self.photo_bytes = load_photo(self.photo_path)
        except Exception as e:
            self.error = str(e)

def main():
    st.markdown("""
    <style>
        [data-testid="stImage"] img {
            width: 100% !important;
            height: 280px !important;
            object-fit: cover !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📸 Photo Gallery - From Database (Parallel)")
    st.markdown("---")
    
    # Query database
    query = """
        SELECT 
            image_path, 
            inspection_id, 
            prediction,
            factory_id,
            confidence_score
        FROM serverless_opm_catalog.opm.inspections
        ORDER BY timestamp DESC
        LIMIT 4
    """
    
    try:
        with st.spinner("Fetching from database..."):
            inspections = query_database(query)
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        st.stop()
    
    if not inspections:
        st.info("No photos found")
        st.stop()
    
    st.success(f"✅ Found {len(inspections)} photos")
    st.markdown("---")
    
    # Load all photos in parallel
    with st.spinner("Loading photos in parallel..."):
        threads = [PhotoLoader(insp['image_path']) for insp in inspections]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads (10 sec timeout each)
        for t in threads:
            t.join(timeout=10)
    
    # Display results
    cols = st.columns(4)
    
    for i, (thread, inspection) in enumerate(zip(threads, inspections)):
        with cols[i]:
            if thread.photo_bytes:
                st.image(thread.photo_bytes, use_column_width=True)
                st.caption(f"🆔 {inspection.get('inspection_id', 'N/A')}")
                st.caption(f"🏭 {inspection.get('factory_id', 'N/A')}")
                
                prediction = inspection.get('prediction', 'Unknown')
                try:
                    confidence = float(inspection.get('confidence_score', 0))
                    if prediction == 'OK':
                        st.success(f"✅ {prediction} ({confidence*100:.1f}%)")
                    elif prediction == 'KO':
                        st.error(f"❌ {prediction} ({confidence*100:.1f}%)")
                    else:
                        st.info(f"❓ {prediction}")
                except (ValueError, TypeError):
                    st.info(f"{prediction}")
                    
            elif thread.error:
                st.error(f"Error: {thread.error}")
            else:
                st.warning("Timeout")

if __name__ == "__main__":
    main()