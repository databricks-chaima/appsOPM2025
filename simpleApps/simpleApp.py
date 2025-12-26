import streamlit as st
import os
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

st.set_page_config(page_title="Photo Gallery", page_icon="📸", layout="wide")

def load_photo(photo_path: str):
    """Load photo from Databricks Volume"""
    w = WorkspaceClient()
    response = w.files.download(photo_path)
    return response.contents.read()

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
    
    st.title("📸 Photo Gallery - Direct from Volumes")
    st.markdown("---")
    
    # Hardcoded photo paths
    photo_paths = [
        "/Volumes/serverless_opm_catalog/opm/quality/images-highres/photo1.jpg",
        "/Volumes/serverless_opm_catalog/opm/quality/images-highres/photo2.jpg",
        "/Volumes/serverless_opm_catalog/opm/quality/images-highres/photo3.jpg",
        "/Volumes/serverless_opm_catalog/opm/quality/images-highres/photo4.jpg"
    ]
    
    cols = st.columns(4)
    
    for i, photo_path in enumerate(photo_paths):
        with cols[i]:
            st.caption(f"Photo {i+1}")
            try:
                with st.spinner("Loading..."):
                    photo_bytes = load_photo(photo_path)
                st.image(photo_bytes, use_column_width=True)
            except Exception as e:
                st.error(f"Failed: {str(e)}")

if __name__ == "__main__":
    main()