import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MapStateService {
  private calculateTrigger = new Subject<any>();
  private calculateCircleTrigger = new Subject<any>();

  calculateCitrle = this.calculateCircleTrigger.asObservable();
  calculate$ = this.calculateTrigger.asObservable();

  triggerCalculation(params: any) {
    this.calculateTrigger.next(params);
  }
  triggerCircleCalculation(params: any) {
    this.calculateCircleTrigger.next(params);
  }
}