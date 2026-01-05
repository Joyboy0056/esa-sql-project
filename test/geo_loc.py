import folium

from build.config import config
from src.logger import logger

# Bbox
bbox = config.default_bbox
min_lon, min_lat, max_lon, max_lat = bbox

# Centro mappa
center_lat = (min_lat + max_lat) / 2
center_lon = (min_lon + max_lon) / 2

# Crea mappa
m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

# Aggiungi rettangolo
folium.Rectangle(
    bounds=[[min_lat, min_lon], [max_lat, max_lon]],
    color='red',
    fill=True,
    fillOpacity=0.2,
    popup='Area ricerca Sentinel-2'
).add_to(m)

# Salva
m.save('test/bbox_map.html')
logger.info("✓ Mappa salvata: bbox_map.html")