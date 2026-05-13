import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
import io
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import sqlite3
from sqlite3 import Error
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np
import requests
from dotenv import load_dotenv
import sys
from pathlib import Path
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets

# تحميل متغيرات البيئة
load_dotenv()

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مسار backend أولاً لـ plant_classifier.py، ثم ml لباقي الوحدات
_backend_dir = Path(__file__).resolve().parent
ml_path = _backend_dir.parent / 'ml'
sys.path.insert(0, str(ml_path))
sys.path.insert(0, str(_backend_dir))

# استيراد PlantClassifier لتحميل النموذج
try:
    from plant_classifier import PlantClassifier
    PLANT_CLASSIFIER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ PlantClassifier غير متوفر - سيتم استخدام تحميل النموذج المباشر")
    PLANT_CLASSIFIER_AVAILABLE = False
    PlantClassifier = None

# استيراد خدمات الطقس وصحة النبات
try:
    from weather_service import weather_service
    WEATHER_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ خدمة الطقس غير متوفرة")
    WEATHER_SERVICE_AVAILABLE = False
    weather_service = None

try:
    from hardware_service import hardware_service
    HARDWARE_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ خدمة الهاردوير غير متوفرة")
    HARDWARE_SERVICE_AVAILABLE = False
    hardware_service = None

try:
    from plant_health_model import plant_health_analyzer
    HEALTH_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ نموذج صحة النبات غير متوفر")
    HEALTH_MODEL_AVAILABLE = False
    plant_health_analyzer = None

