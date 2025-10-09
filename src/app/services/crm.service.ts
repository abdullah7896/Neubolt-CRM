import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CrmService {
  private baseAuthUrl = 'http://203.135.63.46:5000/neubolt/auth';
  private baseUrl = 'http://203.135.63.46:5000/neubolt/crm';
  private driverUrl = 'http://203.135.63.46:5000/neubolt';

  constructor(private http: HttpClient) {}

  // ✅ Get headers with token
  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    });
  }

  // ✅ Login API (store token)
  login(credentials: { username: string; password: string }): Observable<any> {
    return this.http.post(`${this.baseAuthUrl}/login`, credentials).pipe(
      tap((response: any) => {
        if (response && response.access_token) {
          localStorage.setItem('access_token', response.access_token);
        }
      })
    );
  }

  // ✅ Logout
  logout(): void {
    localStorage.removeItem('access_token');
  }

  // ✅ Get Driver Details
  getDriverDetails(cnic: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-drivers_info/${cnic}`, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Post Complaint
  postComplaint(complaint: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/complaints`, complaint, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Get All Complaints
  getComplaints(): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-complaints`, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Get Complaint by ID
  getComplaintById(id: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-complaints_id/${id}`, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Get Complaints by CNIC
  getComplaintsByCnic(cnic: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-complaints_cnic/${cnic}`, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Update Complaint
  updateComplaint(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/put-complaints/${id}`, data, {
      headers: this.getAuthHeaders()
    });
  }

  // ✅ Delete Complaint
  deleteComplaint(id: string, data: any): Observable<any> {
    return this.http.delete(`${this.baseUrl}/delete-complaints/${id}`, {
      headers: this.getAuthHeaders(),
      body: data
    });
  }

  // ✅ Driver APIs
  postDriver(driver: any): Observable<any> {
    return this.http.post(`${this.driverUrl}/ev_drivers`, driver, {
      headers: this.getAuthHeaders()
    });
  }

  getDrivers(): Observable<any> {
    return this.http.get(`${this.driverUrl}/get-ev_drivers`, {
      headers: this.getAuthHeaders()
    });
  }
}
