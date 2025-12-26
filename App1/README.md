# Quality Control Cockpit - Streamlit Version

A Streamlit web application for browsing computer vision quality control inspection images from manufacturing production lines. Designed to run on Databricks Apps with Streamlit support.

## Purpose

This Streamlit app provides an image gallery interface for quality control inspections, displaying 8 images per page with comprehensive filtering capabilities. It's designed specifically for Databricks environments and replaces the FastAPI version with a native Streamlit implementation.

## Features

- **Image Gallery**: Display 8 inspection images per page in a 4x2 grid layout
- **Advanced Filtering**: 
  - Region, Factory, and Camera selection
  - Prediction status (OK/KO)
  - Defect type filtering
  - Inspection ID search
  - Date range filtering
- **Real-time Statistics**: Total inspections, filtered results, OK/KO counts
- **Databricks Integration**: 
  - Queries Lakebase PostgreSQL for factory metadata
  - Queries SQL Warehouse for inspection data
  - Streams images directly from Unity Catalog Volumes
- **Performance Optimized**: 
  - Caching for factory and defect type data (5 minutes)
  - Image caching (1 hour)
  - Pagination to limit data transfer
  - Efficient connection management with 59-minute auto-refresh

## Technologies Used

- **Streamlit**: Modern Python web framework for data apps
- **Databricks SDK**: Integration with Unity Catalog, SQL Warehouse, and Volumes
- **psycopg2**: PostgreSQL driver for Lakebase connectivity
- **Python-dotenv**: Environment variable management

## Architecture

The app uses a three-tier data architecture:

1. **Lakebase PostgreSQL** (`services.lakebase`):
   - Factory metadata: `opm.factories_synched`
   - Singleton service with OAuth token authentication
   - Auto-refresh after 59 minutes

2. **SQL Warehouse** (`services.warehouse`):
   - Inspection records: `serverless_opm_catalog.opm.inspections`
   - Singleton service with auto-refresh
   - Uses Databricks SDK statement execution API

3. **Unity Catalog Volumes**:
   - Image storage: `/Volumes/serverless_opm_catalog/opm/quality/images-highres/`
   - Direct streaming via WorkspaceClient

## Project Structure

```
streamlit_app/
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies (Streamlit-specific)
└── README.md               # This file
```

The app imports services from the parent directory:
- `../services/warehouse.py` - SQL Warehouse queries
- `../services/lakebase.py` - Lakebase PostgreSQL queries

## Getting Started

### 1. Install dependencies

```bash
cd streamlit_app
pip install -r requirements.txt
```

### 2. Configure environment variables

The app uses the `.env` file from the parent directory. Ensure it contains:

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

# Lakebase PostgreSQL Configuration (standard PG environment variables)
PGHOST=your-lakebase-host.database.cloud.databricks.com
PGPORT=5432
PGDATABASE=serverless_opm_catalog
PGUSER=your-postgres-user-id
PGSSLMODE=require
```

### 3. Run the application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

### 4. Databricks Deployment

To deploy on Databricks Apps:

1. Create a new Databricks App with Streamlit support
2. Set environment variables in the app configuration
3. The app will use Databricks authentication automatically
4. Ensure the service principal has access to:
   - SQL Warehouse
   - Unity Catalog tables (`serverless_opm_catalog.opm.*`)
   - Volume path (`/Volumes/serverless_opm_catalog/opm/quality/images-highres/`)

## Data Schema

| Field | Type | Description |
|-------|------|-------------|
| inspection_id | String | Unique ID  |
| factory_id | String | Factory identifier |
| camera_id | String | Camera identifier |
| timestamp | Timestamp | Full timestamp of inspection |
| image_path | String | Path to image in Unity Catalog Volumes |
| prediction | String | "OK" or "KO" |
| confidence_score | Double | Model confidence (0.85-0.99) |
| defect_type | String/Null | Null if OK, otherwise defect type |
| inference_time_ms | Integer | Inference duration (50-200ms) |
| model_version | String | Model version (e.g., "v2.3.1") |
| date | Date | Date portion of timestamp |

## Performance Considerations

### Caching Strategy
- **Factory data**: Cached for 5 minutes (low change frequency)
- **Defect types**: Cached for 5 minutes (low change frequency)
- **Images**: Cached for 1 hour (high reuse, large size)
- Cache is per-user session to ensure data freshness

### Connection Management
- Singleton services maintain connection state
- Auto-refresh after 59 minutes (OAuth token expiry)
- Efficient connection pooling

### Multithreading
While Streamlit doesn't officially support custom multithreading, the app is designed with Streamlit's architecture in mind:
- Each user session runs in its own script thread
- Caching reduces redundant computations
- Image loading is optimized with Streamlit's native caching

For more information on Streamlit's threading model, see: https://docs.streamlit.io/develop/concepts/design/multithreading

## Visual Design

The app follows OP Mobility brand guidelines:
- **Primary Blue**: #0066B3
- **OK Status**: Green (#00A651)
- **KO Status**: Red (#E31937)
- Clean, modern interface with card-based layout
- Responsive grid system (4 columns)

## Differences from FastAPI Version

1. **No separate frontend**: Streamlit handles both backend and frontend
2. **Built-in interactivity**: Native widgets replace custom JavaScript
3. **Session state**: Streamlit manages state automatically
4. **Caching**: Uses Streamlit's `@st.cache_data` decorator
5. **Deployment**: Simpler deployment on Databricks Apps with Streamlit support

## Development Notes

- The app imports services from the parent directory
- Services are singleton classes that manage connection lifecycle
- All queries use parameterized WHERE clauses for security
- Images are streamed directly from Volumes (no local storage)

## License

Internal use only - OP Mobility