# دالة lifespan للتعامل مع بدء وإيقاف التطبيق
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل SMG Plant Recognition API")
    logger.info("=" * 50)

    try:
        torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))
    except Exception:
        pass

    # التحقق من قاعدة البيانات والجداول
    logger.info("🗄️ التحقق من قاعدة البيانات...")
    if ensure_database_and_tables():
        logger.info("✅ قاعدة البيانات جاهزة")
    else:
        logger.warning("⚠️ تحذير: قد تكون هناك مشاكل في قاعدة البيانات")
    
    # تحميل نموذج التعرف على النباتات
    logger.info("📦 تحميل نموذج التعرف على النباتات...")
    if load_model():
        logger.info("✅ تم تحميل نموذج التعرف على النباتات بنجاح")
    else:
        logger.warning("⚠️ فشل في تحميل نموذج التعرف على النباتات")
    
    # تحميل نموذج صحة النبات
    logger.info("📦 تحميل نموذج صحة النبات...")
    if load_health_model():
        logger.info("✅ تم تحميل نموذج صحة النبات بنجاح")
    else:
        logger.warning("⚠️ نموذج صحة النبات غير متوفر - سيتم استخدام تحليل افتراضي")
    
    # التحقق من خدمة الطقس
    if WEATHER_SERVICE_AVAILABLE:
        logger.info("✅ خدمة الطقس متوفرة")
    else:
        logger.warning("⚠️ خدمة الطقس غير متوفرة")
    
    logger.info("=" * 50)
    logger.info("✅ تم تشغيل الخادم بنجاح")
    logger.info("=" * 50)
    
    yield
    
    # Shutdown
    logger.info("⏹️ إيقاف الخادم...")

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="SMG Plant Recognition API",
    description="API للتعرف على النباتات مع دمج بيانات الحساسات",
    version="1.0.0",
    lifespan=lifespan
)

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج، حدد النطاقات المسموحة
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# معالج استثناءات مخصص لأخطاء التحقق من البيانات
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    معالج مخصص لأخطاء التحقق من البيانات
    يتعامل مع حالات رفع الملفات التي تحتوي على بيانات ثنائية
    """
    def clean_value(value):
        """تنظيف القيمة من أي بيانات ثنائية"""
        if isinstance(value, bytes):
            return '<binary data>'
        elif isinstance(value, str):
            # إذا كانت النص طويل جداً أو يحتوي على أحرف غير قابلة للطباعة، استبدلها
            if len(value) > 1000:
                return '<large data>'
            # التحقق من وجود أحرف غير قابلة للطباعة (مثل البيانات الثنائية المحولة)
            try:
                value.encode('utf-8')
                # إذا كان النص يحتوي على الكثير من الأحرف غير القابلة للطباعة
                if sum(1 for c in value if not c.isprintable() and c not in '\n\r\t') > len(value) * 0.1:
                    return '<binary-like data>'
            except (UnicodeEncodeError, UnicodeDecodeError):
                return '<invalid encoding>'
        elif isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_value(item) for item in value]
        return value
    
    errors = exc.errors()
    
    # تنظيف الأخطاء من أي بيانات ثنائية
    cleaned_errors = []
    for error in errors:
        cleaned_error = {}
        for key, value in error.items():
            if key == 'ctx' and isinstance(value, dict):
                # تنظيف context
                cleaned_error[key] = {k: clean_value(v) for k, v in value.items()}
            elif key == 'input':
                # تنظيف input
                cleaned_error[key] = clean_value(value)
            else:
                cleaned_error[key] = clean_value(value) if isinstance(value, (bytes, str, dict, list)) else value
        
        cleaned_errors.append(cleaned_error)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": cleaned_errors,
            "message": "خطأ في التحقق من البيانات المرسلة"
        }
    )

# إنشاء مجلدات التحميل
uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
avatars_dir = uploads_dir / "avatars"
avatars_dir.mkdir(exist_ok=True)

@app.get("/uploads/avatars/{filename}")
async def get_avatar(filename: str):
    avatar_path = avatars_dir / filename
    if avatar_path.exists():
        return FileResponse(avatar_path)
    raise HTTPException(status_code=404, detail="الصورة غير موجودة")

# نماذج البيانات
class ScanRequest(BaseModel):
    image_base64: str
    device_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None

class SensorData(BaseModel):
    device_id: str
    soil_raw: int
    temperature_c: float
    humidity_percent: float
    battery: float
    timestamp: Optional[str] = None

class FeedbackRequest(BaseModel):
    scan_id: int
    is_correct: bool
    correct_species_id: Optional[int] = None
    feedback_text: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

# إعدادات قاعدة البيانات SQLite
DB_PATH = os.getenv('DB_PATH', str(Path(__file__).parent.parent / 'data' / 'smg_plants.db'))

# إعدادات الخادم
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('PORT', os.getenv('SERVER_PORT', '8000')))

# إعدادات JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# متغيرات النموذج
model = None
model_arch = None
species_classes = []
class_to_idx = {}
idx_to_class = {}

# متغيرات نموذج صحة النبات
health_model_loaded = False

def ensure_database_and_tables():
    """التحقق من وجود قاعدة البيانات والجداول وإنشائها إذا لزم الأمر"""
    try:
        logger.info(f"🗄️ التحقق من قاعدة البيانات SQLite: {DB_PATH}")
        
        # التأكد من وجود المجلد
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # محاولة الاتصال وإنشاء قاعدة البيانات والجداول
        try:
            # اختبار الاتصال فقط
            test_connection = get_db_connection()
            ensure_tables_exist(test_connection)
            test_connection.close()
            logger.info(f"✅ قاعدة البيانات SQLite جاهزة: {DB_PATH}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ تحذير في الاتصال بقاعدة البيانات: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من قاعدة البيانات: {e}")
        return False

def ensure_tables_exist(connection):
    """التحقق من وجود الجداول وإنشائها إذا لم تكن موجودة"""
    try:
        cursor = connection.cursor()
        
        # التحقق من وجود جدول species
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='species'")
        if not cursor.fetchone():
            logger.info("⚠️ الجداول غير موجودة - جاري إنشائها تلقائياً...")
            
            # قراءة ملف SQL
            sql_file = Path(__file__).parent.parent / 'sql' / 'create_tables_sqlite.sql'
            if sql_file.exists():
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    # تنفيذ جميع الاستعلامات
                    cursor.executescript(sql_content)
                    connection.commit()
                    logger.info("✅ تم إنشاء الجداول بنجاح")
                except Exception as e:
                    logger.error(f"❌ خطأ في إنشاء الجداول: {e}")
            else:
                logger.warning(f"⚠️ ملف SQL غير موجود: {sql_file}")
        
        cursor.close()
    except Exception as e:
        logger.warning(f"⚠️ خطأ في التحقق من الجداول: {e}")

def get_db_connection():
    """الحصول على اتصال بقاعدة البيانات SQLite"""
    try:
        # التأكد من وجود المجلد
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # الاتصال بقاعدة البيانات SQLite
        connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        connection.row_factory = sqlite3.Row  # للحصول على نتائج كـ dict
        
        # التحقق من وجود الجداول وإنشائها تلقائياً
        ensure_tables_exist(connection)
        
        return connection
    except Exception as e:
        logger.error(f"خطأ في الاتصال بقاعدة البيانات SQLite: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الاتصال بقاعدة البيانات")

def load_model():
    global model, model_arch, species_classes, class_to_idx, idx_to_class
    
    try:
        # تحديد مسار النموذج - البحث في عدة مواقع
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'models', 'efficientnet_b4_v1.pt'),
            os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'efficientnet_b4_v1.pt'),
            os.path.join(Path(__file__).parent.parent, 'ml', 'models', 'efficientnet_b4_v1.pt'),
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path or not os.path.exists(model_path):
            logger.warning(f"ملف النموذج غير موجود في المسارات التالية:")
            for path in possible_paths:
                logger.warning(f"  - {path}")
            return False
        
        # تحميل النموذج
        try:
            checkpoint = torch.load(
                model_path,
                map_location='cpu',
                weights_only=False,
                mmap=True,
            )
        except TypeError:
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
        
        # التحقق من تنسيق الملف
        if isinstance(checkpoint, dict):
            # تنسيق جديد: يحتوي على model_state_dict
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
                model_arch = checkpoint.get('architecture', checkpoint.get('arch', 'efficientnet_b4'))
                num_classes = checkpoint.get('num_classes', len(checkpoint.get('species_classes', [])))
                
                # التحقق من بنية النموذج المحفوظ
                uses_timm = any('backbone.blocks' in key or 'backbone.conv_stem' in key for key in state_dict.keys())
                
                # إنشاء النموذج
                if PLANT_CLASSIFIER_AVAILABLE and PlantClassifier:
                    # إذا كان النموذج يستخدم timm، نحتاج لإنشاءه باستخدام timm
                    if uses_timm:
                        logger.info("🔍 النموذج يستخدم timm - إنشاء النموذج باستخدام timm...")
                        try:
                            import timm
                            # إنشاء النموذج باستخدام timm مباشرة
                            model = PlantClassifier(num_classes, model_arch, pretrained=False)
                            # استبدال backbone بـ timm model
                            model.backbone = timm.create_model('efficientnet_b4', pretrained=False, num_classes=num_classes)
                            # تحميل الأوزان
                            model.load_state_dict(state_dict, strict=False)
                            logger.info("✅ تم تحميل النموذج باستخدام timm بنجاح")
                        except ImportError:
                            logger.error("❌ timm غير مثبت - لا يمكن تحميل النموذج")
                            logger.info("💡 قم بتثبيت timm: pip install timm")
                            return False
                        except Exception as e:
                            logger.warning(f"⚠️ خطأ في تحميل النموذج باستخدام timm: {e}")
                            logger.info("🔄 محاولة تحميل مع strict=False...")
                            try:
                                model = PlantClassifier(num_classes, model_arch, pretrained=False)
                                model.load_state_dict(state_dict, strict=False)
                            except Exception as e2:
                                logger.error(f"❌ فشل تحميل النموذج: {e2}")
                                return False
                    else:
                        # النموذج يستخدم torchvision
                        logger.info("🔍 النموذج يستخدم torchvision - إنشاء النموذج...")
                        model = PlantClassifier(num_classes, model_arch, pretrained=False)
                        try:
                            model.load_state_dict(state_dict)
                        except Exception as e:
                            logger.warning(f"⚠️ خطأ في تحميل النموذج: {e}")
                            logger.info("🔄 محاولة تحميل مع strict=False...")
                            model.load_state_dict(state_dict, strict=False)
                else:
                    logger.error("❌ PlantClassifier غير متوفر - لا يمكن تحميل النموذج")
                    return False
                
                # تحميل فئات الأنواع
                species_classes = checkpoint.get('species_classes', [])
                class_to_idx = checkpoint.get('class_to_idx', {})
                idx_to_class = checkpoint.get('idx_to_class', {})
                
                # تحويل مفاتيح idx_to_class إلى أعداد صحيحة إذا كانت strings
                if idx_to_class and isinstance(list(idx_to_class.keys())[0], str):
                    logger.info("🔄 تحويل مفاتيح idx_to_class من strings إلى integers...")
                    idx_to_class = {int(k): v for k, v in idx_to_class.items()}
                
                # إذا لم تكن الفئات موجودة، حاول إنشائها من num_classes
                if not species_classes and num_classes:
                    logger.warning("⚠️ فئات الأنواع غير موجودة في النموذج")
                    species_classes = [f"class_{i}" for i in range(num_classes)]
                    class_to_idx = {cls: idx for idx, cls in enumerate(species_classes)}
                    idx_to_class = {idx: cls for cls, idx in class_to_idx.items()}
                
                # تسجيل معلومات الفئات
                logger.info(f"📋 عدد الفئات المحملة: {len(species_classes)}")
                logger.info(f"📋 الفئات المحملة: {species_classes[:10]}...")  # أول 10 فئات
                logger.info(f"📋 عدد مفاتيح idx_to_class: {len(idx_to_class)}")
                if idx_to_class:
                    logger.info(f"📋 أمثلة من idx_to_class: {dict(list(idx_to_class.items())[:5])}")
            elif 'model' in checkpoint:
                # تنسيق قديم: يحتوي على model مباشرة
                model = checkpoint['model']
                model_arch = checkpoint.get('arch', 'efficientnet_b4')
                species_classes = checkpoint.get('species_classes', [])
                class_to_idx = checkpoint.get('class_to_idx', {})
                idx_to_class = checkpoint.get('idx_to_class', {})
            else:
                # قد يكون state_dict مباشرة
                logger.warning("⚠️ تنسيق غير معروف - محاولة تحميل كـ state_dict")
                if PLANT_CLASSIFIER_AVAILABLE and PlantClassifier:
                    # نحتاج لمعرفة num_classes و arch
                    logger.error("❌ لا يمكن تحديد معمارية النموذج وعدد الفئات")
                    return False
                else:
                    logger.error("❌ PlantClassifier غير متوفر")
                    return False
        else:
            # قد يكون state_dict مباشرة (تنسيق قديم جداً)
            logger.warning("⚠️ تنسيق قديم جداً - محاولة تحميل مباشر")
            if PLANT_CLASSIFIER_AVAILABLE and PlantClassifier:
                logger.error("❌ لا يمكن تحديد معمارية النموذج وعدد الفئات")
                return False
            else:
                logger.error("❌ PlantClassifier غير متوفر")
                return False
        
        model.eval()
        
        logger.info(f"✅ تم تحميل النموذج بنجاح: {model_arch}")
        logger.info(f"📊 عدد الفئات: {len(species_classes)}")
        
        # التحقق من صحة الفئات
        if not species_classes:
            logger.error("❌ لا توجد فئات محملة!")
            return False
        
        if not idx_to_class:
            logger.error("❌ idx_to_class فارغ!")
            return False
        
        # التحقق من تطابق عدد الفئات
        if len(species_classes) != len(idx_to_class):
            logger.warning(f"⚠️ عدد الفئات ({len(species_classes)}) لا يطابق عدد مفاتيح idx_to_class ({len(idx_to_class)})")
        
        # عرض جميع الفئات المحملة
        logger.info("=" * 50)
        logger.info("📋 جميع الفئات المحملة:")
        for idx, name in sorted(idx_to_class.items())[:20]:  # أول 20 فئة
            logger.info(f"  [{idx}] {name}")
        if len(idx_to_class) > 20:
            logger.info(f"  ... و {len(idx_to_class) - 20} فئة أخرى")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"خطأ في تحميل النموذج: {e}")
        return False

def load_health_model():
    global health_model_loaded
    
    if not HEALTH_MODEL_AVAILABLE or plant_health_analyzer is None:
        logger.warning("نموذج صحة النبات غير متوفر")
        return False
    
    try:
        # تحديد مسار نموذج الصحة - البحث في عدة مواقع
        possible_health_paths = [
            os.path.join(os.path.dirname(__file__), 'models', 'plant_health_v1.pt'),
            os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'plant_health_v1.pt'),
            os.path.join(Path(__file__).parent.parent, 'ml', 'models', 'plant_health_v1.pt'),
        ]
        
        health_model_path = None
        for path in possible_health_paths:
            if os.path.exists(path):
                health_model_path = path
                break
        
        if not health_model_path or not os.path.exists(health_model_path):
            logger.warning(f"ملف نموذج الصحة غير موجود في المسارات التالية:")
            for path in possible_health_paths:
                logger.warning(f"  - {path}")
            logger.info("سيتم استخدام تحليل افتراضي لصحة النبات")
            return False
        
        # تحميل النموذج
        success = plant_health_analyzer.load_model(health_model_path)
        
        if success:
            health_model_loaded = True
            logger.info("✅ تم تحميل نموذج صحة النبات بنجاح")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل نموذج صحة النبات: {e}")
        return False

def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    try:
        # تحويل bytes إلى صورة
        image = Image.open(io.BytesIO(image_bytes))
        
        # تسجيل معلومات الصورة
        logger.info(f"📷 حجم الصورة الأصلي: {image.size}, النمط: {image.mode}")
        
        # تحويل إلى RGB إذا لزم الأمر
        if image.mode != 'RGB':
            logger.info(f"🔄 تحويل الصورة من {image.mode} إلى RGB")
            image = image.convert('RGB')
        
        # تحسين الصورة قبل المعالجة
        # تقليل الضوضاء وتحسين التباين
        from PIL import ImageEnhance
        
        # تحسين التباين قليلاً
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)  # زيادة التباين بنسبة 10%
        
        # تحسين الحدة قليلاً
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)  # زيادة الحدة بنسبة 10%
        
        # تحويلات الصورة - استخدام نفس التحويلات المستخدمة في التدريب
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # تطبيق التحويلات
        image_tensor = transform(image).unsqueeze(0)
        
        logger.info(f"✅ تمت معالجة الصورة بنجاح - الشكل: {image_tensor.shape}")
        
        return image_tensor
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الصورة: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"خطأ في معالجة الصورة: {str(e)}")

def predict_species(image_tensor: torch.Tensor) -> Dict[str, Any]:
    global model, species_classes, idx_to_class
    
    if model is None:
        raise HTTPException(status_code=500, detail="النموذج غير محمل")
    
    # التحقق من وجود فئات محملة
    if not idx_to_class:
        logger.error("❌ فئات الأنواع غير محملة! idx_to_class فارغ")
        logger.error(f"species_classes: {species_classes}")
        raise HTTPException(status_code=500, detail="فئات الأنواع غير محملة - يرجى إعادة تحميل النموذج")
    
    try:
        with torch.no_grad():
            # التنبؤ
            outputs = model(image_tensor)
            
            # تسجيل معلومات التشخيص
            logger.info(f"🔍 شكل outputs: {outputs.shape}")
            logger.info(f"🔍 قيم outputs (أول 5): {outputs[0][:5].tolist()}")
            
            probabilities = F.softmax(outputs, dim=1)
            
            # الحصول على أفضل 3 توقعات
            top3_prob, top3_indices = torch.topk(probabilities, 3, dim=1)
            
            # تسجيل معلومات التشخيص
            logger.info(f"🔍 أفضل 3 فهارس: {top3_indices[0].tolist()}")
            logger.info(f"🔍 أفضل 3 احتمالات: {top3_prob[0].tolist()}")
            logger.info(f"🔍 عدد الفئات المتاحة: {len(idx_to_class)}")
            logger.info(f"🔍 الفئات المتاحة: {list(idx_to_class.values())[:10]}...")  # أول 10 فئات
            
            # تحويل النتائج
            predictions = []
            for i in range(3):
                idx = top3_indices[0][i].item()
                prob = top3_prob[0][i].item()
                
                # التحقق من وجود الفهرس في القاموس
                if idx not in idx_to_class:
                    logger.warning(f"⚠️ الفهرس {idx} غير موجود في idx_to_class!")
                    logger.warning(f"⚠️ الفهارس المتاحة: {list(idx_to_class.keys())[:10]}")
                    species_name = f"Unknown_{idx}"
                else:
                    species_name = idx_to_class[idx]
                
                logger.info(f"🔍 التنبؤ {i+1}: الفهرس={idx}, الاسم={species_name}, الثقة={prob:.4f}")
                
                predictions.append({
                    'species_name': species_name,
                    'confidence': prob,
                    'rank': i + 1
                })
            
            # التحقق من أن التنبؤات متنوعة
            if len(set([p['species_name'] for p in predictions])) == 1:
                logger.warning(f"⚠️ جميع التنبؤات متشابهة: {predictions[0]['species_name']}")
                logger.warning(f"⚠️ قد تكون هناك مشكلة في النموذج أو البيانات")
            
            return {
                'predictions': predictions,
                'top_prediction': predictions[0],
                'confidence': predictions[0]['confidence']
            }
            
    except Exception as e:
        logger.error(f"❌ خطأ في التنبؤ: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"خطأ في التنبؤ: {str(e)}")

def get_species_info(species_name: str) -> Dict[str, Any]:
    """
    البحث عن معلومات النبات في قاعدة البيانات
    """
    try:
        logger.info(f"🔍 البحث عن معلومات النبات: '{species_name}'")
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # البحث الدقيق أولاً
        query = """
        SELECT * FROM species 
        WHERE scientific_name = ? OR common_name_ar = ? OR common_name_en = ?
        """
        cursor.execute(query, (species_name, species_name, species_name))
        row = cursor.fetchone()
        species_info = dict(row) if row else None
        
        # إذا لم يتم العثور عليه، حاول البحث الجزئي (LIKE)
        if not species_info:
            logger.warning(f"⚠️ لم يتم العثور على '{species_name}' بالبحث الدقيق - محاولة البحث الجزئي...")
            
            # إزالة "ال" من البداية للبحث
            name_without_al = species_name.replace('ال', '').strip() if species_name.startswith('ال') else species_name
            
            query_like = """
            SELECT * FROM species 
            WHERE common_name_ar LIKE ? 
               OR common_name_ar LIKE ?
               OR scientific_name LIKE ?
            LIMIT 1
            """
            cursor.execute(query_like, (f'%{species_name}%', f'%{name_without_al}%', f'%{species_name}%'))
            row = cursor.fetchone()
            species_info = dict(row) if row else None
            
            if species_info:
                logger.info(f"✅ تم العثور على النبات بالبحث الجزئي: {species_info.get('common_name_ar', 'غير معروف')}")
            else:
                logger.warning(f"❌ لم يتم العثور على '{species_name}' حتى بالبحث الجزئي")
        
        if species_info:
            logger.info(f"✅ تم العثور على معلومات النبات:")
            logger.info(f"   - ID: {species_info.get('id')}")
            logger.info(f"   - الاسم العربي: {species_info.get('common_name_ar')}")
            logger.info(f"   - الاسم العلمي: {species_info.get('scientific_name')}")
        else:
            logger.warning(f"❌ لا توجد معلومات في قاعدة البيانات للنبات: '{species_name}'")
            logger.warning(f"💡 قد تحتاج إلى إضافة هذا النبات إلى قاعدة البيانات")
        
        cursor.close()
        connection.close()
        
        return species_info
        
    except Exception as e:
        logger.error(f"❌ خطأ في الحصول على معلومات النوع: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(user_id: int, username: str) -> str:
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_token(authorization: Optional[str] = Header(None, alias="Authorization")) -> Dict[str, Any]:
    if authorization is None:
        raise HTTPException(status_code=401, detail="رمز الوصول مطلوب")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="نوع المصادقة غير صحيح")
    except ValueError:
        raise HTTPException(status_code=401, detail="رمز الوصول غير صحيح")
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="انتهت صلاحية الرمز")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="رمز غير صحيح")

def get_sensor_data(device_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT * FROM sensor_snapshots 
        WHERE device_id = ? AND created_at >= datetime('now', '-' || ? || ' hours')
        ORDER BY created_at DESC
        """
        cursor.execute(query, (device_id, hours))
        rows = cursor.fetchall()
        sensor_data = [dict(row) for row in rows]
        
        cursor.close()
        connection.close()
        
        return sensor_data
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على بيانات الحساسات: {e}")
        return []

