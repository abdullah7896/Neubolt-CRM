import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, map, shareReplay, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CrmService {
  private baseUrl = 'http://localhost:8000/neubolt';
  private complaintsCache$?: Observable<any>;
  private driversCache$?: Observable<any>;

  constructor(private http: HttpClient) { }

  // ✅ Get headers with token
  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    });
  }

  // ✅ Login API (store tokens)
  login(credentials: { username: string; password: string }): Observable<any> {
    return this.http.post(`${this.baseUrl}/login`, credentials).pipe(
      tap((response: any) => {
        if (response && response.access_token) {
          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('refresh_token', response.refresh_token || '');
          localStorage.setItem('user_id', response.user_id || '');
          localStorage.setItem('user_type', response.user_type || '');
        }
      })
    );
  }

  // ✅ Logout
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_type');
    this.clearAllCache();
  }

  // ✅ Get Driver Details by CNIC (dr_id)
  getDriverDetails(cnic: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/drivers/${cnic}`, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Post Complaint
  postComplaint(complaint: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/complaints`, complaint, {
      headers: this.getAuthHeaders()
    }).pipe(tap(() => this.invalidateComplaintsCache()));
  }

  // ✅ Get All Complaints
  getComplaints(forceRefresh = false): Observable<any> {
    if (forceRefresh || !this.complaintsCache$) {
      this.complaintsCache$ = this.http.get(`${this.baseUrl}/complaints`, {
        headers: this.getAuthHeaders()
      }).pipe(shareReplay(1));
    }
    return this.complaintsCache$;
  }

  // ✅ Update Complaint
  updateComplaint(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/complaints/${id}`, data, {
      headers: this.getAuthHeaders()
    }).pipe(tap(() => this.invalidateComplaintsCache()));
  }

  // ✅ Delete Complaint
  deleteComplaint(id: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/complaints/${id}`, {
      headers: this.getAuthHeaders()
    }).pipe(tap(() => this.invalidateComplaintsCache()));
  }

  // ✅ Driver APIs
  postDriver(driver: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/drivers`, driver, {
      headers: this.getAuthHeaders()
    }).pipe(tap(() => this.invalidateDriversCache()));
  }

  getDrivers(forceRefresh = false): Observable<any> {
    if (forceRefresh || !this.driversCache$) {
      this.driversCache$ = this.http.get(`${this.baseUrl}/drivers`, {
        headers: this.getAuthHeaders()
      }).pipe(
        map((res: any) => Array.isArray(res) ? res.map((driver: any) => this.normalizeDriver(driver)) : []),
        shareReplay(1)
      );
    }
    return this.driversCache$;
  }

  private normalizeDriver(driver: any): any {
    const drId = driver?.dr_id ?? driver?.driver_id ?? driver?.cnic ?? '';
    const name = driver?.name ?? driver?.driver_name ?? '';
    const contact = driver?.contact_no ?? driver?.contactNumber ?? driver?.phone_no ?? '';
    const evId = driver?.ev_id ?? driver?.allocated_rikshaw ?? driver?.allocatedRikshaw ?? driver?.vehicle_id ?? '';
    const currentAddress = driver?.current_address ?? driver?.currentAddress ?? driver?.address ?? '';

    return {
      ...driver,
      dr_id: drId,
      driver_id: drId,
      cnic: drId,
      name,
      driver_name: name,
      contact_no: contact,
      contactNumber: contact,
      phone_no: contact,
      ev_id: evId,
      allocated_rikshaw: evId,
      allocatedRikshaw: evId,
      vehicle_id: evId,
      current_address: currentAddress,
      currentAddress,
      address: currentAddress
    };
  }

  private invalidateComplaintsCache(): void {
    this.complaintsCache$ = undefined;
  }

  private invalidateDriversCache(): void {
    this.driversCache$ = undefined;
  }

  private clearAllCache(): void {
    this.invalidateComplaintsCache();
    this.invalidateDriversCache();
  }
}
