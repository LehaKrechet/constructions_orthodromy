from pyproj import CRS, Geod, Transformer


def wgs84(lon1, lat1, lon2, lat2, points):
    geod = Geod(ellps='WGS84')

    num_points = points
    intermediate_points = geod.npts(lon1, lat1, lon2, lat2, num_points)
    
    coords = [[lat1, lon1]]
    for pt in intermediate_points:
        coords.append([pt[1], pt[0]])
    coords.append([lat2, lon2])
    
    return coords

def ck_42(lon1, lat1, lon2, lat2, points):
    crs_ck42 = CRS.from_epsg(4284)
    geod = crs_ck42.get_geod()

    intermediate_points = geod.npts(lon1, lat1, lon2, lat2, points)
    
    to_wgs84 = Transformer.from_crs("EPSG:4284", "EPSG:4326", always_xy=True)
    
    coords = []
    
    lon1_wgs, lat1_wgs = to_wgs84.transform(lon1, lat1)
    coords.append([lat1_wgs, lon1_wgs])
    
    for pt in intermediate_points:
        lon_wgs, lat_wgs = to_wgs84.transform(pt[0], pt[1])
        coords.append([lat_wgs, lon_wgs])
        
    lon2_wgs, lat2_wgs = to_wgs84.transform(lon2, lat2)
    coords.append([lat2_wgs, lon2_wgs])
    
    return coords

def merkator(x1, y1, x2, y2, points):
    to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    
    lon1, lat1 = to_wgs84.transform(x1, y1)
    lon2, lat2 = to_wgs84.transform(x2, y2)

    geod = Geod(ellps='WGS84')
    intermediate_points = geod.npts(lon1, lat1, lon2, lat2, points)
    
    coords = [[lat1, lon1]]
    for pt in intermediate_points:
        coords.append([pt[1], pt[0]])
    coords.append([lat2, lon2])
    
    return coords
    