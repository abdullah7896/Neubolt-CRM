import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DriverRegister } from './driver-register';

describe('DriverRegister', () => {
  let component: DriverRegister;
  let fixture: ComponentFixture<DriverRegister>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DriverRegister]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DriverRegister);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
