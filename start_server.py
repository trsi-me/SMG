#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

# تحميل متغيرات البيئة
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # سيتم التعامل معها لاحقاً

def check_requirements():
    print("🔍 التحقق من المتطلبات...")
    
    # قائمة المتطلبات مع أسماء الاستيراد الصحيحة
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'python-multipart': 'multipart',  # مطلوب لـ FastAPI Form data
        'PyJWT': 'jwt',
        'Pillow': 'PIL',
        'numpy': 'numpy',
        'requests': 'requests',
        'pydantic': 'pydantic',
        'python-dotenv': 'dotenv',  # سيتم التحقق بشكل خاص
        'torch': 'torch',
        'torchvision': 'torchvision',
        'timm': 'timm'
    }
    
    # التحقق من dotenv بشكل خاص
    def check_dotenv():
        try:
            import dotenv
            return True
        except ImportError:
            try:
                from dotenv import load_dotenv
                return True
            except ImportError:
                return False
    
    # التحقق من python-multipart بشكل خاص
    def check_multipart():
        try:
            import multipart
            return True
        except ImportError:
            try:
                import importlib.util
                spec = importlib.util.find_spec("multipart")
                return spec is not None
            except:
                return False
    
    missing_packages = []
    torch_error = False
    
    for package_name, import_name in required_packages.items():
        try:
            # معالجة خاصة لـ dotenv
            if package_name == 'python-dotenv':
                if not check_dotenv():
                    print(f"❌ {package_name}")
                    missing_packages.append(package_name)
                else:
                    print(f"✅ {package_name}")
            # معالجة خاصة لـ python-multipart
            elif package_name == 'python-multipart':
                if not check_multipart():
                    print(f"❌ {package_name}")
                    missing_packages.append(package_name)
                else:
                    print(f"✅ {package_name}")
            else:
                __import__(import_name)
                print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing_packages.append(package_name)
        except OSError as e:
            # مشكلة DLL في PyTorch
            if 'torch' in package_name.lower():
                print(f"⚠️ {package_name} - مشكلة DLL (سيتم محاولة إصلاحها)")
                torch_error = True
                missing_packages.append(package_name)
            else:
                print(f"❌ {package_name} - خطأ: {e}")
                missing_packages.append(package_name)
        except Exception as e:
            print(f"❌ {package_name} - خطأ: {e}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📦 تثبيت الحزم المفقودة: {', '.join(missing_packages)}")
        
        # إذا كانت هناك مشكلة في PyTorch، أعد تثبيته
        if torch_error:
            print("\n🔧 محاولة إصلاح مشكلة PyTorch...")
            print("💡 قد تحتاج إلى تثبيت Visual C++ Redistributable من Microsoft")
            print("💡 أو إعادة تثبيت PyTorch يدوياً:")
            print("   pip uninstall torch torchvision")
            print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu")
        
        try:
            # تثبيت المكتبات المفقودة
            install_cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade'] + missing_packages
            
            # إذا كانت المشكلة في PyTorch، أعد تثبيته بشكل كامل
            if torch_error and ('torch' in missing_packages or 'torchvision' in missing_packages):
                print("\n🔧 إصلاح مشكلة PyTorch DLL...")
                print("🔄 إزالة PyTorch القديم...")
                
                # إزالة PyTorch بالكامل
                try:
                    subprocess.run([
                        sys.executable, '-m', 'pip', 'uninstall', 
                        'torch', 'torchvision', 'torchaudio', '-y'
                    ], check=False, capture_output=True)
                    print("✅ تم إزالة PyTorch القديم")
                except:
                    pass
                
                # إزالة torch من القائمة لتثبيته بشكل منفصل
                missing_without_torch = [p for p in missing_packages if 'torch' not in p.lower()]
                if missing_without_torch:
                    print(f"📦 تثبيت المكتبات الأخرى: {', '.join(missing_without_torch)}")
                    subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '--upgrade'
                    ] + missing_without_torch, check=False)
                
                # تثبيت PyTorch CPU فقط (أخف وأكثر استقراراً)
                print("\n🔄 تثبيت PyTorch CPU...")
                print("⏳ قد يستغرق هذا بضع دقائق...")
                
                try:
                    # محاولة 1: تثبيت من PyPI العادي
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', 
                        'torch', 'torchvision', '--no-cache-dir'
                    ], check=False, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        # محاولة 2: تثبيت من المصدر الرسمي CPU
                        print("🔄 محاولة تثبيت من المصدر الرسمي CPU...")
                        result = subprocess.run([
                            sys.executable, '-m', 'pip', 'install', 
                            'torch', 'torchvision', 
                            '--index-url', 'https://download.pytorch.org/whl/cpu',
                            '--no-cache-dir'
                        ], check=False, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ تم تثبيت PyTorch بنجاح")
                    else:
                        print("⚠️ فشل تثبيت PyTorch تلقائياً")
                        print("\n💡 جرب يدوياً:")
                        print("   pip uninstall torch torchvision -y")
                        print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu")
                        print("\n💡 أو ثبّت Visual C++ Redistributable:")
                        print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
                        
                except Exception as e:
                    print(f"⚠️ خطأ في تثبيت PyTorch: {e}")
                    print("\n💡 جرب يدوياً:")
                    print("   pip uninstall torch torchvision -y")
                    print("   pip install torch torchvision")
            else:
                subprocess.run(install_cmd, check=True)
            
            print("✅ تم تثبيت المتطلبات")
            
            # التحقق مرة أخرى
            print("\n🔍 التحقق مرة أخرى...")
            all_ok = True
            failed_packages = []
            
            for package_name, import_name in required_packages.items():
                try:
                    # معالجة خاصة لـ dotenv
                    if package_name == 'python-dotenv':
                        if not check_dotenv():
                            print(f"❌ {package_name} - لا يزال مفقوداً")
                            all_ok = False
                            failed_packages.append(package_name)
                        else:
                            print(f"✅ {package_name}")
                    # معالجة خاصة لـ python-multipart
                    elif package_name == 'python-multipart':
                        if not check_multipart():
                            print(f"❌ {package_name} - لا يزال مفقوداً")
                            all_ok = False
                            failed_packages.append(package_name)
                        else:
                            print(f"✅ {package_name}")
                    else:
                        __import__(import_name)
                        print(f"✅ {package_name}")
                except OSError as e:
                    # مشكلة DLL في PyTorch
                    if 'torch' in package_name.lower():
                        print(f"❌ {package_name} - مشكلة DLL (لا يزال)")
                        print(f"   الخطأ: {str(e)[:100]}")
                        all_ok = False
                        failed_packages.append(package_name)
                    else:
                        print(f"❌ {package_name} - خطأ: {e}")
                        all_ok = False
                        failed_packages.append(package_name)
                except Exception as e:
                    print(f"❌ {package_name} - لا يزال مفقوداً")
                    all_ok = False
                    failed_packages.append(package_name)
            
            if failed_packages and any('torch' in p.lower() for p in failed_packages):
                print("\n" + "="*50)
                print("⚠️ مشكلة PyTorch DLL لم تُحل تلقائياً")
                print("="*50)
                print("\n📋 الحلول المقترحة:")
                print("\n1️⃣ تثبيت Visual C++ Redistributable:")
                print("   - حمّل من: https://aka.ms/vs/17/release/vc_redist.x64.exe")
                print("   - ثبّت الملف")
                print("   - أعد تشغيل الكمبيوتر")
                print("\n2️⃣ إعادة تثبيت PyTorch يدوياً:")
                print("   pip uninstall torch torchvision torchaudio -y")
                print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu")
                print("\n3️⃣ استخدام إصدار أقدم من PyTorch:")
                print("   pip install torch==2.0.0 torchvision==0.15.0 --index-url https://download.pytorch.org/whl/cpu")
                print("\n4️⃣ تحديث pip:")
                print("   python -m pip install --upgrade pip")
                print("\n" + "="*50)
                print("💡 بعد تطبيق أي حل، أعد تشغيل: python start_server.py")
                print("="*50)
            
            return all_ok
            
        except subprocess.CalledProcessError as e:
            print(f"❌ فشل في تثبيت المتطلبات: {e}")
            print("\n💡 حاول تثبيتها يدوياً:")
            print(f"   pip install {' '.join(missing_packages)}")
            return False
    
    return True

def check_model():
    print("🤖 التحقق من نموذج النباتات...")
    
    model_paths = [
        Path(__file__).parent / 'ml' / 'models' / 'efficientnet_b4_v1.pt',
        Path(__file__).parent / 'backend' / 'models' / 'efficientnet_b4_v1.pt',
    ]
    
    for model_path in model_paths:
        if model_path.exists():
            print(f"✅ نموذج موجود: {model_path}")
            return True
    
    print("⚠️ نموذج النباتات غير موجود")
    print("💡 لإنشاء نموذج افتراضي، قم بتشغيل: python create_default_model.py")
    print("💡 أو قم بتدريب نموذج جديد: python train_model.py")
    return True

def ensure_env_file():
    """إنشاء ملف .env إذا لم يكن موجوداً"""
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    env_example = backend_dir / "env_example.txt"
    
    if env_file.exists():
        return  # الملف موجود
    
    if env_example.exists():
        try:
            # نسخ من env_example.txt إلى .env
            import shutil
            shutil.copy(env_example, env_file)
            print(f"📝 تم إنشاء ملف .env من env_example.txt")
            print("💡 يرجى تحديث إعدادات قاعدة البيانات في ملف .env")
            
            # إعادة تحميل متغيرات البيئة
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except:
                pass
        except Exception as e:
            print(f"⚠️ لم يتم إنشاء ملف .env تلقائياً: {e}")

def check_and_create_tables(connection):
    """التحقق من وجود الجداول وإنشائها إذا لم تكن موجودة"""
    try:
        import sqlite3
        cursor = connection.cursor()
        
        # التحقق من وجود جدول species (الأهم)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='species'")
        if not cursor.fetchone():
            print("⚠️ الجداول غير موجودة - جاري إنشائها تلقائياً...")
            
            # قراءة ملف SQL وإنشاء الجداول
            sql_file = Path(__file__).parent / 'sql' / 'create_tables_sqlite.sql'
            if sql_file.exists():
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    # تنفيذ جميع الاستعلامات
                    cursor.executescript(sql_content)
                    connection.commit()
                    print("✅ تم إنشاء الجداول بنجاح")
                except Exception as e:
                    print(f"⚠️ خطأ في إنشاء الجداول: {e}")
                    print("💡 يمكنك إنشاء الجداول يدوياً باستخدام: python setup_database.py")
            else:
                print(f"⚠️ ملف SQL غير موجود: {sql_file}")
                print("💡 قم بتشغيل: python setup_database.py")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"⚠️ خطأ في التحقق من الجداول: {e}")
        return False

