# Quality Control Cockpit

A modern FastAPI web application for browsing computer vision quality control inspection images from manufacturing production lines. Designed to run on Databricks Apps on Azure Databricks.

## Use Case

This app displays inspection results from CCD cameras on end-of-line welding stations across 40 factories. Each factory has 2 cameras that capture one photo per minute for computer vision quality control.

## Features

- Modern web UI with OP Mobility brand identity
- Filter by region, factory, camera, prediction status, and defect type
- Search by inspection ID
- Date range filtering
- Paginated image gallery with OK/KO status indicators
- Statistics overview (total, filtered, OK, KO counts)
- Download individual inspection images
- Real-time image streaming from Databricks Volumes

## Technologies Used

- **FastAPI**: High-performance Python web framework
- **Jinja2**: HTML templating
- **Vanilla JavaScript**: Frontend logic (no framework dependencies)
- **Python-dotenv**: Environment variable management
- **Databricks SDK**: Integration with Databricks Unity Catalog (SQL warehouse queries, Volume file streaming, Lakebase authentication)
- **psycopg2**: PostgreSQL driver for Lakebase connectivity

## Architecture

**Backend (FastAPI):**
- `/` - Serve web UI
- `/api/factories` - Get factory metadata
- `/api/inspections` - Get paginated inspections with filters
- `/api/image` - Stream images from Volumes
- `/health` - Health check

**Frontend (HTML/CSS/JS):**
- Single-page application
- Vanilla JavaScript (no build step required)
- Responsive design
- OP Mobility visual identity

## Data Schema

| Field | Type | Description |
|-------|------|-------------|
| inspection_id | String | Unique ID  |
| factory_id | String | Factory identifier |
| camera_id | String | Camera identifier (e.g., "CAM-01") |
| timestamp | Timestamp | Full timestamp of inspection |
| image_path | String | Path to image in Unity Catalog Volumes |
| prediction | String | "OK" or "KO" |
| confidence_score | Double | Model confidence (0.85-0.99) |
| defect_type | String/Null | Null if OK, otherwise defect type |
| inference_time_ms | Integer | Inference duration (50-200ms) |
| model_version | String | Model version (e.g., "v2.3.1") |
| date | Date | Date portion of timestamp |

## Project Structure

```
├── app.py                       # FastAPI application (main backend)
├── templates/
│   └── index.html               # Main web UI template
├── static/
│   ├── css/
│   │   └── style.css            # OP Mobility styling
│   └── js/
│       └── app.js               # Frontend logic
├── services/
│   ├── warehouse.py             # Singleton service for SQL warehouse queries
│   ├── lakebase.py              # Singleton service for Lakebase PostgreSQL queries
│   └── databricks_volume.py    # Databricks Volume operations (legacy)
├── mock_data/
│   ├── generate_mock.py         # Script to generate test data
│   ├── factories.json           # Mock factory data
│   └── inspections.json         # Mock inspection records
├── notebooks/
│   └── load_mock_data_to_delta.py  # Databricks notebook to load data to Delta tables
├── requirements.txt             # Python dependencies
└── README.md
```

## Data Sources

**Lakebase PostgreSQL:**
- `opm.factories_synched` - Factory metadata (factory_id, region, cameras)

**Delta Tables (Unity Catalog):**
- `serverless_opm_catalog.opm.inspections` - Inspection records (see Data Schema above)

**Volume:**
- `/Volumes/serverless_opm_catalog/opm/quality/images-highres/` - Inspection images

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file based on `example.env`:

```bash
# Databricks Configuration (required)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_WAREHOUSE_ID=your-warehouse-id

# Authentication (choose one method)
# Option 1: Service Principal (recommended for production)
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret

# Option 2: Personal Access Token (for development)
# DATABRICKS_TOKEN=your-personal-access-token

# Lakebase PostgreSQL Configuration
LAKEBASE_INSTANCE_NAME=your-lakebase-instance-name
LAKEBASE_DATABASE_NAME=serverless_opm_catalog
DATABRICKS_DATABASE_PORT=5432

# Optional: Change default port (default is 8080)
# PORT=8080
```

### 3. Load data to Delta tables (first time only)

Run the notebook `notebooks/load_mock_data_to_delta.py` in Databricks to create and populate the Delta tables.

### 4. Run the application

```bash
python app.py
```

Or with uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### 5. Open your browser

Navigate to `http://localhost:8080`

## Visual Identity

The app follows OP Mobility brand guidelines:
- Primary Blue: #0066B3
- OK Status: Green (#00A651)
- KO Status: Red (#E31937)
- Clean white background with subtle shadows
- Inter font family

## Databricks Integration

**Lakebase PostgreSQL:**
- Factory metadata queries from Lakebase PostgreSQL database
- Singleton service with OAuth token authentication via Databricks SDK
- Auto-refresh connection after 59 minutes
- Uses psycopg2 for PostgreSQL connectivity

**SQL Warehouse:**
- Inspection queries from Delta tables in Unity Catalog
- Singleton connection manager with auto-refresh (59-minute timeout)
- Uses Databricks SDK statement execution API

**Volume Streaming:**
- Images streamed from Unity Catalog Volumes via FastAPI endpoint
- Browser loads images directly with lazy loading
- Chunked streaming (8KB chunks) for efficient transfer
- No in-memory buffering on backend

## API Documentation

Once running, visit:
- Interactive API docs: `http://localhost:8080/docs`
- Alternative docs: `http://localhost:8080/redoc`

## Deployment on Databricks Apps

This app is designed to run as a Databricks App:

1. Ensure your service principal has access to:
   - SQL Warehouse
   - Unity Catalog tables (`serverless_opm_catalog.opm.*`)
   - Volume path (`/Volumes/serverless_opm_catalog/opm/quality/images-highres/`)

2. Set environment variables in Databricks App configuration

3. The app will automatically use Databricks authentication when running in Databricks

## Development Notes

**Backup Files:**
- `app_streamlit.py.bak` - Original Streamlit version (for reference)
- `server_old.py.bak` - Standalone streaming server (now integrated into main app)

**Performance:**
- Images are lazy-loaded by the browser
- Pagination limits data transfer
- SQL queries are optimized with proper filtering
- Connection pooling via singleton service

## License

Internal use only - OP Mobility
