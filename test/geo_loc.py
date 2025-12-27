import folium

# Bbox
bbox = [11.798012, 42.514816, 12.401342, 42.741971]
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
print("✓ Mappa salvata: bbox_map.html")