import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { CrmService } from 'src/app/services/crm.service';

@Component({
  selector: 'app-driver-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './driver-register.html',
  styleUrls: ['./driver-register.scss']
})
export class DriverRegister implements OnInit {
  evData: any[] = [];
  paginatedData: any[] = [];
  currentPage = 1;
  pageSize = 5;
  totalPages = 0;

  driverForm: FormGroup;
  files: any = { cnicFront: null, cnicBack: null, license: null, driverImage: null, criminalRecord: null };
  preview: any = { cnicFront: null, cnicBack: null, license: null, driverImage: null, criminalRecord: null };

  sortConfig: { column: string; direction: 'asc' | 'desc' }[] = [];

  @ViewChild('fileInputFront') fileInputFront!: ElementRef;
  @ViewChild('fileInputBack') fileInputBack!: ElementRef;
  @ViewChild('fileInputLicense') fileInputLicense!: ElementRef;
  @ViewChild('fileInputDriver') fileInputDriver!: ElementRef;
  @ViewChild('fileInputCriminal') fileInputCriminal!: ElementRef;

  constructor(private fb: FormBuilder, private crm: CrmService) {
    this.driverForm = this.fb.group({
      name: ['', Validators.required],
      contactNo: ['', Validators.required],
      dob: ['', Validators.required],
      address: ['', Validators.required],
      rikshawId: ['', Validators.required],
      cnic: ['', [Validators.required, Validators.pattern(/^[0-9]{13}$/)]]
    });
  }

  ngOnInit() {
    this.loadDrivers();
  }

  loadDrivers() {
    this.crm.getDrivers().subscribe({
      next: (res: any) => {
        this.evData = res;
        this.totalPages = Math.ceil(this.evData.length / this.pageSize);
        this.setPage(1);
      },
      error: (err) => console.error('Error fetching drivers', err)
    });
  }

  setPage(page: number) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    this.currentPage = page;

    const start = (page - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedData = this.evData.slice(start, end);
  }

  onFileSelect(event: any, field: string) {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      this.files[field] = file;

      const reader = new FileReader();
      reader.onload = () => {
        this.preview[field] = reader.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  onSubmit() {
    if (!this.driverForm.valid) {
      alert('Please fill all required fields!');
      return;
    }

    const driverData = {
      name: this.driverForm.get('name')?.value,
      contact_number: this.driverForm.get('contactNo')?.value,
      cnic_number: this.driverForm.get('cnic')?.value,
      dob: this.driverForm.get('dob')?.value,
      current_address: this.driverForm.get('address')?.value,
      allocated_rikshaw: this.driverForm.get('rikshawId')?.value,
      driver_image: this.files.driverImage ? this.files.driverImage.name : 'uploads/drivers/default.jpg',
      cnic_front_image: this.files.cnicFront ? this.files.cnicFront.name : 'uploads/cnic/front_default.jpg',
      cnic_back_image: this.files.cnicBack ? this.files.cnicBack.name : 'uploads/cnic/back_default.jpg',
      license_image: this.files.license ? this.files.license.name : 'uploads/license/default.jpg',
      criminal_record_image: this.files.criminalRecord ? this.files.criminalRecord.name : 'uploads/criminal/none.jpg'
    };

    this.crm.postDriver(driverData).subscribe({
      next: () => {
        alert('Driver Registered Successfully ✅');
        this.driverForm.reset();
        this.preview = { cnicFront: null, cnicBack: null, license: null, driverImage: null, criminalRecord: null };
        this.loadDrivers();
      },
      error: (err) => {
        console.error('Error registering driver', err);
        alert('Failed to register driver!');
      }
    });
  }

  /** -------------------- SORTING -------------------- **/
  sortTable(column: string) {
    const existing = this.sortConfig.find(s => s.column === column);
    if (existing) {
      existing.direction = existing.direction === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortConfig = [{ column, direction: 'asc' }];
    }
    this.applySorting();
  }

  applySorting() {
    this.evData.sort((a: any, b: any) => {
      for (let config of this.sortConfig) {
        let valueA = a[config.column];
        let valueB = b[config.column];

        if (typeof valueA === 'string') valueA = valueA.toLowerCase();
        if (typeof valueB === 'string') valueB = valueB.toLowerCase();

        if (valueA < valueB) return config.direction === 'asc' ? -1 : 1;
        if (valueA > valueB) return config.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
    this.setPage(1);
  }

  getSortIcon(column: string): string {
    const config = this.sortConfig.find(s => s.column === column);
    if (!config) return '↕'; // default sorting icon
    return config.direction === 'asc' ? '↑' : '↓';
  }
}
