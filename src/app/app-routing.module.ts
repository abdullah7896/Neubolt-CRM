import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Project import
import { AdminComponent } from './theme/layouts/admin-layout/admin-layout.component';
import { DefaultComponent } from './demo/dashboard/default/default.component';
import { GuestLayoutComponent } from './theme/layouts/guest-layout/guest-layout.component';
import { DriverRegister } from './driver-register/driver-register';

const routes: Routes = [
  {
    path: '',
    component: AdminComponent,
    children: [
      {
        path: '',
        redirectTo: 'dashboard/default',
        pathMatch: 'full'
      },
       {
        path: 'Driver-Registration',
        component: DriverRegister
      },
      {
        path: 'dashboard/default',
        component: DefaultComponent
      }
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
