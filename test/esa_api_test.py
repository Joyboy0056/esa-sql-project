import requests
import json

from src.logger import logger

response = requests.post(
    "https://catalogue.dataspace.copernicus.eu/stac/search",
    json={
        "collections": ["sentinel-2-l2a"],
        "bbox": [11.798, 42.515, 12.401, 42.742],
        # "datetime": "2024-06-01T00:00:00Z/2024-06-30T23:59:59Z",
        "limit": 5
    }
)

data: dict = response.json()
print(f"\nDATA fields:  {data.keys()}")

print(f"\nFeatures live in a list of len={len(data['features'])}:")
for feat in data['features']:
    print(feat.keys())


print(f"\nFound: {data['numberReturned']} scenes in `features`")

# Vedi struttura primo risultato
if data['features']:
    feature = data['features'][0]
    print("\nCampi disponibili:")
    print(f"ID: {feature['id']}")

    property_keys = list(feature['properties'].keys())
    geometry_keys = list(feature['geometry'].keys())
    assets_keys = list(feature['assets'].keys())
    collection_keys = list(feature['collection'])

    print(f"\nProperties keys: {len(property_keys)}\n{property_keys}")
    print(f"\nGeometry keys: {len(geometry_keys)}\n{geometry_keys}")
    print(f"\nAssets keys: {len(assets_keys)}\n{assets_keys}")
    print(f"\nCollection keys: {len(collection_keys)}\n{collection_keys}")
    # print(f"\nPrimo feature completo:")
    # print(json.dumps(feature, indent=2)[:1000])  # Prime 1000 chars