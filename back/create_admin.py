import sys
import os
from models import init_db, User, get_session

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_admin():
    db_path = os.path.join(os.path.dirname(__file__), 'shavzak.db')
    engine = init_db(db_path)
    session = get_session(engine)

    try:
        # Check if admin exists
        admin = session.query(User).filter_by(username='admin').first()
        if admin:
            print("Admin user already exists.")
            # Update password just in case
            admin.set_password('pahimatheadmin')
            admin.role = 'admin'
            admin.full_name = 'מנהל מערכת'
            session.commit()
            print("Admin password and role updated.")
        else:
            # Create new admin
            new_admin = User(
                username='admin',
                full_name='מנהל מערכת',
                role='admin'
            )
            new_admin.set_password('pahimatheadmin')
            session.add(new_admin)
            session.commit()
            print("Admin user created successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_admin()
