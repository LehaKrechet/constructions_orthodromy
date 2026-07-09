import calculation_orthodrome as calculation_orthodrome
import calculation_polygon as calculation_polygon
from flask import Flask, request, jsonify, send_from_directory
import os
import bd as bd

app = Flask(__name__)

@app.route('/')
def index():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    frontend_dir = os.path.abspath(os.path.join(current_dir, '..', 'frontend'))

    return send_from_directory(frontend_dir, 'index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
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
    try:
        polygons = bd.get_polygons()
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    return jsonify(polygons)

@app.route('/add_polygon', methods=['POST'])
def add_polygon():
    try:
        data = request.get_json()
        new_polygon = data['polygon']
        try:
            bd.add_polygon(new_polygon)
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
    try:
        global polygons
        data = request.get_json()
        del_polygon = data['polygon']
        try:
            bd.delete_polygon(del_polygon)
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
    try:
        try:
            bd.delete_polygon()
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Ошибка при удалении всех полигонов из базы данных: {str(e)}"
            }), 400
        
        data = request.get_json()
        new_polygons = data['polygons']
        try:
            bd.add_several_polygons(new_polygons)

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
    try:
        data = request.get_json()
        line_coords = data['line_coords']
        
        result = bd.find_intersections_in_db(line_coords)
        
        return jsonify({
            "status": "success",
            "result": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
