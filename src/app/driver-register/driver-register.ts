import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule } from '@angular/forms'; // for [(ngModel)]
import { CrmService } from 'src/app/services/crm.service';

@Component({
  selector: 'app-driver-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './driver-register.html',
  styleUrls: ['./driver-register.scss']
})
export class DriverRegister implements OnInit {
  evData: any[] = [];
  filteredData: any[] = [];
  paginatedData: any[] = [];

  currentPage = 1;
  pageSize = 5;
  totalPages = 0;

  searchQuery: string = '';

  driverForm: FormGroup;
  selectedDriver: any = null;
  uploadedFiles: { [key: string]: string } = {};

  sortConfig: { column: string; direction: 'asc' | 'desc' }[] = [];

  constructor(private fb: FormBuilder, private crm: CrmService) {
    this.driverForm = this.fb.group({
      name: ['', Validators.required],
      contact_number: ['', [Validators.required, Validators.pattern(/^[0-9]{11}$/)]],
      dob: ['', Validators.required],
      current_address: ['', Validators.required],
      allocated_rikshaw: [''],
      cnic_number: ['', [Validators.required, Validators.pattern(/^[0-9]{13}$/)]]
    });
  }

  ngOnInit() {
    this.loadDrivers();
  }

  loadDrivers() {
    this.crm.getDrivers().subscribe({
      next: (res: any) => {
        this.evData = res;
        this.applySearch();
      },
      error: (err) => console.error('❌ Error fetching drivers', err)
    });
  }

  /** -------------------- SEARCH -------------------- **/
  applySearch() {
    const query = this.searchQuery.trim().toLowerCase();
    if (query) {
      this.filteredData = this.evData.filter(ev =>
        (ev.allocated_rikshaw && ev.allocated_rikshaw.toString().toLowerCase().includes(query)) ||
        (ev.driver_id && ev.driver_id.toString().toLowerCase().includes(query))
      );
    } else {
      this.filteredData = [...this.evData];
    }

    this.totalPages = Math.ceil(this.filteredData.length / this.pageSize);
    this.setPage(1);
  }

  clearSearch() {
    this.searchQuery = '';
    this.applySearch();
  }

  onSubmit() {
    if (!this.driverForm.valid) {
      alert('⚠️ Please fill all required fields correctly!');
      return;
    }

    const driverData = {
      ...this.driverForm.value,
      ...this.uploadedFiles
    };

    this.crm.postDriver(driverData).subscribe({
      next: () => {
        alert('✅ Driver Registered Successfully');
        this.driverForm.reset();
        this.uploadedFiles = {};
        this.loadDrivers();
      },
      error: (err) => {
        console.error('❌ Error registering driver', err);
        alert('Failed to register driver!');
      }
    });
  }

  onFileSelect(event: any, field: string) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        this.uploadedFiles[field] = reader.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  setPage(page: number) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    this.currentPage = page;

    const start = (page - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedData = this.filteredData.slice(start, end);
  }

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
    this.filteredData.sort((a: any, b: any) => {
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
    if (!config) return '↕';
    return config.direction === 'asc' ? '↑' : '↓';
  }

  openDetails(driver: any) {
    this.selectedDriver = driver;
  }
}
