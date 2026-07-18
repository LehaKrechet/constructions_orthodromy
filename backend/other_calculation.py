import numpy as np
from pyproj import Geod
from shapely.geometry import LineString, Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import math
import time

def circle(lat, lon, radius):
    '''
    Расчет георграфически верной окружности на поверхности земли
    '''
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
    '''
    Расчет пересечения линии и круга 
    '''

    try:
        line_xy = line
        circle_xy = [[pt[1], pt[0]] for pt in circle]

        line_geo = LineString(line_xy)
        poly_geo = Polygon(circle_xy)
        
        return line_geo.intersects(poly_geo)
        
    except Exception as e:
        print(f"Ошибка при расчете пересечения: {e}")
        return False
    
def build_smooth_path(start, end, polygons_coords, max_turn_angle=30.0, buffer_distance=0.02):
    """
    Построение безопасного маршрута, огибающего запретные зоны строго по контуру 
    и мгновенно возвращающегося на линию ортодромии
    """
    start_time = time.time()
    
    start = list(start)
    end = list(end)
    
    # 1. Формируем реальные геозоны препятствий
    raw_obstacles = []
    for poly in polygons_coords:
        if len(poly) > 2:
            if poly[0] != poly[-1]:
                poly = list(poly) + [poly[0]]
            p = Polygon(poly)
            if p.is_valid:
                raw_obstacles.append(p)
                
    if not raw_obstacles:
        return get_orthodrome_points(start, end, 100)
        
    base_obstacles = unary_union(raw_obstacles)
    
    # 2. Базовая ортодромия (высокая плотность точек для точности)
    ortho_points = get_orthodrome_points(start, end, 300)
    ortho_line = LineString(ortho_points)
    
    # Если пересечений нет — сразу возвращаем чистый путь
    if not ortho_line.intersects(base_obstacles):
        print("Препятствий на пути нет.")
        return ortho_points

    # 3. Формируем безопасную зону обхода (буфер безопасности)
    graph_obstacles = base_obstacles.buffer(buffer_distance * 1.3)
    
    if isinstance(graph_obstacles, Polygon):
        obs_list = [graph_obstacles]
    elif isinstance(graph_obstacles, MultiPolygon):
        obs_list = list(graph_obstacles.geoms)
    else:
        obs_list = []

    # 4. Находим точные точки пересечения ортодромии с внешними границами буферов
    intersection_nodes = []
    for obs in obs_list:
        inter = ortho_line.intersection(obs.exterior)
        if not inter.is_empty:
            if isinstance(inter, Point):
                intersection_nodes.append(list(inter.coords[0]))
            elif hasattr(inter, 'geoms'):
                for geom in inter.geoms:
                    if isinstance(geom, Point):
                        intersection_nodes.append(list(geom.coords[0]))

    # 5. Собираем только «разрешенные» точки исходной ортодромии (снаружи буферов)
    valid_ortho_nodes = []
    for pt in ortho_points:
        if not graph_obstacles.contains(Point(pt)):
            valid_ortho_nodes.append(pt)

    # 6. Формируем массив узлов графа
    graph_nodes = [start] + valid_ortho_nodes + intersection_nodes
    
    for obs in obs_list:
        if ortho_line.intersects(obs):
            for pt in list(obs.exterior.coords)[:-1]:
                graph_nodes.append(list(pt))
    graph_nodes.append(end)
    
    # Очистка от дубликатов
    unique_nodes = []
    for node in graph_nodes:
        if node not in unique_nodes:
            unique_nodes.append(node)
            
    # Сортировка по дистанции от Старта
    unique_nodes.sort(key=lambda p: calculate_distance(start, p))
    if unique_nodes[-1] != end:
        unique_nodes.append(end)

    # 7. Построение матрицы смежности (Visibility Graph)
    num_nodes = len(unique_nodes)
    adj_matrix = {i: {} for i in range(num_nodes)}
    
    for i in range(num_nodes):
        for j in range(i + 1, min(i + 40, num_nodes)):
            p1, p2 = unique_nodes[i], unique_nodes[j]
            segment = LineString([p1, p2])
            
            if not segment.intersects(base_obstacles):
                mid_pt = Point((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                if not base_obstacles.contains(mid_pt):
                    adj_matrix[i][j] = calculate_distance(p1, p2)

    # 8. Алгоритм Дейкстры
    distances = {i: float('inf') for i in range(num_nodes)}
    distances[0] = 0
    previous = {i: None for i in range(num_nodes)}
    unvisited = set(range(num_nodes))
    
    while unvisited:
        current = min(unvisited, key=lambda node: distances[node])
        if distances[current] == float('inf') or current == (num_nodes - 1):
            break
        unvisited.remove(current)
        
        for neighbor, weight in adj_matrix[current].items():
            alt = distances[current] + weight
            if alt < distances[neighbor]:
                distances[neighbor] = alt
                previous[neighbor] = current

    # Восстановление ломаной Дейкстры
    path_nodes = []
    curr = num_nodes - 1
    while curr is not None:
        path_nodes.append(unique_nodes[curr])
        curr = previous[curr]
    path_nodes.reverse()
    
    if path_nodes[0] != start or path_nodes[-1] != end:
        print("Ошибка связности, возврат базового трека")
        return ortho_points

    filtered_nodes = [path_nodes[0]]
    i = 1
    while i < len(path_nodes) - 1:
        p_prev = np.array(filtered_nodes[-1])
        p_curr = np.array(path_nodes[i])
        p_next = np.array(path_nodes[i+1])
        
        # Вычисляем угол излома в этой вершине
        angle = get_angle(p_prev, p_curr, p_next)
        
        # Вычисляем расстояние между точками
        d1 = calculate_distance(p_prev, p_curr)
        d2 = calculate_distance(p_curr, p_next)
        
        is_on_ortho_prev = ortho_line.distance(Point(p_prev)) < 0.0001
        is_on_ortho_next = ortho_line.distance(Point(p_next)) < 0.0001
        
        # Если это микро-сегмент на стыке ортодромии, просто перешагиваем через него (схлопываем ступеньку)
        if (d1 < 0.005 or d2 < 0.005) and (is_on_ortho_prev or is_on_ortho_next):
            # Проверяем, безопасен ли прямой срез без этой точки
            direct_segment = LineString([p_prev, p_next])
            if not direct_segment.intersects(base_obstacles):
                i += 1
                continue
                
        # Если угол поворота микроскопический (< 3 градусов), вершина избыточна
        if angle < 3.0:
            direct_segment = LineString([p_prev, p_next])
            if not direct_segment.intersects(base_obstacles):
                i += 1
                continue
                
        filtered_nodes.append(path_nodes[i])
        i += 1
    filtered_nodes.append(path_nodes[-1])

    # 9. Скругление углов:
    smooth_path = generate_safe_smooth_turns(filtered_nodes, base_obstacles, max_turn_angle, step=0.004)

    # 10. Восстановление геодезической кривизны ортодромии на прямых чистых участках
    dense_path = densify_orthodrome_segments(smooth_path, ortho_line)

    # 11. Равномерный ресемплинг для красивого точечного/пунктирного рендеринга
    final_path = resample_path(dense_path, step=0.004)

    print(f"Маршрут успешно оптимизирован за {time.time() - start_time:.3f} сек.")
    return final_path


def generate_safe_smooth_turns(waypoints, base_obstacles, max_turn_angle, step=0.004):
    """
    Безопасное скругление углов квадратичными кривыми Безье.
    """
    if len(waypoints) < 3:
        return waypoints

    # Максимальный излом на одну хорду дуги: достаточно мелкий, чтобы линия
    # выглядела гладкой, и не крупнее разрешённого max_turn_angle.
    per_chord = max(0.25, min(180, max_turn_angle))

    final_path = [waypoints[0]]

    for i in range(1, len(waypoints) - 1):
        p1 = np.array(waypoints[i-1])
        p2 = np.array(waypoints[i])
        p3 = np.array(waypoints[i+1])

        angle = get_angle(p1, p2, p3)

        # Если угол изменения курса микроскопический, скругление не требуется
        if angle < 1.5:
            final_path.append(waypoints[i])
            continue

        v1 = p1 - p2
        v2 = p3 - p2
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            final_path.append(waypoints[i])
            continue

        v1_u = v1 / norm_v1
        v2_u = v2 / norm_v2

        # Коэффициент 0.40 гарантирует, что скругления не наложатся друг на друга,
        # но при этом дуга будет максимально широкой и плавной.
        max_shift = min(norm_v1 * 0.40, norm_v2 * 0.40)
        shift_dist = max_shift

        valid_turn_points = None

        # Сжимаем дугу Безье к углу только в случае, если она пересекает реальную зону
        while shift_dist > 0.0001:
            start_turn = p2 + v1_u * shift_dist
            end_turn = p2 + v2_u * shift_dist

            num_segments = min(180, max(12, int(math.ceil(angle / per_chord))))
            temp_turn = []

            for t in np.linspace(0, 1, num_segments):
                pt = (1-t)**2 * start_turn + 2*(1-t)*t * p2 + t**2 * end_turn
                temp_turn.append(pt.tolist())

            turn_line = LineString(temp_turn)
            if not turn_line.intersects(base_obstacles):
                valid_turn_points = temp_turn
                break

            shift_dist *= 0.75

        if valid_turn_points is not None:
            final_path.extend(valid_turn_points)
        else:
            final_path.append(waypoints[i])

    final_path.append(waypoints[-1])
    return final_path


def densify_orthodrome_segments(path, ortho_line, ortho_tol=1e-6, spacing=0.01):
    """
    Восстанавливает геодезическую кривизну на длинных прямых участках,
    лежащих строго на исходной ортодромии.
    """
    if len(path) < 2:
        return path
    dense = [list(path[0])]
    for i in range(1, len(path)):
        a, b = path[i-1], path[i]
        gap = calculate_distance(a, b)
        if (gap > spacing
                and ortho_line.distance(Point(a)) < ortho_tol
                and ortho_line.distance(Point(b)) < ortho_tol):
            n = max(2, int(gap / spacing))
            dense.extend(get_orthodrome_points(a, b, n)[1:-1])
        dense.append(list(b))
    return dense


def resample_path(path, step=0.004):
    """Равномерный ресемплинг пути с шагом step (линейная интерполяция)."""
    if len(path) < 2:
        return path
    out = [list(path[0])]
    for i in range(1, len(path)):
        a = np.array(out[-1])
        b = np.array(path[i])
        d = np.linalg.norm(b - a)
        if d > step:
            n = int(math.ceil(d / step))
            for s in range(1, n):
                out.append((a + (b - a) * (s / n)).tolist())
        out.append(list(path[i]))
    return out

def get_orthodrome_points(start, end, num_points=100):
    geod = Geod(ellps='WGS84')
    try:
        npts = geod.npts(start[0], start[1], end[0], end[1], num_points)
        points = [start] + list(npts) + [end]
        return [list(pt) for pt in points]
    except:
        return [list(start), list(end)]

def calculate_distance(p1, p2):
    return np.hypot(p2[0] - p1[0], p2[1] - p1[1])

def get_angle(p1, p2, p3):
    v1 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0: return 0.0
    cos_angle = np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))

