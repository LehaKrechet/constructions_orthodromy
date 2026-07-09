import { TestBed } from '@angular/core/testing';

import { MapApi } from './map-api';

describe('MapApi', () => {
  let service: MapApi;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MapApi);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
