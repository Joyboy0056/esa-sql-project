# Enrich DB metadata
from psycopg2.extensions import connection

from src.logger import logger

class DBRefiner:
    """Curate and enhance database schema and metadata"""
    
    def __init__(self):
        pass

    comments = {
            'sentinel_scenes': {
                'scene_id': 'Unique identifier for satellite acquisition',
                'datetime': 'Acquisition timestamp (UTC)',
                'start_datetime': 'Acquisition start time',
                'end_datetime': 'Acquisition end time',
                'platform': 'Satellite name (sentinel-2a, sentinel-2b)',
                'constellation': 'Mission family (sentinel-2)',
                'instruments': 'Sensor instruments used',
                'cloud_cover': 'Cloud coverage percentage (0-100)',
                'snow_cover': 'Snow coverage percentage (0-100)',
                'sun_azimuth': 'Sun direction angle (degrees)',
                'sun_elevation': 'Sun height above horizon (degrees)',
                'view_azimuth': 'Viewing angle azimuth',
                'incidence_angle': 'Sensor incidence angle',
                'absolute_orbit': 'Absolute orbit number since launch',
                'relative_orbit': 'Relative orbit number (1-143)',
                'orbit_state': 'Ascending or descending',
                'product_type': 'Product type identifier',
                'processing_level': 'Processing level (Level-2A = surface reflectance)',
                'processing_version': 'Processing software version',
                'timeliness': 'Data delivery timeliness category',
                'grid_code': 'MGRS tile identifier (e.g., T32TQN)',
                'footprint': 'Geographic coverage polygon (WGS84)',
                'bbox_minx': 'Bounding box minimum longitude',
                'bbox_miny': 'Bounding box minimum latitude',
                'bbox_maxx': 'Bounding box maximum longitude',
                'bbox_maxy': 'Bounding box maximum latitude',
                'gsd': 'Ground Sample Distance (meters per pixel)',
                'created': 'Product creation timestamp',
                'updated': 'Product update timestamp',
                'ingestion_time': 'Database ingestion timestamp'
            },

        'scene_assets': {
            'asset_id': 'Unique asset identifier (auto-increment)',
            'scene_id': 'Reference to parent scene',
            'asset_key': 'Asset identifier (B02_10m, TCI_10m, thumbnail, etc)',
            'asset_type': 'MIME type (image/tiff, image/jpeg, application/xml)',
            'href': 'Direct download URL for this asset',
            'roles': 'Asset roles (data, visual, thumbnail, metadata)',
            'eo_bands': 'Spectral bands contained (blue, green, red, nir, etc)',
            'gsd': 'Ground Sample Distance in meters (10, 20, or 60)',
            'file_size': 'File size in bytes',
            'proj_shape': 'Image dimensions [height, width] in pixels',
            'title': 'Human-readable asset title',
            'description': 'Detailed asset description'
        }
    }

    def fill_comments(self, conn: connection):
        """Add COMMENT descriptions to table columns in PostgresDB"""
        
        cursor = conn.cursor()
        for table, cols in self.comments.items():
            for col, desc in cols.items():
                cursor.execute(f"""
                    COMMENT ON COLUMN {table}.{col} IS %s
                """, (desc,))
        
        conn.commit()
        logger.info(f"✓ Comments added to {sum(len(c) for c in self.comments.values())} columns")

    def add_indices(self):
        pass

