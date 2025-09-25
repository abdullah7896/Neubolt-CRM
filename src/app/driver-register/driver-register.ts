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
  /** -------------------- DATA -------------------- **/
  evData: any[] = [];          // all driver records
  paginatedData: any[] = [];   // data for current page
  currentPage = 1;
  pageSize = 5;
  totalPages = 0;

  driverForm: FormGroup;       // reactive form
  selectedDriver: any = null;  // for detail modal
  uploadedFiles: { [key: string]: string } = {}; // store Base64 encoded files

  /** Sorting Config **/
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

  /** -------------------- LIFECYCLE -------------------- **/
  ngOnInit() {
    this.loadDrivers();
  }

  /** -------------------- API -------------------- **/
  loadDrivers() {
    this.crm.getDrivers().subscribe({
      next: (res: any) => {
        this.evData = res;
        this.totalPages = Math.ceil(this.evData.length / this.pageSize);
        this.setPage(1);
      },
      error: (err) => console.error('❌ Error fetching drivers', err)
    });
  }

  onSubmit() {
    if (!this.driverForm.valid) {
      alert('⚠️ Please fill all required fields correctly!');
      return;
    }

    // prepare request body
    const driverData = {
      ...this.driverForm.value,
      ...this.uploadedFiles // merge optional file fields
      // driver_id & registered_at will be auto-generated on backend
    };

    this.crm.postDriver(driverData).subscribe({
      next: () => {
        alert('✅ Driver Registered Successfully');
       this.driverForm.reset();

      // Reset pristine + untouched state
      this.driverForm.markAsPristine();
      this.driverForm.markAsUntouched();

      // Clear validation errors
      Object.keys(this.driverForm.controls).forEach(key => {
        this.driverForm.get(key)?.setErrors(null);
      });

      // Clear file previews
      this.uploadedFiles = {};

      // Reset file input elements from DOM
      const inputs = document.querySelectorAll<HTMLInputElement>('input[type="file"]');
      inputs.forEach(input => (input.value = ''));

      this.loadDrivers();
        
      },
      error: (err) => {
        console.error('❌ Error registering driver', err);
        alert('Failed to register driver!');
      }
    });
  }

  /** -------------------- FILE UPLOAD -------------------- **/
  onFileSelect(event: any, field: string) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        this.uploadedFiles[field] = reader.result as string; // store Base64
      };
      reader.readAsDataURL(file);
    }
  }

  /** -------------------- PAGINATION -------------------- **/
  setPage(page: number) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    this.currentPage = page;

    const start = (page - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedData = this.evData.slice(start, end);
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
    if (!config) return '↕'; // default icon
    return config.direction === 'asc' ? '↑' : '↓';
  }

  /** -------------------- ROW CLICK (DETAIL MODAL) -------------------- **/
  openDetails(driver: any) {
    this.selectedDriver = driver;
  }
}
