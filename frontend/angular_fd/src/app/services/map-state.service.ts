import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MapStateService {
  private calculateTrigger = new Subject<any>();
  calculate$ = this.calculateTrigger.asObservable();

  triggerCalculation(params: any) {
    this.calculateTrigger.next(params);
  }
}