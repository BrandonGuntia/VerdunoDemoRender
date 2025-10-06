#!/usr/bin/env python3
"""
開發環境設置腳本
重置數據庫並生成測試數據
"""

from app import app, db
import subprocess
import sys

def reset_database():
    """重置數據庫"""
    print("\n🗑️  Resetting database...")
    with app.app_context():
        db.drop_all()
        print("  ✅ Dropped all tables")
        db.create_all()
        print("  ✅ Created all tables")

def seed_test_data():
    """生成測試數據"""
    print("\n🌱 Seeding test data...")
    result = subprocess.run([sys.executable, 'seed_test_data.py'], 
                          capture_output=False)
    return result.returncode == 0

def main():
    """主函數"""
    print("="*60)
    print("🚀 DEVELOPMENT ENVIRONMENT SETUP")
    print("="*60)
    
    try:
        # 重置數據庫
        reset_database()
        
        # 生成測試數據
        if seed_test_data():
            print("\n✅ Development environment setup complete!")
        else:
            print("\n❌ Failed to seed test data")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()