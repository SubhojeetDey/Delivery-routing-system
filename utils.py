from fastapi import HTTPException,Depends
from datetime import datetime
import requests,getapis,random,inference,models
from scipy.spatial.distance import cdist
from clustering import get_k_nearest_hierarchical_up,df,Z
import pandas as pd
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from typing_extensions import Annotated

db_dependency = Annotated[Session,Depends(get_db)]

hubs = {
    "Kolkata/Howrah (Port & Rail)": [22.5726, 88.3639],
    "Durgapur/Asansol (Industrial)": [23.5204, 87.3119],
    "Siliguri (North Bengal Gateway)": [26.7271, 88.3953],
    "Haldia (Port)": [22.0667, 88.0698],
    "Kharagpur (Rail/Highway Hub)": [22.3302, 87.3237]
}

def get_coordinates(pincode):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": f"{pincode}, India",
        "format": "json"
    }

    headers = {
        "User-Agent": "my-app"
    }

    res = requests.get(url, params=params, headers=headers)
    data = res.json()

    lat = data[0]["lat"]
    lon = data[0]["lon"]
    return lat, lon

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c

def is_pincode_in_radius(pincode, center_lat, center_lon, radius_km):
    lat, lon = get_coordinates(pincode)

    distance = haversine(center_lat, center_lon, lat, lon)
    return distance <= radius_km

def get_nearest_hub(pincode,hubs):
    for key,value in hubs.items():
        lat = value[0]
        lon = value[1]
        is_avialable = is_pincode_in_radius(pincode,lat,lon,15)
        if is_avialable:
            return key,lat,lon
    raise HTTPException(status_code=400,detail="Invalid Pincode.")

def get_nearest_warehouse(pincode,hub):
    df = pd.read_csv("west_bengal_warehouses.csv")
    Nearest_Hub,cen_lat,cen_lon = get_nearest_hub(pincode,hub)
    center_lat,center_lon = get_coordinates(pincode)
    warehouse = df[df['Nearest_Hub']==Nearest_Hub]
    w_coordinates = warehouse[['Warehouse_ID','Latitude','Longitude']]
    w_coordinates_array = np.array(w_coordinates)
    min_distance = None
    for i in w_coordinates_array:
        lat = i[1]
        lon = i[2]
        distance = haversine(float(center_lat), float(center_lon), lat, lon)
        if min_distance is None:
            min_distance = distance
            id = i
        if min_distance > distance:
            min_distance = distance
            id = i
    warehouse = {"warehouse_id":id[0],"co-ordinates":f"{id[1]},{id[2]}"}
    hub = {"hub":Nearest_Hub,"lat":center_lat,"lon":center_lon}
    return warehouse,hub

def get_weekday():
    day = datetime.now().strftime("%A")
    if day == "Sunday" or day == "Saturday":
        return "Weekend"
    else:
        return "Weekday"
    
def get_part_of_day():
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Morning Peak"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening Peak"
    else:
        return "Night"

def get_path_coordinates(source,destination):
    url = f"http://router.project-osrm.org/route/v1/driving/{source};{destination}"
    params = {
        "alternatives": "true", # Get alternative routes
        "geometries": "geojson",
        "overview": "full"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['code'] == 'Ok':
        print(f"Found {len(data['routes'])} routes:")
        min_distance = None
        min_time = None
        part_of_day = get_part_of_day()
        weekday = get_weekday()
        for i, route in enumerate(data['routes']):
            distance = route['distance'] / 1000 # Convert to km
            duration = route['duration'] / 60  
            path_coordinates = data['routes'][i]['geometry']['coordinates']
            random_coordinates = random.choice(path_coordinates)
            lat = random_coordinates[0]
            lon = random_coordinates[1] # Convert to minutes
            weather = getapis.get_forecast(lat,lon)
            try:
                traffic_density = getapis.get_traffic(lat,lon)
            except:
                raise HTTPException(status_code=401,detail="Invalid Request")
            
            config={"distance_km":distance,"time_of_day":part_of_day,
                    "day_of_week": weekday,"weather_condition": weather,
                    "traffic_density_level": traffic_density,"road_type": "Highway","average_speed_kmph": 60
                }
            time = inference.prediction(config)
            if min_time is None:
                min_time = time
                id = i
            if min_time > time:
                min_time=time
                id = i
        return data['routes'][i]
            # if min_distance is None:
            #     min_distance = distance
            #     id = i
            # if min_distance > distance:
            #     min_distance = distance
            #     id = i

def get_cluster(warehouse_id:str):
    w_cluster = get_k_nearest_hierarchical_up(warehouse_id,3,df,Z)
    return w_cluster

def compare_warehouse_capacity(warehouse_id:str):
    w_cluster = get_cluster(warehouse_id)
    warehouse_capacity = df[df['Warehouse_ID']==warehouse_id]['capacity'].iloc[0]
    if warehouse_capacity < 200:
        w_nearest = w_cluster[w_cluster['capacity']>500]
        return w_nearest.sample(1)
    return None

def get_delivery_warehouses(hub,db:Session):
    routes = db.execute(
        select(DeliveryRoute).where(DeliveryRoute.hub == hub)
    ).scalars().first()
    print(routes)
    warehouse_array = []
    distance_matrix = []
    for i in paths:
        warehouse = i.nearest_warehouse['warehouse_id']
        co_ordinates = i.nearest_warehouse['co-ordinates']
        warehouse_array.append([warehouse,co_ordinates])
    for i in warehouse_array:
        matrix = []
        for j in warehouse_array:
            source_coordinates = i[1].split(',')
            s_lat = float(source_coordinates[0])
            s_lon = float(source_coordinates[1])
            d_coordinates = j[1].split(',')
            d_lat = float(d_coordinates[0])
            d_lon = float(d_coordinates[1])
            distance = haversine(s_lat,s_lon,d_lat,d_lon)
            matrix.append(distance)
        distance_matrix.append(matrix)
    return distance_matrix

# print(get_delivery_warehouses("Kolkata/Howrah (Port & Rail)",db_dependency))






    
