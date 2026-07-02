import calculation as calculation
from flask import Flask, request, jsonify, send_from_directory
import os

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

        print(coord_mode)
        match coord_mode:
            case 'WGS84':
                result_coords = calculation.wgs84(lon1, lat1, lon2, lat2, points)
            case 'CK-42':
                result_coords = calculation.ck_42(lon1, lat1, lon2, lat2, points)
            case 'Меркатор':
                result_coords = calculation.merkator(lon1, lat1, lon2, lat2, points)
    
        
        return jsonify({
            "status": "success",
            "coords": result_coords
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