def check_database():
    print("🗄️ التحقق من قاعدة البيانات SQLite...")
    
    # التأكد من وجود ملف .env
    ensure_env_file()
    
    try:
        import sqlite3
        
        # الحصول على مسار قاعدة البيانات
        db_path = os.getenv('DB_PATH', str(Path(__file__).parent / 'data' / 'smg_plants.db'))
        
        # التأكد من وجود المجلد
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # محاولة الاتصال بقاعدة البيانات
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        
        # التحقق من وجود الجداول وإنشائها إذا لزم الأمر
        check_and_create_tables(connection)
        
        # التحقق من وجود البيانات
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        except sqlite3.Error:
            user_count = 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM species")
            species_count = cursor.fetchone()[0]
        except sqlite3.Error:
            species_count = 0
        
        cursor.close()
        connection.close()
        
        print(f"✅ قاعدة البيانات SQLite متاحة ({user_count} مستخدم، {species_count} نوع نبات)")
        print(f"📁 موقع قاعدة البيانات: {db_path}")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        print("\n💡 الحلول المقترحة:")
        print("   1. قم بتشغيل: python setup_database.py")
        return False
    except Exception as e:
        print(f"❌ خطأ عام في قاعدة البيانات: {e}")
        print("💡 قم بتشغيل: python setup_database.py")
        return False

def start_server():
    print("🚀 بدء تشغيل خادم SMG...")
    
    backend_dir = Path(__file__).parent / "backend"
    main_py = backend_dir / "main.py"
    
    if not main_py.exists():
        print("❌ ملف main.py غير موجود")
        return False
    
    try:
        # تغيير المجلد إلى backend
        os.chdir(backend_dir)
        
        # تشغيل الخادم
        cmd = [sys.executable, "main.py"]
        print(f"🔄 تشغيل: {' '.join(cmd)}")
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف الخادم بواسطة المستخدم")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
    
    return True

def main():
    print("🌱 SMG Plant Recognition Server")
    print("=" * 40)
    
    # تحديث pip (اختياري)
    try:
        print("🔄 التحقق من إصدار pip...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # التحقق من الحاجة للتحديث (اختياري - يمكن تخطيه)
            pass
    except:
        pass  # تجاهل الأخطاء في التحقق من pip
    
    # التحقق من المتطلبات
    if not check_requirements():
        return
    
    # التحقق من النموذج
    check_model()
    
    # التحقق من قاعدة البيانات
    if not check_database():
        return
    
    # بدء تشغيل الخادم
    start_server()

if __name__ == "__main__":
    main()
