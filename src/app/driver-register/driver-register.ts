import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
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
  selectedDriver: any = null;   // 🔹 Row click ke liye

  sortConfig: { column: string; direction: 'asc' | 'desc' }[] = [];

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
      allocated_rikshaw: this.driverForm.get('rikshawId')?.value
    };

    this.crm.postDriver(driverData).subscribe({
      next: () => {
        alert('Driver Registered Successfully ✅');
        this.driverForm.reset();
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

  /** -------------------- ROW CLICK (Detail Modal) -------------------- **/
  openDetails(driver: any) {
    this.selectedDriver = driver;
  }
}
