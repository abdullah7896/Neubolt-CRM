import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Modal } from 'bootstrap';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';
import { CrmService } from 'src/app/services/crm.service';

@Component({
  selector: 'app-default',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './default.component.html',
  styleUrls: ['./default.component.scss']
})
export class DefaultComponent implements OnInit {
  @ViewChild('addComplainModal') addComplainModal!: ElementRef;
  modalInstance!: Modal;

  complainForm!: FormGroup;
  complaints: any[] = [];
  paginatedComplaints: any[] = [];
  loading: boolean = false;
  driverDetails: any = null;
  noDataFound: boolean = false;

  complainTypes: string[] = ['Service', 'General', 'Maintenance'];
  allowedStatuses: string[] = ['Pending', 'Completed', 'In-Progress'];

  editIndex: number | null = null;
  currentPage: number = 1;
  pageSize: number = 5;
  totalPages: number = 0;

  sortConfig: { column: string; direction: 'asc' | 'desc' | '' }[] = [];
  columns: string[] = [
    'complaint_name', 'complaint_id', 'status', 'driver_name',
    'type', 'complaint_register_time', 'driver_cnic',
    'status_change_time', 'ev_id'
  ];

  constructor(
    private fb: FormBuilder,
    private crmService: CrmService,
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) { }

  ngOnInit(): void {
    this.complainForm = this.fb.group({
      cnic: ['', [Validators.required, Validators.pattern(/^\d{5}-\d{7}-\d{1}$/)]],
      driverName: ['', [Validators.required, Validators.pattern(/^[A-Za-z ]{3,50}$/)]],
      phoneNo: ['', [Validators.required, Validators.pattern(/^\d{10,12}$/)]],
      evId: ['', Validators.required],
      maintenanceType: ['General', Validators.required],
      title: ['', [Validators.required, Validators.maxLength(100)]],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      driverImage: ['']
    });

    this.sortConfig = this.columns.map(col => ({ column: col, direction: '' }));
    this.loadComplaints();
  }

  /** ---------------- LOAD COMPLAINTS ---------------- */
  loadComplaints() {
    this.loading = true;
    this.crmService.getComplaints().subscribe({
      next: (res: any) => {
        this.complaints = Array.isArray(res.complaints) ? res.complaints : [];
        this.totalPages = Math.ceil(this.complaints.length / this.pageSize);
        this.setPage(1);
        this.loading = false;
      },
      error: (err) => {
        console.error('Error fetching complaints:', err);
        this.complaints = [];
        this.loading = false;
      }
    });
  }

  /** ---------------- PAGINATION ---------------- */
  setPage(page: number) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    this.currentPage = page;

    const start = (page - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedComplaints = this.complaints.slice(start, end);
  }

  /** ---------------- MODAL ---------------- */
  openModal() {
    this.modalInstance = new Modal(this.addComplainModal.nativeElement);
    this.modalInstance.show();
    this.noDataFound = false;
    this.complainForm.reset({ maintenanceType: 'General' });
    this.driverDetails = null;
  }

  closeModal() {
    this.modalInstance.hide();
  }

  /** ---------------- CNIC VERIFICATION ---------------- */
  verifyCNIC() {
    const cnic = this.complainForm.get('cnic')?.value;
    if (!cnic) {
      alert('Please enter CNIC first.');
      return;
    }

    const digitsOnlyCNIC = cnic.replace(/-/g, '');
    if (digitsOnlyCNIC.length !== 13 || !/^\d+$/.test(digitsOnlyCNIC)) {
      alert('Please enter a valid 13-digit CNIC.');
      return;
    }

    this.crmService.getDriverDetails(digitsOnlyCNIC).subscribe({
      next: (res: any) => {
        if (res && Object.keys(res).length > 0) {
          this.complainForm.patchValue({
            driverName: res.name || '',
            phoneNo: res.contact_number || '',
            evId: res.allocated_rikshaw || '',
            driverImage: res.driver_image || ''
          });
          this.driverDetails = {
            driverImage: res.driver_image || '',
            address: res.current_address || '',
          };
          this.noDataFound = false;
        } else {
          this.complainForm.patchValue({
            driverName: '',
            phoneNo: '',
            evId: '',
            driverImage: ''
          });
          this.driverDetails = null;
          this.noDataFound = true;
        }
      },
      error: (err) => {
        console.error('Error fetching driver info:', err);
        alert('Error fetching driver info');
      }
    });
  }

