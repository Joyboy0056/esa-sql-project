-- Find satellite scenes covering Rome
SELECT scene_id, datetime, cloud_cover, grid_code
FROM sentinel_scenes
WHERE ST_Intersects(
    footprint,
    ST_SetSRID(ST_MakePoint(12.4964, 41.9028), 4326)
)
ORDER BY datetime DESC
LIMIT 10;

-- Show me the clearest satellite images of Milan from the last 3 months
SELECT scene_id, datetime, cloud_cover, platform
FROM sentinel_scenes
WHERE ST_Intersects(
    footprint,
    ST_SetSRID(ST_MakePoint(9.1900, 45.4642), 4326)
)
AND datetime >= NOW() - INTERVAL '3 months'
AND cloud_cover < 20
ORDER BY cloud_cover ASC
LIMIT 5;

-- Find satellite scenes along the Tuscan coast with less than 5% clouds
WITH tuscany_coast AS (
    SELECT ST_MakeLine(ARRAY[
        ST_SetSRID(ST_MakePoint(10.0, 43.8), 4326),
        ST_SetSRID(ST_MakePoint(10.3, 43.5), 4326),
        ST_SetSRID(ST_MakePoint(10.8, 42.8), 4326),
        ST_SetSRID(ST_MakePoint(11.1, 42.4), 4326)
    ]) as coastline
)
SELECT s.scene_id, s.datetime, s.cloud_cover, s.grid_code
FROM sentinel_scenes s, tuscany_coast tc
WHERE ST_DWithin(
    s.footprint::geography,
    tc.coastline::geography,
    20000
)
AND s.cloud_cover < 5
ORDER BY s.datetime DESC
LIMIT 10;

-- Geodesic between Rome and Milan in GeoJSON output
SELECT 
    'Roma-Milano geodesic' as name,
    json_build_object(
        'type', 'LineString',
        'coordinates', json_build_array(
            json_build_array(12.49, 41.90),
            json_build_array(9.19, 45.46)
        )
    ) as geometry,
    ST_Length(
        ST_ShortestLine(
            ST_SetSRID(ST_MakePoint(12.49, 41.90), 4326)::geography,
            ST_SetSRID(ST_MakePoint(9.19, 45.46), 4326)::geography
        )::geography
    ) / 1000 as distance_km
    -- `https://geojson.io` per visualizzare
;

-- Compare straight line distance vs actual distance between Rome and Palermo
WITH points AS (
    SELECT 
        ST_SetSRID(ST_MakePoint(12.49, 41.90), 4326) as roma,
        ST_SetSRID(ST_MakePoint(13.36, 38.12), 4326) as palermo
)
SELECT 
    'Cartesian (flat)' as metric,
    ST_Distance(roma, palermo) as distance_degrees
FROM points
UNION ALL
SELECT 
    'Geodesic (sphere)' as metric,
    ST_Distance(roma::geography, palermo::geography) as distance_meters
FROM points;

-- Find the minimum convex polygon containing all satellite scenes over Tuscany
SELECT ST_AsText(
    ST_ConvexHull(
        ST_Collect(footprint)
    )
) as tuscany_convex_hull
FROM sentinel_scenes
WHERE ST_Intersects(
    footprint,
    ST_MakeEnvelope(10.0, 42.5, 11.5, 44.5, 4326)
);

-- All satellite scenes within 50km of the Rome-Florence path
WITH geodesic_path AS (
    SELECT ST_MakeLine(ARRAY[
        ST_SetSRID(ST_MakePoint(12.49, 41.90), 4326),  -- Roma
        ST_SetSRID(ST_MakePoint(11.88, 42.83), 4326),  -- Orvieto
        ST_SetSRID(ST_MakePoint(11.25, 43.77), 4326)   -- Firenze
    ])::geography as path
)
SELECT s.scene_id, s.datetime, s.grid_code
FROM sentinel_scenes s, geodesic_path gp
WHERE ST_DWithin(
    s.footprint::geography,
    gp.path,
    50000  -- 50km buffer
)
AND s.cloud_cover < 10
ORDER BY s.datetime DESC
LIMIT 20;

-- Find scenes with satellite passing from south to north over Rome
SELECT 
    scene_id,
    datetime,
    DEGREES(ST_Azimuth(
        ST_Centroid(footprint),
        ST_SetSRID(ST_MakePoint(12.49, 41.90), 4326)
    )) as bearing_to_rome
FROM sentinel_scenes
WHERE ST_Intersects(
    footprint,
    ST_SetSRID(ST_MakePoint(12.49, 41.90), 4326) -- Rome
)
LIMIT 10;

-- How similar is the footprint shape of two nearby satellite scenes?
WITH scene_pair AS (
    SELECT 
        s1.scene_id as id1,
        s2.scene_id as id2,
        s1.footprint as geom1,
        s2.footprint as geom2
    FROM sentinel_scenes s1, sentinel_scenes s2
    WHERE s1.grid_code = 'MGRS-32TQN'
    AND s2.grid_code = 'MGRS-32TQN'
    AND s1.scene_id < s2.scene_id
    LIMIT 1
)
SELECT 
    id1, id2,
    ST_HausdorffDistance(geom1, geom2) as shape_similarity
FROM scene_pair;

-- Find satellite scenes covering the midpoint between Naples and Bari
WITH midpoint AS (
    SELECT ST_LineInterpolatePoint(
        ST_MakeLine(  -- MakeLine vuole geometry, non geography
            ST_SetSRID(ST_MakePoint(14.25, 40.85), 4326),  -- Napoli
            ST_SetSRID(ST_MakePoint(16.87, 41.13), 4326)   -- Bari
        ),
        0.5  -- 50% lungo la linea
    ) as mid_point
)
SELECT s.scene_id, s.datetime, s.cloud_cover
FROM sentinel_scenes s, midpoint m
WHERE ST_Intersects(s.footprint, m.mid_point)
ORDER BY s.cloud_cover ASC
LIMIT 5;

-- Verify if footprints have consistent orientation (clockwise vs counterclockwise)
SELECT 
    scene_id,
    CASE 
        WHEN ST_IsPolygonCCW(footprint) THEN 'Counterclockwise'
        ELSE 'Clockwise'
    END as orientation,
    ST_Area(footprint::geography) / 1e6 as area_km2
FROM sentinel_scenes
LIMIT 10;

-- Simplify complex footprints while preserving topology
SELECT 
    scene_id,
    ST_NPoints(footprint) as original_vertices,
    ST_NPoints(
        ST_SimplifyPreserveTopology(footprint, 0.01)
    ) as simplified_vertices,
    ST_AsText(
        ST_SimplifyPreserveTopology(footprint, 0.01)
    ) as simplified_geom
FROM sentinel_scenes
WHERE ST_NPoints(footprint) > 10
LIMIT 5;

-- Select satellite scenes from the last summer
SELECT *  
  FROM sentinel_scenes s 
 WHERE to_char(s.datetime, 'MM-dd') BETWEEN '06-21' AND '09-23'   
   AND to_char(s.datetime, 'yyyy') = 
        CASE 
            WHEN EXTRACT(MONTH FROM CURRENT_DATE) < 6 
            THEN CAST(EXTRACT(YEAR FROM CURRENT_DATE) - 1 AS TEXT)
            ELSE CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS TEXT)
        END
;

-- Select visualizable satellite image
SELECT *
FROM scene_assets
WHERE asset_type = 'image/jpeg'
OR asset_key = 'thumbnail'
;