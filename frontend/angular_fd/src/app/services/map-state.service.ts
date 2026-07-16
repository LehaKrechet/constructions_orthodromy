import { Injectable } from '@angular/core';
import { Subject, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MapStateService {
  private calculateTrigger = new Subject<any>();
  private calculateCircleTrigger = new Subject<any>();
  private addOrthodromyTrigger = new Subject<any>();
  private deleteOrthodromyTrigger = new Subject<any>();
  
  private selectOrthodromyTrigger = new Subject<any>();
  private refreshOrthodromiesListTrigger = new Subject<void>();


  calculateCitrle = this.calculateCircleTrigger.asObservable();
  calculate$ = this.calculateTrigger.asObservable();
  addOrthodromy = this.addOrthodromyTrigger.asObservable();
  deleteOrtohromy = this.deleteOrthodromyTrigger.asObservable();

  selectOrthodromy$ = this.selectOrthodromyTrigger.asObservable();
  refreshOrthodromiesList$ = this.refreshOrthodromiesListTrigger.asObservable();

  private circleCoordinatesTrigger = new Subject<number[][]>();
  circleCoordinates$ = this.circleCoordinatesTrigger.asObservable();

  triggerCalculation(params: any) {
    this.calculateTrigger.next(params);
  }
  triggerCircleCalculation(params: any) {
    this.calculateCircleTrigger.next(params);
  }

  triggerAddOrthodromy(params: any){
    this.addOrthodromyTrigger.next(params);
  }

  triggerDeleteOrthodromy(params: any){
    this.deleteOrthodromyTrigger.next(params);
  }

  triggerSelectOrthodromy(orthodromy: any) {
    this.selectOrthodromyTrigger.next(orthodromy);
  }

  triggerRefreshList() {
    this.refreshOrthodromiesListTrigger.next(); 
  }

  triggerCircleCoordinates(coords: number[][]) {
    this.circleCoordinatesTrigger.next(coords);
  }
}