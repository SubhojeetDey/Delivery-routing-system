import pandas as pd
import numpy as np

# Define major logistics hubs in West Bengal (Lat, Long)
hubs = {
    "Kolkata/Howrah (Port & Rail)": [22.5726, 88.3639],
    "Durgapur/Asansol (Industrial)": [23.5204, 87.3119],
    "Siliguri (North Bengal Gateway)": [26.7271, 88.3953],
    "Haldia (Port)": [22.0667, 88.0698],
    "Kharagpur (Rail/Highway Hub)": [22.3302, 87.3237]
}

def generate_warehouses(n_points=200):
    data = []
    points_per_hub = n_points // len(hubs)
    
    for hub_name, coords in hubs.items():
        # Generate points around the hub using a normal distribution
        
        lats = np.random.normal(coords[0], 0.12, points_per_hub)
        lons = np.random.normal(coords[1], 0.12, points_per_hub)
        
        for lat, lon in zip(lats, lons):
            data.append({
                "Warehouse_ID": f"WH_{len(data)+1:03d}",
                "Nearest_Hub": hub_name,
                "Latitude": round(lat, 6),
                "Longitude": round(lon, 6),
                'capacity': np.random.randint(500, 2000)
            })
            
    return pd.DataFrame(data)


df_warehouses = generate_warehouses(200)


df_warehouses.to_csv("west_bengal_warehouses.csv", index=False)