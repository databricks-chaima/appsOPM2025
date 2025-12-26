# Implementation Notes - Streamlit Quality Control Gallery

## Overview

This Streamlit app replicates the FastAPI image gallery functionality with a native Streamlit implementation. It's designed specifically for Databricks Apps with Streamlit support.

## Key Design Decisions

### 1. Architecture

**Reused Components:**
- `../services/warehouse.py` - SQL Warehouse singleton service
- `../services/lakebase.py` - Lakebase PostgreSQL singleton service
- Both services maintain the 59-minute connection refresh pattern

**New Components:**
- `app.py` - Main Streamlit application
- `.streamlit/config.toml` - Streamlit configuration with OP Mobility branding

### 2. Data Flow

```
User Interaction
    ↓
Streamlit Widgets (Sidebar)
    ↓
Filter Collection
    ↓
SQL Queries (via Warehouse/Lakebase services)
    ↓
Data Processing
    ↓
Image Loading (from Volumes via WorkspaceClient)
    ↓
Cached Display (Streamlit caching)
```

### 3. Caching Strategy

Following Streamlit best practices and the multithreading documentation:

- **`@st.cache_data(ttl=300)`** for factory data (5 minutes)
  - Low change frequency
  - Shared across filter operations
  
- **`@st.cache_data(ttl=300)`** for defect types (5 minutes)
  - Low change frequency
  - Used in filter dropdown
  
- **`@st.cache_data(ttl=3600)`** for images (1 hour)
  - High reuse potential
  - Large data size
  - Reduces Volume API calls

### 4. Pagination Implementation

Uses Streamlit session state to maintain page number:
```python
if 'page' not in st.session_state:
    st.session_state.page = 1
```

Resets to page 1 when filters change to avoid empty results.

### 5. Image Display

**4x2 Grid Layout:**
- 4 columns per row
- 2 rows per page
- Total: 8 images per page

**Implementation:**
```python
for i in range(0, len(inspections), 4):
    cols = st.columns(4)
    for j, col in enumerate(cols):
        if i + j < len(inspections):
            render_inspection_card(inspections[i + j], col)
```

### 6. Multithreading Considerations

Per [Streamlit's multithreading documentation](https://docs.streamlit.io/develop/concepts/design/multithreading):

- Each user session runs in its own script thread
- Streamlit commands are called from the main script thread (no custom threads needed)
- Caching reduces redundant computations
- No custom multithreading implemented (not officially supported)
- All Streamlit commands (`st.image`, `st.markdown`, etc.) are called from the main script thread

**Why no custom threads?**
- Streamlit's architecture handles concurrency per-user automatically
- Custom threads would require `ScriptRunContext` management (not officially supported)
- Caching provides sufficient performance optimization
- IO operations (database queries, image loading) are sequential but cached

### 7. Databricks Integration

**WorkspaceClient Usage:**
```python
w = WorkspaceClient()
response = w.files.download(image_path)
image_bytes = response.contents.read()
```

**Authentication:**
- Automatically uses Databricks SDK authentication
- Supports both service principal and PAT
- OAuth tokens managed by singleton services

### 8. Error Handling

- Try-catch blocks around all external calls
- Graceful degradation (show error messages, don't crash)
- Fallback to empty states when data unavailable

### 9. UI/UX Design

**Follows OP Mobility Brand:**
- Primary Blue: #0066B3
- OK Status: Green (#00A651)
- KO Status: Red (#E31937)

**Layout:**
- Sidebar for all filters (keeps main area clean)
- Stats cards at top (4-column grid)
- Image gallery in main area (4-column grid)
- Pagination at bottom

**Custom CSS:**
- Injected via `st.markdown()` with `unsafe_allow_html=True`
- Maintains visual consistency with FastAPI version
- Card-based design for inspection items

### 10. Performance Optimizations

1. **Caching**: Aggressive caching of factory data, defect types, and images
2. **Pagination**: Only load 8 images at a time
3. **Lazy Loading**: Images loaded on-demand when page is viewed
4. **Singleton Services**: Connection pooling via singleton pattern
5. **Query Optimization**: Filtered queries with proper WHERE clauses

### 11. Differences from FastAPI Version

| Feature | FastAPI | Streamlit |
|---------|---------|-----------|
| Frontend | Custom HTML/CSS/JS | Native Streamlit widgets |
| State Management | JavaScript | Streamlit session state |
| Image Loading | Streaming endpoint | Direct WorkspaceClient |
| Caching | Browser cache | `@st.cache_data` |
| Interactivity | AJAX calls | Widget callbacks |
| Deployment | Any ASGI server | Streamlit-enabled environment |

### 12. Known Limitations

1. **No Download Button**: Streamlit doesn't easily support downloading images from external sources
   - Could be added with `st.download_button` if needed
   
2. **No Real-time Updates**: Streamlit requires page rerun for updates
   - Could use `st.experimental_rerun()` with timers if needed
   
3. **Memory Usage**: Images cached in memory (configurable via TTL)
   - 1-hour TTL balances performance vs memory

### 13. Testing Checklist

- [ ] Filters work correctly (region, factory, camera, prediction, defect type)
- [ ] Search by inspection ID works
- [ ] Date range filtering works
- [ ] Pagination works (previous/next buttons)
- [ ] Images load correctly from Volumes
- [ ] Stats cards update with filters
- [ ] Reset button clears all filters
- [ ] Apply filters button triggers data reload
- [ ] Caching works (check performance on repeated views)
- [ ] Error handling works (test with invalid credentials)

### 14. Future Enhancements

Potential improvements (not implemented):

1. **Export Functionality**: Export filtered results to CSV
2. **Image Zoom**: Click to view full-size image
3. **Batch Download**: Download multiple images at once
4. **Real-time Updates**: Auto-refresh with new inspections
5. **Advanced Analytics**: Charts and trends over time
6. **Image Comparison**: Side-by-side comparison of OK vs KO
7. **Annotation**: Mark up images with notes

### 15. Deployment Considerations

**Databricks Apps:**
- Requires Streamlit support in Databricks Apps
- Environment variables set via app configuration
- Service principal needs proper permissions
- Volume path must be accessible

**Resource Requirements:**
- Memory: ~1-2GB (depends on cache size)
- CPU: Minimal (mostly IO-bound)
- Network: Moderate (image streaming from Volumes)

## References

- [Streamlit Multithreading Documentation](https://docs.streamlit.io/develop/concepts/design/multithreading)
- [Databricks Apps Cookbook](https://apps-cookbook.dev/)
- [Databricks SDK Python](https://docs.databricks.com/dev-tools/sdk-python.html)
- [Lakebase Read Example](https://apps-cookbook.dev/docs/streamlit/tables/lakebase_read)

## Conclusion

This Streamlit implementation provides a clean, Python-only solution for the quality control image gallery. It reuses existing services, follows Streamlit best practices, and is optimized for Databricks Apps deployment.