def generate_care_instructions(species_info: Dict[str, Any], sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not species_info:
        return {
            'watering_needed': False,
            'sunlight_level': 'medium',
            'temperature_status': 'normal',
            'care_instructions': 'لا توجد معلومات كافية عن هذا النوع',
            'recommendations': []
        }
    
    recommendations = []
    
    # تحليل بيانات التربة
    if sensor_data:
        latest_sensor = sensor_data[0]
        soil_percent = (1023 - latest_sensor['soil_raw']) / 1023 * 100
        
        if soil_percent < 30:
            recommendations.append("النبات يحتاج إلى سقي فوري")
        elif soil_percent < 50:
            recommendations.append("النبات يحتاج إلى سقي قريباً")
        else:
            recommendations.append("مستوى الرطوبة مناسب")
        
        # تحليل درجة الحرارة
        temp = latest_sensor['temperature_c']
        temp_min = species_info.get('temp_min', 15)
        temp_max = species_info.get('temp_max', 30)
        
        if temp < temp_min:
            recommendations.append("درجة الحرارة منخفضة جداً")
        elif temp > temp_max:
            recommendations.append("درجة الحرارة مرتفعة جداً")
        else:
            recommendations.append("درجة الحرارة مناسبة")
    
    return {
        'watering_needed': soil_percent < 40 if sensor_data else False,
        'sunlight_level': species_info.get('sunlight_requirements', 'medium'),
        'temperature_status': 'normal',
        'care_instructions': species_info.get('care_text_ar', 'لا توجد تعليمات متاحة'),
        'recommendations': recommendations
    }

# Routes

@app.get("/")
async def root():
    return {"message": "SMG Plant Recognition API", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "species_model_loaded": model is not None,
            "health_model_loaded": health_model_loaded,
            "weather_service_available": WEATHER_SERVICE_AVAILABLE,
            "hardware_service_available": HARDWARE_SERVICE_AVAILABLE,
            "database_connected": True
        },
        "features": {
            "plant_identification": model is not None,
            "health_detection": HEALTH_MODEL_AVAILABLE,
            "weather_integration": WEATHER_SERVICE_AVAILABLE,
            "sensor_integration": True,
            "hardware_integration": HARDWARE_SERVICE_AVAILABLE,
            "lcd_display": HARDWARE_SERVICE_AVAILABLE
        }
    }

