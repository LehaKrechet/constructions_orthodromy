import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common'; 
import { SidebarComponent as SB } from './sidebar.component';
import { MapStateService } from '../../services/map-state.service';
import { MapApiService } from '../../services/map-api.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent implements OnInit, OnDestroy {
  params = {
    lon1: 37.61357696727,
    lat1: 55.7541099812487752,
    lon2: 160.75293945312,
    lat2: 55.855275,
    points: 100,
    coordMode: 'WGS84',
    lon: 37,
    lat: 55,
    radius: 1000000,
    avoidZones: false,
    bufferDistance: 0.1
  };

  allSavedOrthodromies: any[] = [];      
  intersectingOrthodromies: any[] = [];  

  selectedOrthodromy: any = null;
  selectedIntersectingOrthodromy: any = null;
  private sub!: Subscription;

  constructor(private mapStateService: MapStateService, private apiService: MapApiService) {}

  ngOnInit() {
    this.loadSavedOrthodromies();

    // Слушаем сигнал на обновление списка (после сохранения/удаления на карте)
    this.sub = this.mapStateService.refreshOrthodromiesList$.subscribe(() => {
      setTimeout(() => {
        this.loadSavedOrthodromies();
      });
    });

    // Слушаем координаты построенного круга с карты
    const circleSub = this.mapStateService.circleCoordinates$.subscribe((coords: number[][]) => {
      this.onCircleSelectedForIntersection(coords);
    });
    this.sub.add(circleSub);
  }

  ngOnDestroy() {
    if (this.sub) this.sub.unsubscribe();
  }

  loadSavedOrthodromies() {
    this.apiService.get_orthodromy().subscribe({
      next: (response: any) => {
        setTimeout(() => {
          this.selectedOrthodromy = null;

          if (response && response.status === 'success' && Array.isArray(response.coords)) {
            const rawCoords = response.coords;

            if (
              rawCoords.length > 0 && 
              Array.isArray(rawCoords[0]) && 
              typeof rawCoords[0][0] === 'number'
            ) {
              this.allSavedOrthodromies = [{
                name: 'Ортодромия №1 (сохраненная)',
                coords: rawCoords
              }];
            } 
            else if (
              rawCoords.length > 0 && 
              Array.isArray(rawCoords[0]) && 
              Array.isArray(rawCoords[0][0])
            ) {
              this.allSavedOrthodromies = rawCoords.map((line: any, index: number) => {
                return {
                  name: `№${index + 1}:${line[0]}:${line[line.length - 1]}`,
                  coords: line
                };
              });
            } else {
              this.allSavedOrthodromies = [];
            }
          } else {
            this.allSavedOrthodromies = [];
          }
          console.log('Все ортодромии загружены:', this.allSavedOrthodromies);
        });
      },
      error: (err: any) => {
        console.error('Ошибка загрузки сохраненных ортодромий:', err);
      }
    });
  }

  onCircleSelectedForIntersection(circleCoords: number[][]) {
    if (!circleCoords || circleCoords.length === 0) {
      console.warn('Координаты круга не переданы');
      return;
    }

    this.apiService.get_lines_intersection_circle(circleCoords).subscribe({
      next: (response: any) => {
        setTimeout(() => {
          this.selectedIntersectingOrthodromy = null;
          this.intersectingOrthodromies = [];

          if (response && response.status === 'success' && Array.isArray(response.coords)) {
            const rawCoords = response.coords;

            this.intersectingOrthodromies = rawCoords.map((line: any, index: number) => {
              const start = line[0];
              const end = line[line.length - 1];
              return {
                name: `№${index + 1}(${line[0]}:${line[line.length - 1]})`,
                coords: line
              };
            });

            console.log('Найдено пересекающих ортодромий:', this.intersectingOrthodromies.length);
          } else {
            console.log('Пересекающих ортодромий не найдено');
          }
        });
      },
      error: (err: any) => {
        console.error('Ошибка при поиске пересекающих ортодромий:', err);
      }
    });
  }

  // Метод, который срабатывает при выборе ортодромии из выпадающего списка
  onOrthodromySelect() {
    if (this.selectedOrthodromy && this.selectedOrthodromy.coords) {
      this.mapStateService.triggerSelectOrthodromy(this.selectedOrthodromy);
    }
  }

  onIntersectingOrthodromySelect() {
    if (this.selectedIntersectingOrthodromy && this.selectedIntersectingOrthodromy.coords) {
      this.mapStateService.triggerSelectOrthodromy(this.selectedIntersectingOrthodromy);
    }
  }

  onSubmit() {
    this.mapStateService.triggerCalculation(this.params);
  }

  onSubmit_circle() {
    this.mapStateService.triggerCircleCalculation(this.params);
  }

  add_orthodromy() {
    this.mapStateService.triggerAddOrthodromy(this.params);
  }

  delete_orthodromy() {
    this.mapStateService.triggerDeleteOrthodromy(this.params);
  }
}