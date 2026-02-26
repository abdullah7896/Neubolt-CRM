import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CrmService } from 'src/app/services/crm.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-auth-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth-login.component.html',
  styleUrls: ['./auth-login.component.scss']
})
export class AuthLoginComponent {
  email: string = '';
  password: string = '';
  errorMessage: string = '';
  loading: boolean = false;

  constructor(private crmService: CrmService, private router: Router) { }

  onLogin() {
    if (!this.email || !this.password) {
      this.errorMessage = 'Please enter both email and password.';
      return;
    }

    this.loading = true;
    const credentials = {
      username: this.email,
      password: this.password
    };

    this.crmService.login(credentials).subscribe({
      next: (response) => {
        console.log('✅ Login success:', response);
        this.loading = false;

        // Token is already saved by CrmService.login()

        // Redirect
        this.router.navigate(['/dashboard/default']);
      },
      error: (err) => {
        console.error('❌ Login failed:', err);
        this.loading = false;
        this.errorMessage = err?.error?.detail || 'Invalid credentials. Please try again.';
      }
    });
  }
}
