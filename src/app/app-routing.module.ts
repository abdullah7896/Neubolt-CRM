import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Project imports
import { AdminComponent } from './theme/layouts/admin-layout/admin-layout.component';
import { DefaultComponent } from './demo/dashboard/default/default.component';
import { GuestLayoutComponent } from './theme/layouts/guest-layout/guest-layout.component';
import { DriverRegister } from './driver-register/driver-register';
import { AuthGuard } from 'src/app/guards/auth-guard'; // ✅ Import the guard

const routes: Routes = [
  {
    path: '',
    component: AdminComponent,
    children: [
      {
        path: '',
        redirectTo: '/login',
        pathMatch: 'full'
      },
      {
        path: 'Driver-Registration',
        component: DriverRegister,
        canActivate: [AuthGuard] // ✅ Protect this route
      },
      {
        path: 'dashboard/default',
        component: DefaultComponent,
        canActivate: [AuthGuard] // ✅ Protect this route
      }
    ]
  },
  {
    path: '',
    component: GuestLayoutComponent,
    children: [
      {
        path: 'login',
        loadComponent: () => import('./demo/pages/authentication/auth-login/auth-login.component').then((c) => c.AuthLoginComponent)
      },
      // {
      //   path: 'register',
      //   loadComponent: () =>
      //     import('./demo/pages/authentication/auth-register/auth-register.component').then((c) => c.AuthRegisterComponent)
      // }
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard/default'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
