#!/usr/bin/env python3

import os
import sys
import sqlite3
from pathlib import Path

def get_database_path():
    """الحصول على مسار قاعدة بيانات SQLite"""
    db_dir = Path(__file__).parent / "data"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "smg_plants.db"

def install_backend_requirements():
    """تثبيت متطلبات Backend"""
    requirements_file = Path(__file__).parent / "backend" / "requirements.txt"
    
    if not requirements_file.exists():
        print("⚠️ ملف requirements.txt غير موجود")
        return False
    
    print("📦 تثبيت متطلبات Backend...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        print("✅ تم تثبيت متطلبات Backend بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت متطلبات Backend")
        if e.stdout:
            print(f"📋 الإخراج: {e.stdout[:500]}")
        if e.stderr:
            print(f"⚠️ الأخطاء: {e.stderr[:500]}")
        return False

def test_database_connection():
    """اختبار الاتصال بقاعدة البيانات SQLite"""
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(str(db_path))
        conn.close()
        print("✅ الاتصال بقاعدة البيانات SQLite نجح")
        return True
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

def setup_database():
    """إعداد قاعدة البيانات SQLite"""
    sql_dir = Path(__file__).parent / "sql"
    sql_file = sql_dir / "create_tables_sqlite.sql"
    
    if not sql_file.exists():
        print("❌ ملف create_tables_sqlite.sql غير موجود")
        return False
    
    print("🗄️ إعداد قاعدة البيانات SQLite...")
    
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # قراءة ملف SQL وتنفيذه
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # تنفيذ جميع الاستعلامات
        cursor.executescript(sql_content)
        
        # التحقق من إنشاء الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ تم إنشاء {len(tables)} جدول")
        
        # التحقق من البيانات
        cursor.execute("SELECT COUNT(*) FROM species")
        species_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"✅ قاعدة البيانات جاهزة ({user_count} مستخدم، {species_count} نوع نبات)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_env_file():
    """إنشاء ملف .env"""
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    
    db_path = get_database_path()
    
    env_content = f"""# إعدادات قاعدة البيانات SQLite
DB_PATH={db_path}

# إعدادات الخادم
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# إعدادات الأمان
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# إعدادات النموذج
MODEL_PATH=models/efficientnet_b4_v1.pt
MODEL_ARCH=efficientnet_b4

# إعدادات التطوير
DEBUG=True
LOG_LEVEL=INFO
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ تم إنشاء ملف .env في: {env_file}")

def main():
    print("🗄️ SMG Database Setup (SQLite)")
    print("=" * 30)
    
    # تثبيت متطلبات Backend
    if not install_backend_requirements():
        print("⚠️ تحذير: لم يتم تثبيت جميع المتطلبات")
        print("💡 يمكنك المتابعة، لكن قد تحتاج لتثبيت المتطلبات لاحقاً")
    
    # اختبار الاتصال
    if not test_database_connection():
        return
    
    # إعداد قاعدة البيانات
    if not setup_database():
        return
    
    # إنشاء ملف .env
    create_env_file()
    
    print("\n🎉 تم إعداد قاعدة البيانات بنجاح!")
    print(f"📁 موقع قاعدة البيانات: {get_database_path()}")
    print("📝 يمكنك الآن تشغيل الخادم باستخدام: python start_server.py")

if __name__ == "__main__":
    main()
