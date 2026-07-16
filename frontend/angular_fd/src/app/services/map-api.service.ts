import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MapApiService {
  private baseUrl = ''; 

  constructor(private http: HttpClient) {}

  calculateOrthodrome(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/calculate`, payload);
  }

  getPolygons(): Observable<number[][][]> {
    return this.http.get<number[][][]>(`${this.baseUrl}/get_polygons`);
  }

  addPolygon(polygon: number[][]): Observable<any> {
    return this.http.post(`${this.baseUrl}/add_polygon`, { polygon });
  }

  deletePolygon(polygon: number[][]): Observable<any> {
    return this.http.post(`${this.baseUrl}/delete_polygon`, { polygon });
  }

  updateAllPolygons(polygons: number[][][]): Observable<any> {
    return this.http.post(`${this.baseUrl}/update_all_polygons`, { polygons });
  }

  checkIntersections(lineCoords: number[][]): Observable<any> {
    return this.http.post(`${this.baseUrl}/check_intersections`, { line_coords: lineCoords });
  }

  get_circle(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/get_circle`, payload);
  }

  add_orthodromy(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/add_orthodromy`, payload);
  }

  delete_orthodromy(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/delete_orthodromy`, payload);
  }

  get_orthodromy(): Observable<any> {
    return this.http.get(`${this.baseUrl}/get_orthodromy`);
  }

  get_lines_intersection_circle(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/get_lines_intersection_circle`, payload);
  }

}