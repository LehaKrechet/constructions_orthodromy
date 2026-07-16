import { Component, OnInit, OnDestroy } from '@angular/core';
import { MapApiService } from '../../services/map-api.service';
import { MapStateService } from '../../services/map-state.service';
import { Subscription } from 'rxjs';
import * as L from 'leaflet';
import 'leaflet-draw';

@Component({
  selector: 'app-map-view',
  standalone: true,
  template: `<div id="map"></div>`,
  styleUrls: ['./map-view.component.css']
})
export class MapViewComponent implements OnInit, OnDestroy {
  private map!: L.Map;
  private drawnItems = new L.FeatureGroup();
  private currentPolyline: L.Polyline | null = null;
  private currentCircle: L.Polygon | null = null;
  private intersectionLayers: L.Polyline[] = [];
  private rawPolygonsData: number[][][] = [];
  private lastParams: any = null;
  private sub!: Subscription;
  private orthodromy_line: number[][] = [];
  private selectSub!: Subscription;

  constructor(
    private apiService: MapApiService,
    private mapStateService: MapStateService
  ) {}

  ngOnInit() {
    this.initMap();
    this.loadPolygons();

    // Слушаем клики из сайдбара
    this.sub = this.mapStateService.calculate$.subscribe(params => {
      this.lastParams = params;
      this.updateOrthodrome();
    });

    this.sub = this.mapStateService.calculateCitrle.subscribe(params => {
      this.lastParams = params;
      this.get_circle();
    });

    this.sub = this.mapStateService.addOrthodromy.subscribe(params => {
      this.add_orthodromy();
    });

    this.sub = this.mapStateService.deleteOrtohromy.subscribe(params => {
      this.lastParams = params;
      this.delete_orthodromy();
    });

    this.selectSub = this.mapStateService.selectOrthodromy$.subscribe(orthodromy => {
      this.displaySelectedOrthodromy(orthodromy);
    });
  }

  ngOnDestroy() {
    if (this.sub) this.sub.unsubscribe();
  }

  private initMap() {
    this.map = L.map('map').setView([55.75, 37.61], 4);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.drawnItems.addTo(this.map);

    // Настройка Leaflet.Draw
    const drawControl = new L.Control.Draw({
      edit: { featureGroup: this.drawnItems, remove: true },
      draw: {
        polygon: {
          allowIntersection: false,
          shapeOptions: { color: '#333333', fillColor: '#999999', fillOpacity: 0.3 }
        },
        polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false
      }
    });
    this.map.addControl(drawControl);

    // Вешаем слушатели событий Leaflet
    this.map.on(L.Draw.Event.CREATED, (e: any) => this.onPolygonCreated(e));
    this.map.on(L.Draw.Event.DELETED, (e: any) => this.onPolygonDeleted(e));
    this.map.on(L.Draw.Event.EDITED, (e: any) => this.onPolygonEdited(e));
  }

  private loadPolygons() {
    this.apiService.getPolygons().subscribe({
      next: (polygonsArray) => {
        this.rawPolygonsData = polygonsArray;
        this.drawnItems.clearLayers();

        polygonsArray.forEach(coords => {
          const leafletCoords = coords.map(pt => [pt[1], pt[0]] as L.LatLngExpression);
          const poly = L.polygon(leafletCoords, {
            color: '#333333', fillColor: '#999999', fillOpacity: 0.2
          });
          poly.addTo(this.drawnItems);
        });

        if (this.drawnItems.getLayers().length > 0 && !this.currentPolyline) {
          this.map.fitBounds(this.drawnItems.getBounds());
        }
      },
      error: (err) => console.error('Ошибка загрузки полигонов:', err)
    });
  }

  private onPolygonCreated(event: any) {
    const layer = event.layer;
    const leafletCoords = layer.getLatLngs()[0] as L.LatLng[];
    const backendCoords = leafletCoords.map(latlng => [latlng.lng, latlng.lat]);

    this.apiService.addPolygon(backendCoords).subscribe(() => {
      this.loadPolygons();
      this.updateOrthodrome();
    });
  }

  private onPolygonDeleted(event: any) {
    const layers = event.layers;
    layers.eachLayer((layer: any) => {
      const leafletCoords = layer.getLatLngs()[0] as L.LatLng[];
      const backendCoords = leafletCoords.map(latlng => [latlng.lng, latlng.lat]);

      this.apiService.deletePolygon(backendCoords).subscribe();
    });

    setTimeout(() => {
      this.loadPolygons();
      this.updateOrthodrome();
    }, 100);
  }

