
from database import SessionLocal
from routers.users import Neubolt_User
from routers.vehicles import EV
from routers.drivers import Driver
from routers.stations import BSS
from routers.batteries import Battery
from routers.swaps import SWAP
from routers.complaints import Complaints
from authentication import hash_password
import uuid
from datetime import date, datetime

def seed():
    db = SessionLocal()
    try:
        # 1. Get or Create Admin
        admin = db.query(Neubolt_User).filter(Neubolt_User.username == "admin").first()
        if not admin:
            admin = Neubolt_User(
                user_id="3520212345678",
                user_type="admin",
                username="admin",
                password=hash_password("admin123"),
                display_name="System Administrator",
                contact_no="03001234567",
                email="admin@neubolt.com"
            )
            db.add(admin)
            db.flush()
        
        # 2. Add some EVs
        ev1 = EV(
            ev_id="EV-001",
            manufacturer="Neubolt Motors",
            category="Rickshaw",
            chasis_num="CH-123456",
            city="Lahore",
            user_id=admin.user_id
        )
        ev2 = EV(
            ev_id="EV-002",
            manufacturer="Neubolt Motors",
            category="Rickshaw",
            chasis_num="CH-789012",
            city="Karachi",
            user_id=admin.user_id
        )
        db.add_all([ev1, ev2])
        db.flush()

        # 3. Add some Drivers
        d1 = Driver(
            dr_id="35201-1111111-1",
            name="Ahmed Khan",
            contact_no="0301-1111111",
            ev_id=ev1.ev_id,
            user_id=admin.user_id,
            city="Lahore"
        )
        d2 = Driver(
            dr_id="42101-2222222-2",
            name="Sajid Ali",
            contact_no="0321-2222222",
            ev_id=ev2.ev_id,
            user_id=admin.user_id,
            city="Karachi"
        )
        db.add_all([d1, d2])
        db.flush()

        # 4. Add some BSS
        bss1 = BSS(
            bss_id="BSS-LHR-01",
            station_name="Lahore Central Station",
            location="Gulberg, Lahore",
            city="Lahore",
            user_id=admin.user_id
        )
        db.add(bss1)
        db.flush()

        # 5. Add some Batteries
        b1 = Battery(battery_id="BAT-001", company="Neubolt", model="N1", user_id=admin.user_id)
        b2 = Battery(battery_id="BAT-002", company="Neubolt", model="N1", user_id=admin.user_id)
        b3 = Battery(battery_id="BAT-003", company="Neubolt", model="N1", user_id=admin.user_id)
        b4 = Battery(battery_id="BAT-004", company="Neubolt", model="N1", user_id=admin.user_id)
        db.add_all([b1, b2, b3, b4])
        db.flush()

        # 6. Add some Complaints
        c1 = Complaints(
            complain_id="CMP-001",
            user_id=admin.user_id,
            dr_id=d1.dr_id,
            type="Battery",
            status="Pending",
            title="Battery Draining Fast",
            description="The battery drains from 100% to 20% in just 2 hours of driving.",
            location="Lahore"
        )
        c2 = Complaints(
            complain_id="CMP-002",
            user_id=admin.user_id,
            dr_id=d2.dr_id,
            type="Vehicle",
            status="Resolved",
            title="Brake Issue",
            description="The rear brakes are squeaking.",
            location="Karachi",
            resolved_time=datetime.now()
        )
        db.add_all([c1, c2])
        
        db.commit()
        print("Successfully seeded database with sample data!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