  /** ---------------- RESET FORM ---------------- */
  refreshForm() {
    this.complainForm.reset({ maintenanceType: 'General' });
    this.driverDetails = null;
    this.noDataFound = false;
  }

  /** ---------------- SANITIZATION ---------------- */
  sanitizeInput(value: string): string {
    const div = document.createElement('div');
    div.innerText = value;
    return div.innerHTML.trim();
  }

  /** ---------------- SUBMIT COMPLAINT ---------------- */
  submitComplain() {
    if (this.complainForm.invalid) {
      alert('Please fill all required fields correctly!');
      this.complainForm.markAllAsTouched();
      return;
    }

    const title = this.sanitizeInput(this.complainForm.value.title);
    const description = this.sanitizeInput(this.complainForm.value.description);

    const payload = {
      driver_cnic: this.complainForm.value.cnic.replace(/-/g, ''), // Strip dashes for DB limit (13 chars)
      driver_name: this.complainForm.value.driverName,
      phone_no: this.complainForm.value.phoneNo,
      driver_number: this.complainForm.value.phoneNo, // Added to satisfy backend requirement
      ev_id: this.complainForm.value.evId,
      driver_image: this.complainForm.value.driverImage,
      complaint_name: title,
      description: description,
      type: this.complainForm.value.maintenanceType
    };

    this.crmService.postComplaint(payload).subscribe({
      next: () => {
        alert('Complain submitted successfully!');
        this.closeModal();
        this.loadComplaints();
      },
      error: (err) => {
        console.error('Error submitting complain:', err);
      }
    });
  }

  /** ---------------- INLINE EDIT ---------------- */
  editRow(index: number) {
    this.editIndex = index;
  }

  cancelEdit() {
    this.editIndex = null;
    this.loadComplaints();
  }

  saveRow(order: any) {
    // Sanitize CNIC: remove dashes, take first 13 digits to prevent overflow/duplication bugs
    if (order.driver_cnic) {
      order.driver_cnic = order.driver_cnic.toString().replace(/\D/g, '').substring(0, 13);
    }

    this.crmService.updateComplaint(order.complaint_id, order).subscribe({
      next: () => {
        alert('Complaint updated successfully!');
        this.editIndex = null;
        this.loadComplaints();
      },
      error: (err) => {
        console.error('Error updating complaint:', err);
        alert('Failed to update complaint');
      }
    });
  }

  /** ---------------- SORTING ---------------- */
  sortTable(column: string) {
    const config = this.sortConfig.find(c => c.column === column);
    if (config) {
      config.direction =
        config.direction === 'asc' ? 'desc' : config.direction === 'desc' ? '' : 'asc';
    }
    this.applySorting();
  }

  applySorting() {
    const activeSort = this.sortConfig.find(c => c.direction !== '');
    if (!activeSort) {
      this.setPage(1);
      return;
    }

    const { column, direction } = activeSort;
    this.complaints.sort((a: any, b: any) => {
      let valA = a[column],
        valB = b[column];
      if (column.includes('time')) {
        valA = new Date(valA).getTime();
        valB = new Date(valB).getTime();
      }
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();
      if (valA < valB) return direction === 'asc' ? -1 : 1;
      if (valA > valB) return direction === 'asc' ? 1 : -1;
      return 0;
    });

    this.setPage(1);
  }

  getSortIcon(column: string): string {
    const config = this.sortConfig.find(c => c.column === column);
    if (!config || config.direction === '') return '↕';
    return config.direction === 'asc' ? '↑' : '↓';
  }
}
