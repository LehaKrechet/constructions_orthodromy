import os
import json
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, create_engine, literal
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_AsGeoJSON, ST_Transform, ST_Intersection, ST_Intersects, ST_Centroid, ST_DWithin

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ExclusionZone(Base):
    __tablename__ = 'exclusion_zones'
    
    id = Column(Integer, primary_key=True)
    # Создаем поле для геометрии с типом POLYGON и SRID 4326
    geom = Column(Geometry(geometry_type='POLYGON', srid=4326))


def _coords_to_wkt(polygon_coords):
    """Конвертирует массив [[lon, lat], ...] в формат WKT POLYGON"""
    # Делаем копию, чтобы не изменять оригинальный массив
    coords = list(polygon_coords)
    # Замыкаем полигон, если первая и последняя точки не совпадают
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    pts_str = ", ".join([f"{float(pt[0])} {float(pt[1])}" for pt in coords])
    return f"POLYGON(({pts_str}))"

    
def add_polygon(session: Session, polygon) -> bool:
    try:
        wkt = _coords_to_wkt(polygon)
        new_zone = ExclusionZone(geom=wkt)
        session.add(new_zone)
        session.commit()
        return True
    
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении полигона: {e}")
        return False

def add_several_polygons(session: Session, polygons) -> bool:
    try:
        zones = [ExclusionZone(geom=_coords_to_wkt(poly)) for poly in polygons]
        session.add_all(zones)  # Добавляем сразу весь список
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении нескольких полигонов: {e}")
        return False

def get_polygons(session: Session):
    try:
        # SELECT ST_AsGeoJSON(geom) FROM exclusion_zones;
        # Использование функций PostGIS через scalar()
        results = session.query(ST_AsGeoJSON(ExclusionZone.geom)).all()
        
        polygons = []
        for r in results:
            if not r[0]: continue
            geojson = json.loads(r[0])
            polygons.append(geojson['coordinates'][0])
        return polygons
    except Exception as e:
        print(f"Ошибка при получении полигонов: {e}")
        return []
    
def delete_polygon(session: Session, polygon=None) -> bool:
    try:
        if polygon is None:
            # Удалить все
            session.query(ExclusionZone).delete()
            session.commit()
            return True
        else:
            wkt = _coords_to_wkt(polygon)
            
            # Удаление по условию ST_DWithin над центроидами
            # Используем встроенные в GeoAlchemy функции PostGIS
            stmt = session.query(ExclusionZone).filter(
                ST_DWithin(
                    ST_Centroid(ExclusionZone.geom).cast(Geometry(geometry_type='GEOMETRY', srid=4326)),
                    ST_Centroid(wkt).cast(Geometry(geometry_type='GEOMETRY', srid=4326)),
                    0.1
                )
            )
            stmt.delete(synchronize_session=False)
            session.commit()
            return True
    except Exception as e:
        session.rollback()
        print(f"Ошибка при удалении полигона: {e}")
        return False

def find_intersections_in_db(session: Session, line_coords_lat_lon):
    if not line_coords_lat_lon or len(line_coords_lat_lon) < 2:
        return {"intersects": False, "intersected_parts": []}
        
    try:
        formatted_pts = [f"{float(pt[1])} {float(pt[0])}" for pt in line_coords_lat_lon]
        line_wkt = f"LINESTRING({', '.join(formatted_pts)})"
        
        # Строим сложный гео-запрос с трансформацией координат через ORM функции:
        # 1. Фильтруем зоны, которые вообще пересекаются с линией (ST_Intersects в WHERE)
        # 2. Выбираем ST_AsGeoJSON(ST_Transform(ST_Intersection(...), 4326))
        line_geom = literal(line_wkt).cast(Geometry(geometry_type='LINESTRING', srid=4326))
        
        query_result = session.query(
            ST_AsGeoJSON(
                ST_Transform(
                    ST_Intersection(
                        ST_Transform(ExclusionZone.geom, 3857), 
                        ST_Transform(line_geom, 3857)
                    ),
                    4326
                )
            )
        ).filter(
            ST_Intersects(ExclusionZone.geom, line_geom)
        ).all()

        intersected_parts = []
        
        for row in query_result:
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