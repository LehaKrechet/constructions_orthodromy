import numpy as np
from pyproj import Geod
from shapely.geometry import LineString, Polygon

def circle(lat, lon, radius):
    geod = Geod(ellps='WGS84')
    center_lon, center_lan = lon, lat
    azimuths = np.linspace(0, 360, 120, endpoint=False)
    lons_center = [center_lon] * len(azimuths)
    lats_center = [center_lan] * len(azimuths)
    distances = [radius] * len(azimuths)
    circle_lons, circle_lats, _ = geod.fwd(lons_center, lats_center, azimuths, distances)
    coords = list(list(i) for i in zip(circle_lats, circle_lons))
    coords.append(coords[0])
    return coords

def intersection_line_circle(line, circle):
    """
    Пересекается ли круг и линия
    line_coords: [[lon1, lat1], [lon2, lat2], ...]
    polygon_coords: [[lon1, lat1], [lon2, lat2], ...]
    """
    line_geo = LineString(line)
    poly_geo = Polygon(circle)
    
    if line_geo.intersects(poly_geo):
        return True
    else:
        return False
