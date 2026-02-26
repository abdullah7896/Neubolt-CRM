import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule } from '@angular/forms';
import { DomSanitizer } from '@angular/platform-browser';
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
  pageSize = 10;
  totalPages = 0;

  searchQuery: string = '';

  driverForm: FormGroup;
  selectedDriver: any = null;
  uploadedFiles: { [key: string]: string } = {};
  imageErrors: { [key: string]: string } = {};

  sortConfig: { column: string; direction: 'asc' | 'desc' }[] = [];

  constructor(
    private fb: FormBuilder,
    private crm: CrmService,
    private sanitizer: DomSanitizer
  ) {
    this.driverForm = this.fb.group({
      name: ['', [Validators.required, Validators.pattern(/^[a-zA-Z\s]+$/)]],
      contact_no: ['', [Validators.required, Validators.pattern(/^[0-9]{11}$/)]],
      dob: ['', Validators.required],
      current_address: ['', [Validators.required, Validators.minLength(5)]],
      ev_id: ['', Validators.required],
      dr_id: ['', [Validators.required, Validators.pattern(/^[0-9]{13}$/)]]
    });
  }

  ngOnInit() {
    this.loadDrivers();
  }

  loadDrivers() {
    this.crm.getDrivers().subscribe({
      next: (res: any) => {
        this.evData = Array.isArray(res)
          ? res.map((driver: any) => ({
              ...driver,
              dr_id: driver?.dr_id ?? driver?.driver_id ?? driver?.cnic ?? '',
              name: driver?.name ?? driver?.driver_name ?? '',
              contact_no: driver?.contact_no ?? driver?.contactNumber ?? driver?.phone_no ?? '',
              ev_id: driver?.ev_id ?? driver?.allocated_rikshaw ?? driver?.vehicle_id ?? '',
              current_address: driver?.current_address ?? driver?.address ?? ''
            }))
          : [];
        this.applySearch();
      },
      error: (err) => console.error('❌ Error fetching drivers', err)
    });
  }

  sanitizeInput(value: string): string {
    if (!value) return '';
    const temp = document.createElement('div');
    temp.textContent = value;
    return temp.innerHTML.trim();
  }

  /** SEARCH **/
  applySearch() {
    const query = this.sanitizeInput(this.searchQuery.trim().toLowerCase());
    if (query) {
      this.filteredData = this.evData.filter(ev =>
        (ev.ev_id && ev.ev_id.toString().toLowerCase().includes(query)) ||
        (ev.dr_id && ev.dr_id.toString().toLowerCase().includes(query))
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

  /** SUBMIT **/
  onSubmit() {
    if (!this.driverForm.valid) {
      alert('⚠️ Please fill all required fields correctly!');
      return;
    }

    const formValues = this.driverForm.value;

    const driverData = {
      dr_id: this.sanitizeInput(formValues.dr_id),
      name: this.sanitizeInput(formValues.name),
      contact_no: this.sanitizeInput(formValues.contact_no),
      dob: formValues.dob,
      city: '',
      current_address: this.sanitizeInput(formValues.current_address),
      ev_id: this.sanitizeInput(formValues.ev_id),
      user_id: localStorage.getItem('user_id') || '',
      driver_image: this.uploadedFiles['driver_image'] || null,
      cnic_front: this.uploadedFiles['cnic_front'] || null,
      cnic_back: this.uploadedFiles['cnic_back'] || null,
      linsence_img: this.uploadedFiles['linsence_img'] || null,
      criminal_record_img: this.uploadedFiles['criminal_record_img'] || null
    };
    console.log('📤 Submitting Driver Data:', driverData);

    this.crm.postDriver(driverData).subscribe({
      next: () => {
        alert('✅ Driver Registered Successfully');
        this.driverForm.reset();
        this.uploadedFiles = {};
        this.imageErrors = {};
        this.loadDrivers();
      },
      error: (err) => {
        console.error('❌ Error registering driver', err);
        const errorMsg = err?.error?.detail || 'Failed to register driver!';
        alert(errorMsg);
      }
    });
  }

  /** FILE UPLOAD **/
  onFileSelect(event: any, field: string) {
    const file = event.target.files[0];
    this.imageErrors[field] = '';

    if (file) {
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
      const maxSize = 5 * 1024 * 1024; // 5 MB

      if (!allowedTypes.includes(file.type)) {
        this.imageErrors[field] = '⚠️ Only JPG, JPEG, or PNG files are allowed!';
        return;
      }

      if (file.size > maxSize) {
        this.imageErrors[field] = '⚠️ File size must be less than 5 MB!';
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        this.uploadedFiles[field] = reader.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  /** PAGINATION **/
  setPage(page: number) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    this.currentPage = page;

    const start = (page - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedData = this.filteredData.slice(start, end);
  }

  /** SORTING **/
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
