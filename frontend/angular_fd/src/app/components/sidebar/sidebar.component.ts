import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MapStateService } from '../../services/map-state.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  params = {
    lon1: 37.61357696727,
    lat1: 55.7541099812487752,
    lon2: 160.75293945312,
    lat2: 55.855275,
    points: 100,
    coordMode: 'WGS84',
    lon: 37,
    lat: 55,
    radius: 100
  };

  constructor(private mapStateService: MapStateService) {}

  onSubmit() {
    this.mapStateService.triggerCalculation(this.params);
  }

  onSubmit_circle() {
    this.mapStateService.triggerCircleCalculation(this.params);
  }
}