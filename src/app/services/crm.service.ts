import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CrmService {
  private baseUrl = 'http://203.135.63.46:5000/neubolt/crm';
  private driverUrl = 'http://203.135.63.46:5000/neubolt';

  constructor(private http: HttpClient) {}

  // 1. Get Driver Details by CNIC (path parameter)
  getDriverDetails(cnic: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-drivers_info/${cnic}`);
  }

  // 2. Post Complaint
  postComplaint(complaint: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/complaints`, complaint);
  }

  // 3. Get Complaints
  getComplaints(): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-complaints`);
  }

  // Optional methods if needed
  getComplaintById(id: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-complaints_id/${id}`);
  }

  getComplaintsByCnic(cnic: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/get-complaints_cnic/${cnic}`);
  }

  updateComplaint(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/put-complaints/${id}`, data);
  }

  deleteComplaint(id: string, data: any): Observable<any> {
    return this.http.delete(`${this.baseUrl}/delete-complaints/${id}`, { body: data });
  }

  // ===================== New Driver APIs =====================

  // POST - Create/Register Driver
  postDriver(driver: any): Observable<any> {
    return this.http.post(`${this.driverUrl}/ev_drivers`, driver);
  }

  // GET - Get All Drivers
  getDrivers(): Observable<any> {
    return this.http.get(`${this.driverUrl}/get-ev_drivers`);
  }
}
