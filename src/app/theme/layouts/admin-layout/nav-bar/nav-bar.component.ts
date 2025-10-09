import { Component, output } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-nav-bar',
  templateUrl: './nav-bar.component.html',
  styleUrls: ['./nav-bar.component.scss']
})
export class NavBarComponent {
  NavCollapse = output();
  NavCollapsedMob = output();

  navCollapsed: boolean;
  windowWidth: number;
  navCollapsedMob: boolean;

  constructor(private router: Router) {
    this.windowWidth = window.innerWidth;
    this.navCollapsedMob = false;
  }

  navCollapse() {
    if (this.windowWidth >= 1025) {
      this.navCollapsed = !this.navCollapsed;
      this.NavCollapse.emit();
    }
  }

  navCollapseMob() {
    if (this.windowWidth < 1025) {
      this.NavCollapsedMob.emit();
    }
  }

  // ✅ Logout method
  logout() {
    // 1️⃣ Clear any authentication data (token, user info, etc.)
    localStorage.clear();
    sessionStorage.clear();

    // 2️⃣ Navigate to login page
    this.router.navigate(['/login']).then(() => {
      // 3️⃣ Prevent going back using browser back button
      window.history.pushState(null, '', window.location.href);
      window.onpopstate = function () {
        window.history.go(1);
      };
    });
  }
}
