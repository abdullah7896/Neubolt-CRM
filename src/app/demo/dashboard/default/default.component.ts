import { Component, inject, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { IconService } from '@ant-design/icons-angular';
import { RiseOutline, FallOutline, SettingOutline, GiftOutline, MessageOutline } from '@ant-design/icons-angular/icons';
import { Modal } from 'bootstrap';
import { CrmService } from 'src/app/services/crm.service';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-default',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './default.component.html',
  styleUrls: ['./default.component.scss']
})
export class DefaultComponent implements OnInit {
  private iconService = inject(IconService);

  @ViewChild('addComplainModal') addComplainModal!: ElementRef;
  modalInstance!: Modal;

  complainForm!: FormGroup;
  complaints: any[] = [];
  paginatedComplaints: any[] = [];
  loading: boolean = false;
  driverDetails: any = null;
  noDataFound: boolean = false;

  complainTypes: string[] = ['Service', 'General', 'Maintenance'];

  // ✅ Only these statuses will show in dropdown
  allowedStatuses: string[] = ['Pending', 'Completed', 'In-Progress'];

  editIndex: number | null = null;

  // Pagination variables
  currentPage: number = 1;
  pageSize: number = 5;
  totalPages: number = 0;

  constructor(
    private fb: FormBuilder,
    private crmService: CrmService,
    private http: HttpClient
  ) {
    this.iconService.addIcon(...[RiseOutline, FallOutline, SettingOutline, GiftOutline, MessageOutline]);
  }

  ngOnInit(): void {
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

    this.loadComplaints();
  }

  /** -------------------- LOAD COMPLAINTS -------------------- **/
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

  /** -------------------- PAGINATION -------------------- **/
  setPage(page: number) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    this.currentPage = page;

    const start = (page - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginatedComplaints = this.complaints.slice(start, end);
  }

  /** -------------------- MODAL HANDLING -------------------- **/
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

  /** -------------------- CNIC VERIFICATION -------------------- **/
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

  /** -------------------- FORM RESET -------------------- **/
  refreshForm() {
    this.complainForm.reset({ maintenanceType: 'General' });
    this.driverDetails = null;
    this.noDataFound = false;
  }

  /** -------------------- NEW COMPLAINT SUBMIT -------------------- **/
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
      next: () => { alert('Complain submitted successfully!'); this.closeModal(); this.loadComplaints(); },
      error: (err) => { console.error('Error submitting complain:', err); }
    });
  }

  /** -------------------- INLINE ROW EDIT -------------------- **/
  editRow(index: number) { this.editIndex = index; }
  cancelEdit() { this.editIndex = null; this.loadComplaints(); }

  saveRow(order: any) {
    const apiUrl = `http://203.135.63.46:5000/neubolt/crm/put-complaints/${order.complaint_id}`;
    this.http.put(apiUrl, order).subscribe({
      next: () => { alert('Complaint updated successfully!'); this.editIndex = null; this.loadComplaints(); },
      error: (err) => { console.error('Error updating complaint:', err); alert('Failed to update complaint'); }
    });
  }
}
