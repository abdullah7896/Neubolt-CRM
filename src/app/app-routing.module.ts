import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Project import
import { AdminComponent } from './theme/layouts/admin-layout/admin-layout.component';
import { DefaultComponent } from './demo/dashboard/default/default.component';
import { GuestLayoutComponent } from './theme/layouts/guest-layout/guest-layout.component';
import { DriverRegister } from './driver-register/driver-register';
import { AuthLoginComponent } from './demo/pages/authentication/auth-login/auth-login.component';

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
        component: DriverRegister
      },
      {
        path: 'dashboard/default',
        component: DefaultComponent
      },
     


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
      {
        path: 'register',
        loadComponent: () =>
          import('./demo/pages/authentication/auth-register/auth-register.component').then((c) => c.AuthRegisterComponent)
      },
      {
        path: 'register',
        loadComponent: () =>
          import('./demo/pages/authentication/auth-register/auth-register.component').then((c) => c.AuthRegisterComponent)
      },
      
     
    ]
  },
  // Optional: guest routes can be removed if not needed
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
