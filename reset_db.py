from app import app, db

with app.app_context():
    db.drop_all()
    print("✓ 舊數據庫表已刪除")
    db.create_all()
    print("✓ 新數據庫表已創建")
    print("✓ 新增 Order 表")