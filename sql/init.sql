--SQL script with DDL for the schema tables

CREATE TABLE sentinel_scenes (
    -- Identificatori
    scene_id TEXT PRIMARY KEY,
    
    -- Temporale
    datetime TIMESTAMPTZ NOT NULL,
    start_datetime TIMESTAMPTZ,
    end_datetime TIMESTAMPTZ,
    
    -- Piattaforma
    platform TEXT,
    constellation TEXT,
    instruments TEXT[],
    
    -- Qualità immagine
    cloud_cover REAL,
    snow_cover REAL,
    
    -- Geometria solare
    sun_azimuth REAL,
    sun_elevation REAL,
    view_azimuth REAL,
    incidence_angle REAL,
    
    -- Orbita
    absolute_orbit INTEGER,
    relative_orbit INTEGER,
    orbit_state TEXT,
    
    -- Prodotto
    product_type TEXT,
    processing_level TEXT,
    processing_version TEXT,
    timeliness TEXT,
    
    -- Spaziale
    grid_code TEXT,  -- Tile ID (es. T32TQN)
    footprint GEOMETRY(Polygon, 4326),
    bbox_minx REAL,
    bbox_miny REAL,
    bbox_maxx REAL,
    bbox_maxy REAL,
    
    -- Metadata
    gsd REAL,  -- Ground Sample Distance
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    ingestion_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- Assets table (image links and data products)
CREATE TABLE scene_assets (
    asset_id SERIAL PRIMARY KEY,
    scene_id TEXT NOT NULL REFERENCES sentinel_scenes(scene_id) ON DELETE CASCADE,
    
    -- Asset identification
    asset_key TEXT NOT NULL,  -- 'B02_10m', 'TCI_10m', 'thumbnail', etc
    asset_type TEXT,          -- 'image/tiff', 'image/jpeg', 'application/xml'
    
    -- Access
    href TEXT NOT NULL,       -- Download URL
    
    -- Classification
    roles TEXT[],             -- ['data', 'visual', 'thumbnail']
    
    -- Technical specs
    eo_bands TEXT[],          -- ['blue', 'green', 'red'] for RGB
    gsd REAL,                 -- Ground sample distance (10m, 20m, 60m)
    
    -- File info
    file_size BIGINT,         -- Bytes
    proj_shape INTEGER[],     -- [height, width] in pixels
    
    -- Metadata
    title TEXT,
    description TEXT,
    
    UNIQUE(scene_id, asset_key)
);

-- Indices
CREATE INDEX idx_datetime ON sentinel_scenes(datetime);
CREATE INDEX idx_cloud_cover ON sentinel_scenes(cloud_cover);
CREATE INDEX idx_grid_code ON sentinel_scenes(grid_code);
CREATE INDEX idx_footprint ON sentinel_scenes USING GIST(footprint);
--
CREATE INDEX idx_assets_scene ON scene_assets(scene_id);
CREATE INDEX idx_assets_key ON scene_assets(asset_key);
CREATE INDEX idx_assets_type ON scene_assets(asset_type);