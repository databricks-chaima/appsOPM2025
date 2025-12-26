# Quick Start Guide - Streamlit App

## 🚀 Run the App Locally

### Prerequisites
- Python 3.9+
- Access to Databricks workspace
- Environment variables configured in parent directory's `.env` file

### Steps

1. **Navigate to the streamlit_app directory**
   ```bash
   cd streamlit_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   ./run.sh
   ```
   
   Or directly:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`

## 🎯 Key Features

- **8 Images Per Page**: Optimized gallery view with 4x2 grid layout
- **Advanced Filters**: Region, Factory, Camera, Prediction (OK/KO), Defect Type
- **Search**: Find inspections by ID
- **Date Range**: Filter by date range
- **Real-time Stats**: Total, Filtered, OK, and KO counts
- **Pagination**: Navigate through results efficiently

## 🔧 Configuration

The app uses environment variables from the parent directory's `.env` file:

```bash
# Required
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_WAREHOUSE_ID=your-warehouse-id
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret

# Lakebase PostgreSQL
PGHOST=your-lakebase-host.database.cloud.databricks.com
PGPORT=5432
PGDATABASE=serverless_opm_catalog
PGUSER=your-postgres-user-id
PGSSLMODE=require
```

## 📊 Data Sources

1. **Lakebase PostgreSQL**: Factory metadata (`opm.factories_synched`)
2. **SQL Warehouse**: Inspection records (`serverless_opm_catalog.opm.inspections`)
3. **Unity Catalog Volumes**: Images (`/Volumes/serverless_opm_catalog/opm/quality/images-highres/`)

## 🎨 Visual Design

- **Primary Blue**: #0066B3 (OP Mobility brand)
- **OK Status**: Green (#00A651)
- **KO Status**: Red (#E31937)
- Clean, modern card-based layout

## ⚡ Performance

- **Caching Strategy**:
  - Factory data: 5 minutes
  - Defect types: 5 minutes
  - Images: 1 hour
- **Connection Management**: Auto-refresh after 59 minutes
- **Pagination**: 8 images per page for optimal loading

## 🐛 Troubleshooting

### App won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify environment variables are set in parent directory's `.env` file

### Images not loading
- Verify `DATABRICKS_HOST` and authentication credentials
- Check that the service principal has access to the Volume path
- Ensure image paths start with `/Volumes/serverless_opm_catalog/opm/quality/images-highres/`

### Database connection errors
- Verify `DATABRICKS_WAREHOUSE_ID` is correct
- Check Lakebase PostgreSQL credentials (`PGHOST`, `PGUSER`, etc.)
- Ensure service principal has access to Unity Catalog tables

### Filters not working
- Check that data exists in the database
- Verify SQL Warehouse is running
- Check browser console for errors

## 📚 Additional Resources

- Full documentation: See `README.md` in this directory
- Streamlit docs: https://docs.streamlit.io
- Databricks SDK: https://docs.databricks.com/dev-tools/sdk-python.html
- Multithreading in Streamlit: https://docs.streamlit.io/develop/concepts/design/multithreading

## 🚢 Deployment on Databricks Apps

1. Create a new Databricks App with Streamlit support
2. Upload the `streamlit_app/` directory
3. Set environment variables in app configuration
4. Ensure service principal has required permissions:
   - SQL Warehouse access
   - Unity Catalog tables (`serverless_opm_catalog.opm.*`)
   - Volume path (`/Volumes/serverless_opm_catalog/opm/quality/images-highres/`)
5. Start the app

The app will automatically use Databricks authentication when running in Databricks.

## 📝 Notes

- The app imports services from the parent directory (`../services/`)
- All services use singleton pattern for efficient connection management
- Images are cached per-user session to improve performance
- Pagination state is maintained in Streamlit session state

