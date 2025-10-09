import { Component, inject, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Modal } from 'bootstrap';
import { HttpClient } from '@angular/common/http';
import { CrmService } from 'src/app/services/crm.service';
import { AuthLoginComponent } from "../../pages/authentication/auth-login/auth-login.component";

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

  // Pagination
  currentPage: number = 1;
  pageSize: number = 5;
  totalPages: number = 0;

  // Sorting
  sortConfig: { column: string; direction: 'asc' | 'desc' | '' }[] = [];

  columns: string[] = [
    'complaint_name', 'complaint_id', 'status', 'driver_name',
    'type', 'complaint_register_time', 'driver_cnic',
    'status_change_time', 'ev_id'
  ];

  constructor(
    private fb: FormBuilder,
    private crmService: CrmService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    // Initialize form
    this.complainForm = this.fb.group({
      cnic: ['', Validators.required],
      driverName: ['', Validators.required],
      phoneNo: ['', Validators.required],
      evId: ['', Validators.required],
      maintenanceType: ['General', Validators.required],
      title: ['', Validators.required],
      description: ['', Validators.required],
      driverImage: ['']
    });

    // Initialize default sorting icons (all unsorted by default)
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

  closeModal() { this.modalInstance.hide(); }

  /** ---------------- CNIC VERIFICATION ---------------- */
  verifyCNIC() {
    const cnic = this.complainForm.get('cnic')?.value;
    if (!cnic) { alert('Please enter CNIC first.'); return; }

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
            dob: res.dob,
            address: res.current_address,
            licenseImage: res.license_image,
            cnicFront: res.cnic_front_image,
            cnicBack: res.cnic_back_image
          };
          this.noDataFound = false;
        } else {
          this.complainForm.patchValue({ driverName: '', phoneNo: '', evId: '', driverImage: '' });
          this.driverDetails = null;
          this.noDataFound = true;
        }
      },
      error: (err) => { console.error('Error fetching driver info:', err); alert('Error fetching driver info'); }
    });
  }

  /** ---------------- RESET FORM ---------------- */
  refreshForm() {
    this.complainForm.reset({ maintenanceType: 'General' });
    this.driverDetails = null;
    this.noDataFound = false;
  }

  /** ---------------- SUBMIT COMPLAINT ---------------- */
  submitComplain() {
    if (!this.complainForm.valid) { alert('Please fill all required fields!'); return; }

    const payload = {
      driver_cnic: this.complainForm.value.cnic,
      driver_name: this.complainForm.value.driverName,
      phone_no: this.complainForm.value.phoneNo,
      ev_id: this.complainForm.value.evId,
      driver_image: this.complainForm.value.driverImage,
      complaint_name: this.complainForm.value.title,
      description: this.complainForm.value.description,
      type: this.complainForm.value.maintenanceType
    };

    this.crmService.postComplaint(payload).subscribe({
      next: () => { 
        alert('Complain submitted successfully!'); 
        this.closeModal(); 
        this.loadComplaints(); 
      },
      error: (err) => { console.error('Error submitting complain:', err); }
    });
  }

  /** ---------------- INLINE ROW EDIT ---------------- */
  editRow(index: number) { this.editIndex = index; }
  cancelEdit() { this.editIndex = null; this.loadComplaints(); }

  saveRow(order: any) {
    const apiUrl = `http://203.135.63.46:5000/neubolt/crm/put-complaints/${order.complaint_id}`;
    this.http.put(apiUrl, order).subscribe({
      next: () => { alert('Complaint updated successfully!'); this.editIndex = null; this.loadComplaints(); },
      error: (err) => { console.error('Error updating complaint:', err); alert('Failed to update complaint'); }
    });
  }

  /** ---------------- SORTING ---------------- */
  sortTable(column: string) {
    const config = this.sortConfig.find(c => c.column === column);
    if (config) {
      // toggle asc / desc
      config.direction = config.direction === 'asc' ? 'desc' : (config.direction === 'desc' ? '' : 'asc');
    }
    this.applySorting();
  }

  applySorting() {
    const activeSort = this.sortConfig.find(c => c.direction !== '');
    if (!activeSort) { this.setPage(1); return; }

    const { column, direction } = activeSort;
    this.complaints.sort((a: any, b: any) => {
      let valA = a[column], valB = b[column];
      if (column.includes('time')) { valA = new Date(valA).getTime(); valB = new Date(valB).getTime(); }
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
    if (!config || config.direction === '') return '↕'; // default unsorted icon
    return config.direction === 'asc' ? '↑' : '↓';
  }
}
