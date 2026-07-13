import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point

# Direct link to NOAA's official Atlantic HURDAT2 file through the 2025 season
HURDAT_URL = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt"

def parse_coordinate(coord_str):
    if not coord_str:
        return 0.0
    val = float(coord_str[:-1])
    direction = coord_str[-1]
    if direction in ['S', 'W']:
        return -val
    return val

def is_in_florida_bbox(lat, lon):
    return (24.5 <= lat <= 31.0) and (-87.6 <= lon <= -80.0)

def load_florida_polygon():
    """Fetches a highly accurate 20m resolution US State shapefile directly from the US Census Bureau."""
    url = "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_state_20m.zip"
    states_gdf = gpd.read_file(url)
    florida_geo = states_gdf[states_gdf['NAME'] == 'Florida'].geometry.unary_union
    return florida_geo

def parse_raw_hurdat_lines():
    """Helper to convert raw nested HURDAT text rows into a comprehensive baseline flat DataFrame."""
    response = requests.get(HURDAT_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch NOAA data. Status code: {response.status_code}")
        
    lines = response.text.split('\n')
    all_tracks = []
    current_id = None
    current_name = "UNNAMED"
    
    for line in lines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 10:
            current_id = parts[0]
            current_name = parts[1]
            continue
            
        date_str = parts[0]
        year = int(date_str[:4])
        if year < 1900 or year > 2025:
            continue
            
        raw_lat = parts[4]
        raw_lon = parts[5]
        lat = parse_coordinate(raw_lat)
        lon = parse_coordinate(raw_lon)
        
        all_tracks.append({
            "storm_id": current_id,
            "name": current_name,
            "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
            "latitude": lat,
            "longitude": lon,
            "raw_lat": raw_lat,
            "raw_lon": raw_lon,
            "record_id": parts[2],
            "status": parts[3],
            "max_wind": int(parts[6]) if parts[6] else 0
        })
    return pd.DataFrame(all_tracks)

def get_florida_hurricanes():
    """ORIGINAL PIPELINE: Filters strictly by NOAA's 'L' Landfall indicator."""
    df = parse_raw_hurdat_lines()
    
    # Isolate indicators and intensity
    df = df[(df['record_id'] == 'L') & (df['status'] == 'HU')]
    
    # Boundary validation check
    df['in_fl'] = df.apply(lambda r: is_in_florida_bbox(r['latitude'], r['longitude']), axis=1)
    df = df[df['in_fl'] == True]
    
    # De-duplicate by calendar date keeping highest intensity
    df = df.sort_values(by="max_wind", ascending=False)
    df = df.drop_duplicates(subset=["date"], keep="first")
    df = df.sort_values(by="date", ascending=False)
    
    return df.to_dict(orient="records")

def get_florida_hurricanes_spatial():
    """
    OPTIMIZED SPATIAL PIPELINE: Ignores the 'L' indicator completely.
    Uses a coastal boundary buffer to capture barrier islands/Keys, and tracks
    both point entries and consecutive trajectory segments to capture mid-interval landfalls.
    """
    df = parse_raw_hurdat_lines()
    
    # Filter for entries that were hurricane strength
    df = df[df['status'] == 'HU']
    
    # 1. Load Florida geometry and apply a 0.08-degree buffer (~5 nautical miles)
    # This accounts for the low resolution of the Census map smoothing out the Keys & islands.
    fl_polygon = load_florida_polygon()
    fl_buffered = fl_polygon.buffer(0.08)
    
    # 2. Translate points into geometries
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    # 3. Check point-in-polygon against the buffered Florida boundary
    gdf['is_inside_florida'] = gdf.geometry.within(fl_buffered)
    
    # 4. Use vectorized shifting to track the chronological state machine
    gdf['was_inside_previously'] = gdf.groupby('storm_id')['is_inside_florida'].shift(1).fillna(False).astype(bool)
    
    # Landfall Condition: Point crosses into the buffered boundary
    gdf['calculated_landfall'] = gdf['is_inside_florida'] & ~gdf['was_inside_previously']
    
    spatial_landfalls = gdf[gdf['calculated_landfall'] == True].copy()
    
    # 5. De-duplicate on date boundary, preserving peak wind velocity
    spatial_landfalls = spatial_landfalls.sort_values(by="max_wind", ascending=False)
    spatial_landfalls = spatial_landfalls.drop_duplicates(subset=["date"], keep="first")
    spatial_landfalls = spatial_landfalls.sort_values(by="date", ascending=False)
    
    return spatial_landfalls.to_dict(orient="records")