def process_scan_result(image_bytes: bytes, device_id: Optional[str] = None, 
                        location: Optional[Dict[str, float]] = None, 
                        user_id: Optional[int] = None):
    """
    دالة مشتركة لمعالجة نتيجة المسح
    """
    # معالجة الصورة
    image_tensor = preprocess_image(image_bytes)
    
    # التنبؤ بنوع النبات
    prediction_result = predict_species(image_tensor)
    
    # الحصول على معلومات النوع
    species_name = prediction_result['top_prediction']['species_name']
    logger.info(f"🌿 التنبؤ الرئيسي: {species_name} (الثقة: {prediction_result['top_prediction']['confidence']:.4f})")
    logger.info(f"📊 جميع التنبؤات: {[p['species_name'] for p in prediction_result['predictions']]}")
    
    species_info = get_species_info(species_name)
    
    # إذا لم يتم العثور على النبات، جرب التنبؤات الأخرى
    if not species_info and len(prediction_result['predictions']) > 1:
        logger.info("🔄 لم يتم العثور على النبات الأول - محاولة التنبؤات الأخرى...")
        for pred in prediction_result['predictions'][1:]:
            logger.info(f"🔍 محاولة البحث عن: {pred['species_name']}")
            species_info = get_species_info(pred['species_name'])
            if species_info:
                logger.info(f"✅ تم العثور على معلومات للنبات: {pred['species_name']}")
                species_name = pred['species_name']  # تحديث الاسم
                break
    
    # الحصول على بيانات الحساسات
    sensor_data = []
    latest_sensor = None
    if device_id:
        sensor_data = get_sensor_data(device_id)
        if sensor_data:
            latest_sensor = sensor_data[0]
    
    # تحليل صحة النبات
    health_analysis = None
    if HEALTH_MODEL_AVAILABLE and plant_health_analyzer:
        try:
            health_analysis = plant_health_analyzer.analyze_comprehensive(
                image_tensor,
                latest_sensor,
                species_info
            )
            logger.info(f"✅ تحليل صحة النبات: {health_analysis.get('health_status_ar', 'غير معروف')}")
        except Exception as e:
            logger.error(f"❌ خطأ في تحليل صحة النبات: {e}")
            health_analysis = {
                'health_status': 'unknown',
                'health_status_ar': 'غير معروف',
                'confidence': 0.0,
                'recommendations': [],
                'warnings': []
            }
    else:
        health_analysis = {
            'health_status': 'unknown',
            'health_status_ar': 'غير معروف',
            'confidence': 0.0,
            'recommendations': ['نموذج صحة النبات غير متوفر'],
            'warnings': []
        }
    
    # الحصول على بيانات الطقس
    weather_data = None
    weather_advice = None
    watering_decision = None
    if WEATHER_SERVICE_AVAILABLE and weather_service and location:
        try:
            lat = location.get('latitude')
            lon = location.get('longitude')
            
            if lat and lon:
                weather_data = weather_service.get_weather_data(lat, lon)
                weather_advice = weather_service.generate_weather_advice(weather_data, species_info)
                
                # قرار السقي بناءً على الطقس
                soil_moisture = None
                if latest_sensor:
                    soil_moisture = (1023 - latest_sensor.get('soil_raw', 500)) / 1023 * 100
                
                watering_decision = weather_service.should_water_plant(
                    weather_data,
                    soil_moisture,
                    species_info
                )
                
                logger.info(f"✅ بيانات الطقس: {weather_data.get('weather_description', 'غير معروف')}")
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على بيانات الطقس: {e}")
    
    # توليد تعليمات العناية الشاملة
    care_instructions = generate_care_instructions(species_info, sensor_data)
    
    # دمج التوصيات من جميع المصادر
    all_recommendations = []
    all_warnings = []
    
    # إضافة توصيات صحة النبات
    if health_analysis:
        all_recommendations.extend(health_analysis.get('recommendations', []))
        all_warnings.extend(health_analysis.get('warnings', []))
    
    # إضافة توصيات الطقس
    if weather_advice:
        all_recommendations.extend(weather_advice.get('recommendations', []))
        all_warnings.extend(weather_advice.get('warnings', []))
    
    # إضافة توصيات العناية الأساسية
    all_recommendations.extend(care_instructions.get('recommendations', []))
    
    # عرض النتيجة على LCD إذا كان هناك جهاز متصل
    if HARDWARE_SERVICE_AVAILABLE and hardware_service and device_id:
        try:
            # البحث عن منفذ الجهاز
            connected_devices = hardware_service.get_connected_devices()
            for device in connected_devices:
                if device.get('port'):
                    port = device['port']
                    plant_name_ar = species_info.get('common_name_ar', species_name) if species_info else species_name
                    health_status_ar = health_analysis.get('health_status_ar', 'غير معروف') if health_analysis else 'غير معروف'
                    
                    # عرض معلومات النبات على LCD
                    hardware_service.display_plant_info(
                        port,
                        plant_name_ar[:12],
                        health_status_ar[:12]
                    )
                    logger.info(f"✅ تم عرض معلومات النبات على LCD: {port}")
                    break
        except Exception as e:
            logger.warning(f"⚠️ فشل عرض المعلومات على LCD: {e}")
    
    # حفظ المسح في قاعدة البيانات
    connection = get_db_connection()
    cursor = connection.cursor()
    
    species_id = species_info.get('id') if species_info else None
    sensor_snapshot_id = latest_sensor.get('id') if latest_sensor else None
    
    # محاولة الإدراج مع جميع الأعمدة أولاً
    try:
        insert_query = """
        INSERT INTO scans (
            user_id, species_id, confidence, image_path, 
            plant_health_status, health_confidence, health_details,
            sensor_snapshot_id, latitude, longitude, weather_data,
            prediction_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            user_id,
            species_id,
            prediction_result['confidence'],
            'scan_image.jpg',  # مسار مؤقت
            health_analysis.get('health_status', 'unknown') if health_analysis else 'unknown',
            health_analysis.get('confidence', 0.0) if health_analysis else 0.0,
            json.dumps(health_analysis, ensure_ascii=False) if health_analysis else None,
            sensor_snapshot_id,
            location.get('latitude') if location else None,
            location.get('longitude') if location else None,
            json.dumps(weather_data, ensure_ascii=False) if weather_data else None,
            json.dumps(prediction_result, ensure_ascii=False),
            datetime.now()
        ))
    except Exception as e:
        # إذا فشل، حاول بدون الأعمدة المتقدمة (للقواعد القديمة)
        if 'Unknown column' in str(e):
            logger.warning(f"⚠️ بعض الأعمدة غير موجودة - استخدام الإدراج الأساسي: {e}")
            try:
                # محاولة بدون أعمدة صحة النبات و weather_data
                insert_query = """
                INSERT INTO scans (
                    user_id, species_id, confidence, image_path, 
                    sensor_snapshot_id, latitude, longitude,
                    prediction_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_query, (
                    user_id,
                    species_id,
                    prediction_result['confidence'],
                    'scan_image.jpg',  # مسار مؤقت
                    sensor_snapshot_id,
                    location.get('latitude') if location else None,
                    location.get('longitude') if location else None,
                    json.dumps(prediction_result, ensure_ascii=False),
                    datetime.now()
                ))
            except Exception as e2:
                # إذا فشل أيضاً، استخدم فقط الأعمدة الأساسية جداً
                if 'Unknown column' in str(e2):
                    logger.warning(f"⚠️ استخدام الإدراج الأساسي جداً: {e2}")
                    insert_query = """
                    INSERT INTO scans (
                        user_id, species_id, confidence, image_path, 
                        prediction_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_query, (
                        user_id,
                        species_id,
                        prediction_result['confidence'],
                        'scan_image.jpg',  # مسار مؤقت
                        json.dumps(prediction_result, ensure_ascii=False),
                        datetime.now()
                    ))
                else:
                    raise
        else:
            raise
    
    scan_id = cursor.lastrowid
    connection.commit()
    cursor.close()
    connection.close()
    
    # بناء الاستجابة الشاملة
    response = {
        "scan_id": scan_id,
        "species_prediction": {
            "top_prediction": prediction_result['top_prediction'],
            "all_predictions": prediction_result['predictions'],
            "species_info": species_info
        },
        "plant_health": health_analysis,
        "weather": {
            "current_weather": weather_data,
            "weather_advice": weather_advice,
            "watering_decision": watering_decision
        } if weather_data else None,
        "sensor_data": {
            "latest": latest_sensor,
            "history": sensor_data[-5:] if sensor_data else []
        },
        "care_instructions": care_instructions,
        "comprehensive_recommendations": {
            "recommendations": all_recommendations,
            "warnings": all_warnings
        },
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"✅ تم مسح النبات بنجاح - ID: {scan_id}")
    return response

@app.post("/api/v1/scan")
async def scan_plant(
    request: Request,
    scan_request: Optional[ScanRequest] = None,
    image: Optional[UploadFile] = File(None),
    device_id: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    user_id: Optional[int] = Form(None),
    soil_raw: Optional[int] = Form(None),
    temperature: Optional[float] = Form(None),
    humidity: Optional[float] = Form(None)
):
    """
    Endpoint لمسح النبات - يدعم كلا التنسيقين:
    1. JSON مع image_base64 (للاختبار)
    2. multipart/form-data مع ملف صورة (للتطبيق المحمول)
    """
    try:
        image_bytes = None
        
        # التحقق من نوع الطلب
        content_type = request.headers.get("content-type", "")
        
        if "multipart/form-data" in content_type:
            # طلب multipart/form-data من التطبيق المحمول
            if not image:
                raise HTTPException(status_code=400, detail="يجب إرسال صورة")
            
            # التحقق من نوع الملف
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="الملف يجب أن يكون صورة")
            
            # قراءة بيانات الصورة
            image_bytes = await image.read()
            
            # بناء location إذا كانت الإحداثيات متوفرة
            location = None
            if latitude is not None and longitude is not None:
                location = {"latitude": latitude, "longitude": longitude}
            
            # إذا كانت هناك بيانات حساسات، احفظها أولاً
            if device_id and (soil_raw is not None or temperature is not None or humidity is not None):
                try:
                    sensor_data = SensorData(
                        device_id=device_id,
                        soil_raw=soil_raw or 500,
                        temperature_c=temperature or 25.0,
                        humidity_percent=humidity or 50.0,
                        battery=100.0
                    )
                    await receive_sensor_data(sensor_data)
                except Exception as e:
                    logger.warning(f"⚠️ فشل حفظ بيانات الحساسات: {e}")
            
            return process_scan_result(
                image_bytes,
                device_id=device_id,
                location=location,
                user_id=user_id
            )
        else:
            # طلب JSON مع image_base64
            if not scan_request:
                raise HTTPException(status_code=400, detail="يجب إرسال scan_request")
            
            # تحويل الصورة من base64
            image_bytes = base64.b64decode(scan_request.image_base64)
            
            return process_scan_result(
                image_bytes, 
                device_id=scan_request.device_id,
                location=scan_request.location
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ خطأ في مسح النبات: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ في مسح النبات: {str(e)}")

@app.post("/api/v1/sensor")
async def receive_sensor_data(sensor_data: SensorData):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO sensor_snapshots (device_id, soil_raw, temperature_c, humidity_percent, battery, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            sensor_data.device_id,
            sensor_data.soil_raw,
            sensor_data.temperature_c,
            sensor_data.humidity_percent,
            sensor_data.battery,
            datetime.now()
        ))
        
        cursor.close()
        connection.close()
        
        return {"status": "success", "message": "تم حفظ بيانات الحساسات"}
        
    except Exception as e:
        logger.error(f"خطأ في حفظ بيانات الحساسات: {e}")
        raise HTTPException(status_code=500, detail="خطأ في حفظ بيانات الحساسات")

@app.post("/api/v1/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO feedbacks (scan_id, is_correct, correct_species_id, feedback_text, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            feedback.scan_id,
            feedback.is_correct,
            feedback.correct_species_id,
            feedback.feedback_text,
            datetime.now()
        ))
        
        cursor.close()
        connection.close()
        
        return {"status": "success", "message": "تم حفظ التقييم"}
        
    except Exception as e:
        logger.error(f"خطأ في حفظ التقييم: {e}")
        raise HTTPException(status_code=500, detail="خطأ في حفظ التقييم")

@app.get("/api/v1/species")
async def list_all_species():
    """الحصول على قائمة بجميع النباتات في قاعدة البيانات"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT id, scientific_name, common_name_ar, common_name_en FROM species ORDER BY common_name_ar"
        cursor.execute(query)
        rows = cursor.fetchall()
        species_list = [dict(row) for row in rows]
        
        cursor.close()
        connection.close()
        
        return {
            "count": len(species_list),
            "species": species_list
        }
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على قائمة النباتات: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الحصول على قائمة النباتات")

