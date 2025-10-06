import os

class Config:
    # 秘密金鑰
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    
    # Session 配置
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 小時
    
    # 數據庫配置
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS 設置
    CORS_HEADERS = 'Content-Type'
    CORS_SUPPORTS_CREDENTIALS = True