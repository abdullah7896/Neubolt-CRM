import { Component, output, HostListener } from '@angular/core';  // ✅ Added HostListener for resize
import { Router } from '@angular/router';
import { NavLeftComponent } from "./nav-left/nav-left.component";

@Component({
  selector: 'app-nav-bar',
  templateUrl: './nav-bar.component.html',
  styleUrls: ['./nav-bar.component.scss'],
  imports: [NavLeftComponent]
})
export class NavBarComponent {
  NavCollapse = output<boolean>();  // ✅ Output now emits the new state (optional: pass boolean for parent to use)
  NavCollapsedMob = output<boolean>();  // Same for mobile

  navCollapsed: boolean = false;  // ✅ Initialized to false (closed by default)
  windowWidth: number;
  // navCollapsedMob: boolean;  // ✅ Removed unused (unify with navCollapsed)

  constructor(private router: Router) {
    this.updateWindowWidth();  // ✅ Renamed for reuse
    // this.navCollapsedMob = false;  // No longer needed
  }

  // ✅ New method to handle resize dynamically
  @HostListener('window:resize', ['$event'])
  onResize(event: any) {
    this.updateWindowWidth();
  }

  private updateWindowWidth() {
    this.windowWidth = window.innerWidth;
  }

  // ✅ Updated: Toggle always, but emit only on desktop. Pass new state to child via [navCollapsed]
  navCollapse() {
    this.navCollapsed = !this.navCollapsed;  // Toggle locally first
    if (this.windowWidth >= 1025) {
      this.NavCollapse.emit(this.navCollapsed);  // Emit new state to parent
    }
    // On mobile, this toggle will still update [navCollapsed] input to child
  }

  // ✅ Updated: Now toggles locally and emits on mobile. (Assuming child click emits NavCollapsedMob on mobile)
  navCollapseMob() {
    if (this.windowWidth < 1025) {
      this.navCollapsed = !this.navCollapsed;  // ✅ Toggle locally (unifies with desktop)
      this.NavCollapsedMob.emit(this.navCollapsed);  // Emit new state to parent
    }
  }

  // ✅ Logout method (unchanged, but good as-is)
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