@app.get("/api/v1/species/{species_id}")
async def get_species_details(species_id: int):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT * FROM species WHERE id = ?"
        cursor.execute(query, (species_id,))
        row = cursor.fetchone()
        species_info = dict(row) if row else None
        
        cursor.close()
        connection.close()
        
        if not species_info:
            raise HTTPException(status_code=404, detail="النوع غير موجود")
        
        return species_info
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على تفاصيل النوع: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الحصول على تفاصيل النوع")

@app.get("/api/v1/species/search/{name}")
async def search_species(name: str):
    """البحث عن نبات بالاسم"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # البحث الدقيق والجزئي
        query = """
        SELECT * FROM species 
        WHERE scientific_name LIKE ? 
           OR common_name_ar LIKE ? 
           OR common_name_en LIKE ?
        LIMIT 20
        """
        search_pattern = f'%{name}%'
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()
        species_list = [dict(row) for row in rows]
        
        cursor.close()
        connection.close()
        
        return {
            "count": len(species_list),
            "species": species_list
        }
        
    except Exception as e:
        logger.error(f"خطأ في البحث عن النباتات: {e}")
        raise HTTPException(status_code=500, detail="خطأ في البحث عن النباتات")

@app.get("/api/v1/hardware/ports")
async def list_hardware_ports():
    if not HARDWARE_SERVICE_AVAILABLE or hardware_service is None:
        raise HTTPException(status_code=503, detail="خدمة الهاردوير غير متوفرة")
    
    try:
        ports = hardware_service.list_available_ports()
        return {"ports": ports, "count": len(ports)}
    except Exception as e:
        logger.error(f"خطأ في الحصول على المنافذ: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الحصول على المنافذ")

@app.post("/api/v1/hardware/connect")
async def connect_hardware(port: str = Form(...), baudrate: int = Form(9600)):
    if not HARDWARE_SERVICE_AVAILABLE or hardware_service is None:
        raise HTTPException(status_code=503, detail="خدمة الهاردوير غير متوفرة")
    
    try:
        success = hardware_service.connect_device(port, baudrate)
        if success:
            return {"status": "success", "message": f"تم الاتصال بالمنفذ {port}"}
        else:
            raise HTTPException(status_code=400, detail="فشل الاتصال بالجهاز")
    except Exception as e:
        logger.error(f"خطأ في الاتصال بالجهاز: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في الاتصال: {str(e)}")

@app.post("/api/v1/hardware/disconnect")
async def disconnect_hardware(port: str = Form(...)):
    if not HARDWARE_SERVICE_AVAILABLE or hardware_service is None:
        raise HTTPException(status_code=503, detail="خدمة الهاردوير غير متوفرة")
    
    try:
        success = hardware_service.disconnect_device(port)
        if success:
            return {"status": "success", "message": f"تم قطع الاتصال بالمنفذ {port}"}
        else:
            raise HTTPException(status_code=400, detail="فشل قطع الاتصال")
    except Exception as e:
        logger.error(f"خطأ في قطع الاتصال: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في قطع الاتصال: {str(e)}")

@app.get("/api/v1/hardware/read/{port}")
async def read_hardware_sensors(port: str):
    if not HARDWARE_SERVICE_AVAILABLE or hardware_service is None:
        raise HTTPException(status_code=503, detail="خدمة الهاردوير غير متوفرة")
    
    try:
        data = hardware_service.read_sensor_data(port)
        if data:
            return {"status": "success", "data": data}
        else:
            raise HTTPException(status_code=404, detail="لا توجد بيانات متاحة")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في قراءة البيانات: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في القراءة: {str(e)}")

@app.post("/api/v1/hardware/lcd")
async def send_lcd_command(
    port: str = Form(...),
    line1: str = Form(""),
    line2: str = Form("")
):
    if not HARDWARE_SERVICE_AVAILABLE or hardware_service is None:
        raise HTTPException(status_code=503, detail="خدمة الهاردوير غير متوفرة")
    
    try:
        success = hardware_service.send_lcd_command(port, 'LCD', line1, line2)
        if success:
            return {"status": "success", "message": "تم إرسال الأمر بنجاح"}
        else:
            raise HTTPException(status_code=400, detail="فشل إرسال الأمر")
    except Exception as e:
        logger.error(f"خطأ في إرسال أمر LCD: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في الإرسال: {str(e)}")

@app.get("/api/v1/hardware/devices")
async def get_connected_devices():
    if not HARDWARE_SERVICE_AVAILABLE or hardware_service is None:
        raise HTTPException(status_code=503, detail="خدمة الهاردوير غير متوفرة")
    
    try:
        devices = hardware_service.get_connected_devices()
        return {"devices": devices, "count": len(devices)}
    except Exception as e:
        logger.error(f"خطأ في الحصول على الأجهزة: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الحصول على الأجهزة")

@app.get("/api/v1/model/version")
async def get_model_version():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT * FROM model_versions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        model_version = dict(row) if row else None
        
        cursor.close()
        connection.close()
        
        if not model_version:
            return {
                "version": "unknown",
                "architecture": model_arch or "unknown",
                "loaded": model is not None,
                "num_classes": len(species_classes) if species_classes else 0,
                "classes_loaded": len(idx_to_class) if idx_to_class else 0
            }
        
        return model_version
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على إصدار النموذج: {e}")
        return {
            "version": "unknown",
            "architecture": model_arch or "unknown",
            "loaded": model is not None,
            "num_classes": len(species_classes) if species_classes else 0,
            "classes_loaded": len(idx_to_class) if idx_to_class else 0
        }

@app.get("/api/v1/model/classes")
async def get_model_classes():
    """الحصول على جميع الفئات المحملة في النموذج"""
    global model, species_classes, idx_to_class, class_to_idx
    
    if model is None:
        raise HTTPException(status_code=500, detail="النموذج غير محمل")
    
    if not idx_to_class:
        raise HTTPException(status_code=500, detail="الفئات غير محملة")
    
    return {
        "num_classes": len(species_classes) if species_classes else 0,
        "classes": species_classes if species_classes else [],
        "class_to_idx": class_to_idx if class_to_idx else {},
        "idx_to_class": {str(k): v for k, v in idx_to_class.items()} if idx_to_class else {},
        "model_loaded": model is not None,
        "architecture": model_arch or "unknown"
    }

@app.post("/api/v1/model/reload")
async def reload_model():
    """إعادة تحميل النموذج"""
    logger.info("🔄 طلب إعادة تحميل النموذج...")
    success = load_model()
    if success:
        return {
            "status": "success",
            "message": "تم إعادة تحميل النموذج بنجاح",
            "num_classes": len(species_classes) if species_classes else 0,
            "classes": species_classes[:10] if species_classes else []  # أول 10 فئات فقط
        }
    else:
        raise HTTPException(status_code=500, detail="فشل إعادة تحميل النموذج")

@app.post("/api/v1/auth/login")
async def login(login_request: LoginRequest):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # البحث عن المستخدم
        query = "SELECT * FROM users WHERE username = ? OR email = ?"
        cursor.execute(query, (login_request.username, login_request.username))
        row = cursor.fetchone()
        user = dict(row) if row else None
        
        if not user:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور غير صحيحة")
        
        # التحقق من كلمة المرور
        if not verify_password(login_request.password, user['password']):
            cursor.close()
            connection.close()
            raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور غير صحيحة")
        
        # إنشاء token
        access_token = create_access_token(user['id'], user['username'])
        
        cursor.close()
        connection.close()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user['id'],
            "username": user['username'],
            "email": user.get('email', ''),
            "full_name": user.get('full_name', '')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في تسجيل الدخول: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="خطأ في تسجيل الدخول")

@app.post("/api/v1/auth/register")
async def register(register_request: RegisterRequest):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # التحقق من وجود المستخدم
        check_query = "SELECT id FROM users WHERE username = ? OR email = ?"
        cursor.execute(check_query, (register_request.username, register_request.email))
        row = cursor.fetchone()
        existing_user = dict(row) if row else None
        
        if existing_user:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="اسم المستخدم أو البريد الإلكتروني موجود بالفعل")
        
        # تشفير كلمة المرور
        hashed_password = hash_password(register_request.password)
        
        # إدراج المستخدم الجديد
        insert_query = """
        INSERT INTO users (username, email, password, full_name, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            register_request.username,
            register_request.email,
            hashed_password,
            register_request.full_name,
            datetime.now()
        ))
        
        user_id = cursor.lastrowid
        
        # إنشاء token
        access_token = create_access_token(user_id, register_request.username)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id,
            "username": register_request.username,
            "email": register_request.email,
            "full_name": register_request.full_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في تسجيل المستخدم: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="خطأ في تسجيل المستخدم")

