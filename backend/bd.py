import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def db_exec(cmd, args=None):
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    try:
        cur.execute(cmd, args)
        if cur.description: 
            rows = cur.fetchall()
            conn.commit()
            return rows
        else:
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка выполнения запроса: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def _coords_to_wkt(polygon_coords):
    """Конвертирует массив [[lon, lat], ...] в формат WKT POLYGON"""
    # Делаем копию, чтобы не изменять оригинальный массив
    coords = list(polygon_coords)
    # Замыкаем полигон, если первая и последняя точки не совпадают
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    pts_str = ", ".join([f"{float(pt[0])} {float(pt[1])}" for pt in coords])
    return f"POLYGON(({pts_str}))"

def add_polygon(polygon):
    try:
        wkt = _coords_to_wkt(polygon)
        cmd = "INSERT INTO exclusion_zones (geom) VALUES (ST_GeomFromText(%s, 4326));"
        return db_exec(cmd, (wkt,))
    except Exception as e:
        print(f"Ошибка при добавлении полигона: {e}")
        return False

def add_several_polygons(polygons):
    try:
        placeholders = ", ".join(["(ST_GeomFromText(%s, 4326))"] * len(polygons))
        query = f"INSERT INTO exclusion_zones (geom) VALUES {placeholders};"
        flat_args = [_coords_to_wkt(poly) for poly in polygons]
        return db_exec(query, flat_args)
    except Exception as e:
        print(f"Ошибка при добавлении нескольких полигонов: {e}")
        return False

def get_polygons():
    try:
        cmd = "SELECT ST_AsGeoJSON(geom::geometry) FROM exclusion_zones;"
        rows = db_exec(cmd)
        
        polygons = []
        for row in rows:
            if not row[0]: continue
            geojson = json.loads(row[0])
            polygons.append(geojson['coordinates'][0])
        return polygons
    except Exception as e:
        print(f"Ошибка при получении полигонов: {e}")
        return []
    
def delete_polygon(polygon=None):
    try:
        if polygon is None:
            cmd = "DELETE FROM exclusion_zones;"
            return db_exec(cmd)
        else:
            wkt = _coords_to_wkt(polygon)
            # Сравниваем центроиды полигонов 
            cmd = """
                DELETE FROM exclusion_zones 
                WHERE ST_DWithin(
                    ST_Centroid(geom::geometry)::geography, 
                    ST_Centroid(ST_GeomFromText(%s, 4326))::geography, 
                    0.1
                );
            """
            return db_exec(cmd, (wkt,))
    except Exception as e:
        print(f"Ошибка при удалении полигона: {e}")
        return False

def find_intersections_in_db(line_coords_lat_lon):
    if not line_coords_lat_lon or len(line_coords_lat_lon) < 2:
        return {"intersects": False, "intersected_parts": []}
        
    try:
        # Из Leaflet приходят [lat, lon]. Для WKT переводим в формат: lon lat (WGS84)
        formatted_pts = []
        for pt in line_coords_lat_lon:
            lat = float(pt[0])
            lon = float(pt[1])
            formatted_pts.append(f"{lon} {lat}")
            
        line_wkt = f"LINESTRING({', '.join(formatted_pts)})"
        
        # 1. Переводим исходный полигон (geom) из 4326 в Меркатор (3857) -> ST_Transform(geom::geometry, 3857)
        # 2. Переводим входную линию из 4326 в Меркатор (3857) -> ST_Transform(ST_GeomFromText(%s, 4326), 3857)
        # 3. Считаем их пересечение на плоскости Меркатора
        # 4. Результат пересечения переводим ОБРАТНО в WGS84 (4326), чтобы вернуть клиенту
        cmd = """
            SELECT ST_AsGeoJSON(
                ST_Transform(
                    ST_SnapToGrid(
                        ST_Intersection(
                            ST_Transform(geom::geometry, 3857), 
                            ST_Transform(ST_GeomFromText(%s, 4326), 3857)
                        ), 
                        0.01
                    ),
                    4326
                )
            ) 
            FROM exclusion_zones 
            WHERE ST_Intersects(geom::geometry, ST_GeomFromText(%s, 4326));
        """
        
        rows = db_exec(cmd, (line_wkt, line_wkt))
        intersected_parts = []
        
        if rows:
            for row in rows:
                if not row[0]: continue
                geojson = json.loads(row[0])
                
                if geojson['type'] == 'LineString':
                    segment = [[pt[1], pt[0]] for pt in geojson['coordinates']]
                    intersected_parts.append(segment)
                    
                elif geojson['type'] == 'MultiLineString':
                    for line in geojson['coordinates']:
                        segment = [[pt[1], pt[0]] for pt in line]
                        intersected_parts.append(segment)
                        
                elif geojson['type'] == 'GeometryCollection':
                    for geom in geojson['geometries']:
                        if geom['type'] in ['LineString', 'MultiLineString']:
                            lines = [geom['coordinates']] if geom['type'] == 'LineString' else geom['coordinates']
                            for line in lines:
                                segment = [[pt[1], pt[0]] for pt in line]
                                intersected_parts.append(segment)
                        
        return {
            "intersects": len(intersected_parts) > 0,
            "intersected_parts": intersected_parts
        }
    except Exception as e:
        print(f"Ошибка при поиске пересечений в БД: {e}")
        return {"intersects": False, "intersected_parts": []}