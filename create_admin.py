from app import app, db
from models import Admin

def create_initial_admin():
    """創建初始 Admin 帳號"""
    with app.app_context():
        # 檢查是否已存在 admin
        existing_admin = Admin.query.filter_by(username='admin').first()
        
        if existing_admin:
            print("Admin account already exists!")
            return
        
        # 創建新的 admin
        admin = Admin(
            username='admin',
            email='admin@example.com',
            is_super_admin=True
        )
        admin.set_password('admin123')  # 請在生產環境中更改！
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin account created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("⚠️  Please change the password in production!")

if __name__ == '__main__':
    create_initial_admin()