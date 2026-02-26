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
    'title', 'complain_id', 'status', 'dr_id', 'driver_name',
    'type', 'complain_timestamp',
    'resolved_time'
  ];

  constructor(
    private fb: FormBuilder,
    private crmService: CrmService,
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) { }

  ngOnInit(): void {
    this.complainForm = this.fb.group({
      // Validation: Exactly 13 digits when stripped, matches regex for format
      cnic: ['', [Validators.required, Validators.pattern(/^\d{5}-\d{7}-\d{1}$/)]],
      driverName: ['', [Validators.required, Validators.pattern(/^[A-Za-z ]{3,50}$/)]],
      // Backend requires exactly 11 digits
      phoneNo: ['', [Validators.required, Validators.pattern(/^\d{11}$/)]],
      evId: ['', Validators.required],
      maintenanceType: ['General', Validators.required],
      title: ['', [Validators.required, Validators.maxLength(100)]],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      driverImage: ['']
    });

    this.sortConfig = this.columns.map(col => ({ column: col, direction: '' }));
    this.loadComplaints();
  }

  /** --- Helper: Unwrap Angular Sanitizer Objects --- */
  private getRawImage(img: any): string {
    if (!img) return '';
    // Check if the image is the nested object seen in your JSON payload
    if (img.changingThisBreaksApplicationSecurity) {
      return img.changingThisBreaksApplicationSecurity;
    }
    return img;
  }

  /** ---------------- LOAD COMPLAINTS ---------------- */
  loadComplaints() {
    this.loading = true;
    this.crmService.getComplaints().subscribe({
      next: (res: any) => {
        this.complaints = Array.isArray(res) ? res : [];
        this.applySorting(); // Sort before calculating pagination
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
    this.totalPages = Math.ceil(this.complaints.length / this.pageSize);
    if (page < 1) page = 1;
    if (page > this.totalPages && this.totalPages > 0) page = this.totalPages;
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

    // Strip dashes to match backend 13-digit requirement
    const digitsOnlyCNIC = cnic.replace(/-/g, '');
    if (digitsOnlyCNIC.length !== 13) {
      alert('Please enter a valid 13-digit CNIC (XXXXX-XXXXXXX-X).');
      return;
    }

    this.crmService.getDriverDetails(digitsOnlyCNIC).subscribe({
      next: (res: any) => {
        if (res && Object.keys(res).length > 0) {
          this.complainForm.patchValue({
            driverName: res.name || '',
            phoneNo: res.contact_no || '',
            evId: res.ev_id || '',
            driverImage: this.getRawImage(res.driver_image)
          });
          this.driverDetails = {
            driverImage: this.getRawImage(res.driver_image),
            address: res.current_address || '',
          };
          this.noDataFound = false;
        } else {
          this.refreshForm();
          this.noDataFound = true;
        }
      },
      error: (err) => {
        console.error('Error fetching driver info:', err);
        this.noDataFound = true;
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
    if (!value) return '';
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

    const cnicDigits = this.complainForm.value.cnic.replace(/-/g, '').substring(0, 13);
    const payload = {
      complain_id: 'CMP-' + Date.now(),
      user_id: localStorage.getItem('user_id') || '',
      dr_id: cnicDigits,
      title: this.sanitizeInput(this.complainForm.value.title),
      description: this.sanitizeInput(this.complainForm.value.description),
      type: this.complainForm.value.maintenanceType,
      location: ''
    };

    this.crmService.postComplaint(payload).subscribe({
      next: () => {
        alert('Complaint submitted successfully!');
        this.closeModal();
        this.loadComplaints();
      },
      error: (err) => {
        console.error('Error submitting complaint:', err);
        const errorMsg = err?.error?.detail || 'System internal error. Check Base64 image size.';
        alert(errorMsg);
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
    const updateData = { status: order.status };

    this.crmService.updateComplaint(order.complain_id, updateData).subscribe({
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
        valA = valA ? new Date(valA).getTime() : 0;
        valB = valB ? new Date(valB).getTime() : 0;
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
