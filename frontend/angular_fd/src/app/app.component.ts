import { Component } from '@angular/core';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { MapViewComponent } from './components/map-view/map-view.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [SidebarComponent, MapViewComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {}