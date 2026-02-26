from database import SessionLocal
from routers.users import Neubolt_User
from authentication import hash_password
import secrets

def update_password(email, new_password):
    db = SessionLocal()
    try:
        user = db.query(Neubolt_User).filter(Neubolt_User.email == email).first()
        if user:
            user.password = hash_password(new_password)
            db.commit()
            print(f"Successfully updated password for {email}")
        else:
            print(f"User {email} not found. Creating user...")
            # Generate a random 13-digit user_id (CNIC)
            user_id = "".join([str(secrets.randbelow(10)) for _ in range(13)])
            new_user = Neubolt_User(
                user_id=user_id,
                user_type="admin", # Assuming admin based on the context of CRM login
                username="ali",
                password=hash_password(new_password),
                display_name="Ali",
                email=email,
                contact_no="03" + "".join([str(secrets.randbelow(10)) for _ in range(9)])
            )
            db.add(new_user)
            db.commit()
            print(f"Successfully created user {email} with password {new_password}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_password("ali@example.com", "ali123")
