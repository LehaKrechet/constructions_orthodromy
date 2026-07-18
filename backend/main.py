import calculation_orthodrome as calculation_orthodrome
from flask import Flask, request, jsonify, redirect
import os
import bd as bd
import other_calculation as other_calculation
from pyproj import Geod

app = Flask(__name__)

@app.route('/')
def index():
    return redirect("http://127.0.0.1:4200")

@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Расчет ортодромии
    """
    try:
        data = request.get_json()
        
        lon1 = float(data['lon1'])
        lat1 = float(data['lat1'])
        lon2 = float(data['lon2'])
        lat2 = float(data['lat2'])
        points = int(data['points'])
        coord_mode = str(data.get('coordMode', 'WGS84'))

        match coord_mode:
            case 'WGS84':
                result_coords = calculation_orthodrome.wgs84(lon1, lat1, lon2, lat2, points)
            case 'CK-42':
                result_coords = calculation_orthodrome.ck_42(lon1, lat1, lon2, lat2, points)
            case 'Меркатор':
                result_coords = calculation_orthodrome.merkator(lon1, lat1, lon2, lat2, points)
        
        return jsonify({
            "status": "success",
            "coords": result_coords
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@app.route('/get_polygons', methods=['GET'])
def get_polygons():
    """
    Получение всех сохраненых полигонов
    """
    try:
        with bd.SessionLocal() as session:
            polygons = bd.get_polygons(session)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    return jsonify(polygons)

@app.route('/add_polygon', methods=['POST'])
def add_polygon():
    """
    Сохранение полигона
    """
    try:
        data = request.get_json()
        new_polygon = data['polygon']
        try:
            with bd.SessionLocal() as session:
            # 1. Добавление полигона
                bd.add_polygon(session, new_polygon)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Ошибка при добавлении полигона в базу данных: {str(e)}"
            }), 400
        
        return jsonify({
            "status": "success",
            "message": "Polygon added successfully."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 400
    
@app.route('/delete_polygon', methods=['POST'])
def delete_polygon():
    """
    Удаление сохраненного полигона
    """
    try:
        global polygons
        data = request.get_json()
        del_polygon = data['polygon']
        try:
            with bd.SessionLocal() as session:
                bd.delete_polygon(session, del_polygon)

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Ошибка при удалении полигона из базы данных: {str(e)}"
            }), 400
        
        return jsonify({
            "status": "success",
            "message": "Polygon deleted successfully."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@app.route('/update_all_polygons', methods=['POST'])
def update_all_polygons():
    """
    Удаление а затем добавление всех полигонов в базу
    """
    try:
        try:
            with bd.SessionLocal() as session:
                bd.delete_polygon(session, None)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Ошибка при удалении всех полигонов из базы данных: {str(e)}"
            }), 400
        
        data = request.get_json()
        new_polygons = data['polygons']
        try:
            with bd.SessionLocal() as session:
                bd.add_several_polygons(session, new_polygons)

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Ошибка при добавлении полигонов в базу данных: {str(e)}"
            }), 400
        
        return jsonify({
            "status": "success",
            "message": "Polygons updated successfully."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@app.route('/check_intersections', methods=['POST'])
def check_intersections():
    """
    Проверка пересечение ортодромии и зон запрета
    """
    try:
        data = request.get_json()
        line_coords = data['line_coords']
        with bd.SessionLocal() as session:

            result = bd.find_intersections_in_db(session, line_coords)
        
        return jsonify({
            "status": "success",
            "result": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@app.route('/get_circle', methods=['POST'])
def get_circle():
    """
    Получение исследуемой окружности
    """
    try:
        data = request.get_json()
        lon = float(data['lon'])
        lat = float(data['lat'])
        radius = float(data['radius'])
        coords = other_calculation.circle(lon, lat, radius)
        return jsonify({
            "status":'success',
            "coords": coords
        }), 200
    
    except Exception as e:
        return jsonify({
            "status":'error',
            "message": str(e)
        }), 400
    
@app.route('/add_orthodromy', methods=['POST'])
def add_orthodromy():
    """
    Сохранение сохраненной ортодромии
    """
    try:
        data = request.get_json()
        with bd.SessionLocal() as session:
            bd.add_orthodromy(session, data)
        return jsonify({
            'status': 'success',
            'message': 'Orthodromy added successfuly'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 400
    
@app.route('/delete_orthodromy', methods=['POST'])
def delete_orthodrome():
    """
    Удаление сохраненной ортодромии
    """
    try:
        data = request.get_json()
        with bd.SessionLocal() as session:
            bd.delete_orthodromy(session, data)
        return jsonify({
            'status':'success',
            'message': 'Delete othodromy'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    
@app.route('/get_orthodromy', methods=['GET'])
def get_orthodromy():
    """
    Построение все сохранненых ортодромий
    """
    try:
        with bd.SessionLocal() as session:
            result = bd.get_orthodromy(session)
        return jsonify({
            'status':'success',
            'coords': result
        }),200
    except Exception as e:
        return jsonify({
            'status':'error',
            'message': str(e)
        }),400
    
@app.route('/get_lines_intersection_circle', methods=['POST'])
def get_lines_intersection_circle():
    """
    Получение маршрутов пересекающих исследуемаю окружность
    """
    try:
        data = request.get_json()
        intersections=[]
        with bd.SessionLocal() as session:
            orthodromys = bd.get_orthodromy(session)
        for i in orthodromys: 
            if other_calculation.intersection_line_circle(i, data):
                intersections.append(i)
        return jsonify({
            'status':'success',
            'coords':intersections
        }),200
    
    except Exception as e:
        return jsonify({
            'status':'success',
            'message': str(e)
        }),400

@app.route('/calculate_safe_route', methods=['POST'])
def calculate_safe_route():
    """
    Построение безопасного маршрута в обход запретных зон
    """
    try:
        data = request.get_json()
        orthodrome_coords = data.get('orthodrome', [])

        start_lon = float(orthodrome_coords[0][1])
        start_lat = float(orthodrome_coords[0][0])
        end_lon = float(orthodrome_coords[-1][1])
        end_lat = float(orthodrome_coords[-1][0])

        
        buffer_distance = float(data.get('buffer_distance', 0.1))
        
        start = [start_lon, start_lat]
        end = [end_lon, end_lat]


        # Получаем запретные зоны из БД
        with bd.SessionLocal() as session:
            polygons = bd.get_polygons(session)

        orthodrome_coords_xy = [[pt[1], pt[0]] for pt in orthodrome_coords]
        if not polygons:
            # Если зон нет, возвращаем присланную ортодромию
            coords = orthodrome_coords_xy
            return jsonify({
                "status": "success",
                "coords": coords,
                "message": "No exclusion zones found. Frontend orthodrome returned."
            }), 200
        
        # Строим безопасный маршрут
        safe_path = other_calculation.build_smooth_path(
            start=start,
            end=end,
            polygons_coords=polygons,
            buffer_distance=buffer_distance
        )
        
        return jsonify({
            "status": "success",
            "coords": safe_path,
            "message": f"Route calculated successfully with {len(safe_path)} waypoints"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error calculating safe route: {str(e)}"
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)


