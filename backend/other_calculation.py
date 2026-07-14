import numpy as np
from pyproj import Geod

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
