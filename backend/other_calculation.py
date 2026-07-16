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

    try:
        line_xy = line
        circle_xy = [[pt[1], pt[0]] for pt in circle]

        line_geo = LineString(line_xy)
        poly_geo = Polygon(circle_xy)
        
        return line_geo.intersects(poly_geo)
        
    except Exception as e:
        print(f"Ошибка при расчете пересечения: {e}")
        return False