  private onPolygonEdited(event: any) {
    const allPolygons: number[][][] = [];
    this.drawnItems.eachLayer((layer: any) => {
      const leafletCoords = layer.getLatLngs()[0] as L.LatLng[];
      const backendCoords = leafletCoords.map(latlng => [latlng.lng, latlng.lat]);
      allPolygons.push(backendCoords);
    });

    this.apiService.updateAllPolygons(allPolygons).subscribe(() => {
      this.rawPolygonsData = allPolygons;
      this.updateOrthodrome();
    });
  }

  private updateOrthodrome() {
    if (!this.lastParams) return;

    this.apiService.calculateOrthodrome(this.lastParams).subscribe({
      next: (data) => {
        if (data.status === 'success') {
          if (this.currentPolyline) {
            this.map.removeLayer(this.currentPolyline);
          }

          this.currentPolyline = L.polyline(data.coords, {
            color: '#0055ff', weight: 3, opacity: 0.8
          }).addTo(this.map);
          this.orthodromy_line = data.coords;
          this.checkLineIntersections(data.coords);
        }
      }
    });
  }



private get_circle() {
  if (!this.lastParams) return;

  this.apiService.get_circle(this.lastParams).subscribe({
    next: (data) => {
      if (data.status === 'success' && data.coords) {
        
        if (this.currentCircle) {
          this.map.removeLayer(this.currentCircle);
        }

        // Переворачиваем координаты из [Lng, Lat] в [Lat, Lng] для Leaflet
        const leafletCoords = data.coords.map((point: [number, number]) => [point[1], point[0]]);

        this.currentCircle = L.polygon(leafletCoords, {
          color: '#00ff4c',       // Цвет линии контура
          fillColor: '#00ff4c',   // Цвет заливки внутри круга
          fillOpacity: 0.2,       // Прозрачность заливки (20%)
          weight: 3,              // Толщина линии контура
          opacity: 0.8            // Прозрачность контура
        }).addTo(this.map);

        this.mapStateService.triggerCircleCoordinates(data.coords);
      }
    },
    error: (err) => {
      console.error('Ошибка при получении координат круга:', err);
    }
  });
  }
  private displaySelectedOrthodromy(orthodromy: any) {
    // Защита: если объект пустой или в нем нет координат — ничего не делаем
    if (!orthodromy || !orthodromy.coords) {
      return;
    }

    const coords = orthodromy.coords;

    // Проверяем, что координаты пришли в виде непустого массива
    if (!Array.isArray(coords) || coords.length === 0) {
      return;
    }

    // Удаляем старую линию, если она была на карте
    if (this.currentPolyline) {
      this.map.removeLayer(this.currentPolyline);
    }

    // Отрисовываем выбранную линию
    this.currentPolyline = L.polyline(coords, {
      color: '#0055ff', 
      weight: 3, 
      opacity: 0.8
    }).addTo(this.map);

    this.orthodromy_line = coords;

    // Центрируем карту по границам новой линии
    if (this.currentPolyline) {
      this.map.fitBounds(this.currentPolyline.getBounds());
    }

    // Запускаем ваш метод проверки пересечений с полигонами
    this.checkLineIntersections(coords);
  }

  private add_orthodromy(){

    this.apiService.add_orthodromy(this.orthodromy_line).subscribe({
      next: (data) => {
        if (data.status === 'success') {
          console.log(data.message)
          this.mapStateService.triggerRefreshList();
        }else{
          console.log(data.message)
        }
      }
    });
  }
  private delete_orthodromy(){

    this.apiService.delete_orthodromy(this.orthodromy_line).subscribe({
      next: (data) => {
        if (data.status === 'success') {
          console.log(data.message)
          if (this.currentPolyline) {
            this.map.removeLayer(this.currentPolyline);
            this.currentPolyline = null;
          }
          this.intersectionLayers.forEach(layer => this.map.removeLayer(layer));
          this.intersectionLayers = [];
          this.orthodromy_line = [];
          this.mapStateService.triggerRefreshList();
        }else{
          console.log(data.message)
        }
      }
    });
  }

  private checkLineIntersections(lineCoords: number[][]) {
    if (!this.rawPolygonsData || this.rawPolygonsData.length === 0) return;

    this.intersectionLayers.forEach(layer => this.map.removeLayer(layer));
    this.intersectionLayers = [];

    this.apiService.checkIntersections(lineCoords).subscribe({
      next: (data) => {
        if (data.status === 'success' && data.result.intersects) {
          data.result.intersected_parts.forEach((segment: L.LatLngExpression[]) => {
            const redLine = L.polyline(segment, {
              color: '#ff0000', weight: 5, opacity: 1.0
            }).addTo(this.map);
            this.intersectionLayers.push(redLine);
          });
        }
      }
    });
  }
}