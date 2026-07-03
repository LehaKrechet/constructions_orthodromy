from shapely.geometry import LineString, Polygon
from pyproj import Transformer

to_mercator = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

def find_intersections(line_coords_lat_lon, polygons_raw_lon_lat):

    if not line_coords_lat_lon or not polygons_raw_lon_lat:
        return {"intersects": False, "intersected_parts": []}
        
    try:
        intersected_parts = []
        
        line_points_merc = []
        for lat, lon in line_coords_lat_lon:
            x, y = to_mercator.transform(float(lon), float(lat))
            line_points_merc.append((x, y))
            
        if len(line_points_merc) < 2:
            return {"intersects": False, "intersected_parts": []}
            
        orthodrome_line = LineString(line_points_merc)
        
        for poly in polygons_raw_lon_lat:
            if len(poly) < 3:
                continue
                
            poly_points_merc = []
            for lon, lat in poly:
                x, y = to_mercator.transform(float(lon), float(lat))
                poly_points_merc.append((x, y))
                
            shapely_poly = Polygon(poly_points_merc)
            
            intersection = orthodrome_line.intersection(shapely_poly)
            
            if not intersection.is_empty:
                def merc_to_lat_lon(coords_list):
                    result = []
                    for x, y in coords_list:
                        lon, lat = to_wgs84.transform(x, y)
                        result.append([lat, lon])
                    return result

                if intersection.geom_type == 'LineString':
                    segment = merc_to_lat_lon(intersection.coords)
                    intersected_parts.append(segment)
                    
                elif intersection.geom_type == 'MultiLineString':
                    for line in intersection.geoms:
                        segment = merc_to_lat_lon(line.coords)
                        intersected_parts.append(segment)

        return {
            "intersects": len(intersected_parts) > 0,
            "intersected_parts": intersected_parts
        }
        
    except Exception as e:
        import traceback
        print("Ошибка внутри find_intersections")
        traceback.print_exc()
        raise e