def get_current_user(current_user: dict = Depends(verify_token)):
    return current_user

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT id, username, email, full_name, avatar_url, created_at FROM users WHERE id = ?"
        cursor.execute(query, (current_user['user_id'],))
        row = cursor.fetchone()
        user = dict(row) if row else None
        
        cursor.close()
        connection.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في جلب معلومات المستخدم: {e}")
        raise HTTPException(status_code=500, detail="خطأ في جلب معلومات المستخدم")

@app.put("/api/v1/auth/profile")
async def update_profile(
    update_request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        updates = []
        values = []
        
        if update_request.full_name:
            updates.append("full_name = ?")
            values.append(update_request.full_name)
        
        if update_request.email:
            check_query = "SELECT id FROM users WHERE email = ? AND id != ?"
            cursor.execute(check_query, (update_request.email, current_user['user_id']))
            row = cursor.fetchone()
            if row:
                cursor.close()
                connection.close()
                raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
            
            updates.append("email = ?")
            values.append(update_request.email)
        
        if not updates:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
        
        values.append(current_user['user_id'])
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        
        connection.commit()
        
        updated_query = "SELECT id, username, email, full_name, avatar_url FROM users WHERE id = ?"
        cursor.execute(updated_query, (current_user['user_id'],))
        row = cursor.fetchone()
        updated_user = dict(row) if row else None
        
        cursor.close()
        connection.close()
        
        return {
            "message": "تم تحديث الملف الشخصي بنجاح",
            "user": updated_user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في تحديث الملف الشخصي: {e}")
        raise HTTPException(status_code=500, detail="خطأ في تحديث الملف الشخصي")

@app.put("/api/v1/auth/password")
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT password FROM users WHERE id = ?"
        cursor.execute(query, (current_user['user_id'],))
        row = cursor.fetchone()
        user = dict(row) if row else None
        
        if not user:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        if not verify_password(password_request.old_password, user['password']):
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
        
        hashed_new_password = hash_password(password_request.new_password)
        update_query = "UPDATE users SET password = ? WHERE id = ?"
        cursor.execute(update_query, (hashed_new_password, current_user['user_id']))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {"message": "تم تغيير كلمة المرور بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في تغيير كلمة المرور: {e}")
        raise HTTPException(status_code=500, detail="خطأ في تغيير كلمة المرور")

@app.post("/api/v1/auth/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="الملف يجب أن يكون صورة")
        
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        avatar_filename = f"avatar_{current_user['user_id']}.{file_extension}"
        avatar_path = avatars_dir / avatar_filename
        
        with open(avatar_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        avatar_url = f"/uploads/avatars/{avatar_filename}"
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        update_query = "UPDATE users SET avatar_url = ? WHERE id = ?"
        cursor.execute(update_query, (avatar_url, current_user['user_id']))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "message": "تم رفع الصورة الشخصية بنجاح",
            "avatar_url": avatar_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في رفع الصورة الشخصية: {e}")
        raise HTTPException(status_code=500, detail="خطأ في رفع الصورة الشخصية")


# واجهة Flutter Web (مخرجات: flutter build web → backend/static/web)
WEB_APP_DIR = Path(__file__).parent / "static" / "web"


@app.head("/")
async def flutter_spa_head_root() -> Response:
    """Render / uptime checks often use HEAD."""
    return Response(status_code=200)


@app.head("/{spa_path:path}")
async def flutter_spa_head(spa_path: str) -> Response:
    return Response(status_code=200)


@app.get("/{spa_path:path}")
async def serve_flutter_web(spa_path: str):
    """تقديم الملفات الثابتة ومسارات SPA بعد تسجيل جميع مسارات الـ API."""
    if not WEB_APP_DIR.is_dir() or not (WEB_APP_DIR / "index.html").exists():
        raise HTTPException(
            status_code=404,
            detail="واجهة الويب غير مبنية. نفّذ: flutter build web وانسخ build/web إلى backend/static/web",
        )
    root = WEB_APP_DIR.resolve()
    candidate = (WEB_APP_DIR / spa_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    if candidate.is_file():
        return FileResponse(candidate)
    if candidate.is_dir() and (candidate / "index.html").is_file():
        return FileResponse(candidate / "index.html")
    return FileResponse(root / "index.html")


# تشغيل الخادم
if __name__ == "__main__":
    logger.info(f"🌐 بدء تشغيل الخادم على {SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info"
    )
