# 🌱 SMG - نظام التعرف على النباتات
# SMG Plant Recognition System

نظام ذكي للتعرف على النباتات باستخدام الذكاء الاصطناعي مع دمج بيانات الحساسات والطقس

---

## 📋 جدول المحتويات

1. [ما هو هذا المشروع؟](#ما-هو-هذا-المشروع)
2. [كيف يعمل النظام؟](#كيف-يعمل-النظام)
3. [هيكل المشروع (كل الملفات والمجلدات)](#هيكل-المشروع)
4. [كيف تبدأ؟](#كيف-تبدأ)
5. [شرح الملفات المهمة](#شرح-الملفات-المهمة)

---

## 🎯 ما هو هذا المشروع؟

هذا مشروع تطبيق ذكي للتعرف على النباتات. يتكون من:

1. **تطبيق Flutter** (للهاتف) - لالتقاط صور النباتات
2. **خادم Backend** (Python) - لتحليل الصور والتعرف على النباتات
3. **نموذج ذكاء اصطناعي** - يتعرف على نوع النبات وحالته الصحية
4. **هاردوير Arduino** - لقياس رطوبة التربة والحرارة

---

## 🔄 كيف يعمل النظام؟

```
1. المستخدم يلتقط صورة للنبات
   ↓
2. التطبيق يرسل الصورة للخادم
   ↓
3. الخادم يستخدم الذكاء الاصطناعي للتعرف على النبات
   ↓
4. الخادم يجمع بيانات من:
   - الحساسات (رطوبة التربة، الحرارة)
   - الطقس (من الإنترنت)
   - قاعدة البيانات (معلومات النبات)
   ↓
5. الخادم يرسل النتيجة للتطبيق:
   - نوع النبات
   - حالة الصحة
   - نصائح العناية
   ↓
6. النتيجة تظهر على:
   - التطبيق (الهاتف)
   - شاشة LCD (الهاردوير)
```

---

## 📁 هيكل المشروع (كل الملفات والمجلدات)

### 📂 المجلد الرئيسي (Root)

```
smg/
├── 📁 backend/          # الخادم (Python)
├── 📁 mobile/           # التطبيق (Flutter)
├── 📁 ml/               # نماذج الذكاء الاصطناعي
├── 📁 data/             # صور التدريب
├── 📁 hardware/         # كود Arduino
├── 📁 sql/              # ملفات قاعدة البيانات
├── 📁 samples/          # أمثلة وبيانات تجريبية
├── 📁 infra/            # إعدادات النشر (Docker)
└── 📄 ملفات Python     # سكربتات مساعدة
```

---

### 📂 1. مجلد `backend/` - الخادم الرئيسي

**ما هو؟** هذا هو الخادم الذي يستقبل الطلبات من التطبيق ويعالجها.

```
backend/
├── 📄 main.py                    # الملف الرئيسي للخادم ⭐⭐⭐
├── 📄 requirements.txt           # قائمة المكتبات المطلوبة
├── 📄 weather_service.py         # خدمة الطقس
├── 📄 hardware_service.py        # خدمة الهاردوير (Arduino)
└── 📄 env_example.txt            # مثال ملف الإعدادات
```

#### شرح الملفات:

**📄 `main.py`** ⭐⭐⭐
- **ما هو؟** الملف الرئيسي للخادم
- **وظيفته:**
  - يستقبل طلبات من التطبيق
  - يحلل صور النباتات
  - يقرأ بيانات الحساسات
  - يرسل النتائج للتطبيق
- **ماذا يحتوي؟**
  - API endpoints (نقاط الاتصال)
  - دوال التعرف على النباتات
  - دوال المصادقة (تسجيل الدخول)
  - دوال قراءة الحساسات

**📄 `requirements.txt`**
- **ما هو؟** قائمة بكل المكتبات المطلوبة
- **مثال:** `fastapi==0.104.1` يعني نحتاج مكتبة FastAPI
- **كيف تستخدمه؟** `pip install -r requirements.txt`

**📄 `weather_service.py`**
- **ما هو؟** خدمة لجلب بيانات الطقس من الإنترنت
- **وظيفته:** يحصل على درجة الحرارة والطقس الحالي
- **يستخدم:** OpenWeatherMap API

**📄 `hardware_service.py`**
- **ما هو؟** خدمة للتعامل مع Arduino
- **وظيفته:** يقرأ بيانات الحساسات ويرسل أوامر لشاشة LCD

---

### 📂 2. مجلد `mobile/smg_app/` - تطبيق الهاتف

**ما هو؟** تطبيق Flutter الذي يعمل على الهاتف.

```
mobile/smg_app/
├── 📁 lib/                        # الكود الرئيسي ⭐⭐⭐
│   ├── 📄 main.dart              # نقطة البداية ⭐
│   ├── 📁 core/                  # الأساسيات
│   ├── 📁 features/              # الميزات
│   └── 📁 presentation/          # الواجهة
├── 📁 android/                   # إعدادات Android
├── 📁 ios/                       # إعدادات iOS
├── 📁 assets/                    # الصور والخطوط
└── 📄 pubspec.yaml              # إعدادات المشروع
```

#### شرح المجلدات:

**📁 `lib/`** ⭐⭐⭐
- **ما هو؟** كل كود التطبيق موجود هنا
- **هيكله:**
  ```
  lib/
  ├── main.dart                    # يبدأ التطبيق من هنا
  ├── core/                        # الأساسيات المشتركة
  │   ├── constants/              # الثوابت (الألوان، النصوص)
  │   ├── services/               # الخدمات (API، التخزين)
  │   └── theme/                  # التصميم والألوان
  ├── features/                    # الميزات الرئيسية
  │   ├── auth/                   # تسجيل الدخول والتسجيل
  │   ├── scan/                   # مسح النباتات
  │   ├── sensor/                 # عرض بيانات الحساسات
  │   └── species/                # قائمة أنواع النباتات
  └── presentation/                # الواجهة والشاشات
      ├── pages/                  # الشاشات (الصفحات)
      ├── router/                 # التنقل بين الشاشات
      └── widgets/                # مكونات قابلة لإعادة الاستخدام
  ```

**📄 `lib/main.dart`** ⭐
- **ما هو؟** نقطة البداية - أول ملف يتم تشغيله
- **وظيفته:** يبدأ التطبيق ويحدد الشاشة الأولى

**📁 `lib/core/`**
- **`constants/`** - الثوابت (مثل روابط API، الألوان)
- **`services/`** - الخدمات (الاتصال بالخادم، حفظ البيانات)
- **`theme/`** - التصميم (الألوان، الخطوط)

**📁 `lib/features/`**
- **`auth/`** - تسجيل الدخول وإنشاء حساب
- **`scan/`** - مسح النباتات والتعرف عليها
- **`sensor/`** - عرض بيانات الحساسات
- **`species/`** - قائمة أنواع النباتات

**📁 `lib/presentation/`**
- **`pages/`** - الشاشات (مثل صفحة المسح، صفحة الحساسات)
- **`router/`** - التنقل (من صفحة لأخرى)
- **`widgets/`** - مكونات صغيرة (مثل بطاقة عرض البيانات)

**📄 `pubspec.yaml`**
- **ما هو؟** ملف الإعدادات
- **يحتوي على:** قائمة المكتبات المستخدمة، الصور، الخطوط

---

### 📂 3. مجلد `ml/` - نماذج الذكاء الاصطناعي

**ما هو؟** النماذج التي تتعرف على النباتات.

```
ml/
├── 📄 train.py                    # تدريب نموذج التعرف على الأنواع
├── 📄 train_health_model.py      # تدريب نموذج صحة النبات
├── 📄 plant_health_model.py      # بنية نموذج الصحة
├── 📄 evaluate.py                 # تقييم دقة النموذج
├── 📄 convert_model.py           # تحويل النموذج لصيغة أخرى
├── 📁 models/                     # النماذج المدربة ⭐
│   ├── efficientnet_b4_v1.pt     # النموذج الرئيسي
│   └── plant_health_v1.pt        # نموذج الصحة
├── 📁 data/                       # بيانات التدريب
└── 📁 results/                    # نتائج التدريب
```

#### شرح الملفات:

**📄 `train.py`**
- **ما هو؟** سكربت لتدريب النموذج على التعرف على أنواع النباتات
- **كيف يعمل؟** يأخذ صور النباتات ويدرب النموذج

**📄 `train_health_model.py`**
- **ما هو؟** سكربت لتدريب النموذج على التعرف على حالة صحة النبات
- **يدرب على:** صحية، مريضة، جافة، مروية زائد، إلخ

**📄 `plant_health_model.py`**
- **ما هو؟** يحدد بنية النموذج (كيف يبدو النموذج)
- **يستخدم:** EfficientNet (نموذج جاهز من Google)

**📁 `models/`** ⭐
- **ما هو؟** النماذج المدربة (الجاهزة للاستخدام)
- **`efficientnet_b4_v1.pt`** - النموذج الرئيسي للتعرف على الأنواع
- **`plant_health_v1.pt`** - النموذج للتعرف على الصحة

---

### 📂 4. مجلد `data/` - صور التدريب

**ما هو؟** صور النباتات المستخدمة لتدريب النموذج.

```
data/
└── health/
    ├── train/                     # صور التدريب
    │   ├── healthy/              # نباتات صحية
    │   ├── sick/                 # نباتات مريضة
    │   ├── dry/                  # نباتات جافة
    │   ├── overwatered/          # نباتات مروية زائد
    │   ├── pest_damage/          # تلف بسبب الآفات
    │   └── nutrient_deficiency/  # نقص العناصر الغذائية
    └── val/                      # صور التحقق (للاختبار)
        └── (نفس المجلدات)
```

**💡 نصيحة:** أضف صورك هنا لتدريب النموذج على نباتاتك الخاصة.

---

### 📂 5. مجلد `hardware/` - كود Arduino

**ما هو؟** الكود الذي ترفعه على Arduino.

```
hardware/
└── 📄 arduino_esp32_code.ino     # الكود الكامل للـ Arduino
```

**📄 `arduino_esp32_code.ino`**
- **ما هو؟** الكود الذي يقرأ الحساسات ويعرض على LCD
- **وظيفته:**
  - يقرأ رطوبة التربة
  - يقرأ الحرارة والرطوبة
  - يعرض البيانات على LCD
  - يرسل البيانات للخادم

---

### 📂 6. مجلد `sql/` - قاعدة البيانات

**ما هو؟** ملفات إنشاء جداول قاعدة البيانات.

```
sql/
├── 📄 create_tables.sql          # إنشاء الجداول
└── 📄 manage_db.py               # سكربت إدارة قاعدة البيانات
```

**📄 `create_tables.sql`**
- **ما هو؟** أوامر SQL لإنشاء الجداول
- **يحتوي على:** جداول المستخدمين، النباتات، المسوح، الحساسات

---

### 📂 7. مجلد `samples/` - أمثلة

**ما هو؟** ملفات أمثلة لفهم شكل البيانات.

```
samples/
├── 📄 api_examples.json          # أمثلة على طلبات API
├── 📄 api_responses.json         # أمثلة على ردود API
├── 📄 sensor_data_examples.json  # أمثلة بيانات الحساسات
└── 📄 plant_care_data.csv        # بيانات العناية بالنباتات
```

---

### 📂 8. مجلد `infra/` - إعدادات النشر

**ما هو؟** ملفات للنشر على خوادم (اختياري).

```
infra/
├── 📄 docker-compose.yml         # إعدادات Docker
├── 📄 Dockerfile.backend         # صورة Docker للخادم
├── 📄 Dockerfile.ml               # صورة Docker للنماذج
└── 📄 nginx.conf                  # إعدادات Nginx
```

**💡 ملاحظة:** هذا للمستخدمين المتقدمين فقط. يمكنك تجاهله في البداية.

---

### 📄 الملفات في المجلد الرئيسي

```
smg/
├── 📄 README.md                  # هذا الملف (الدليل)
├── 📄 setup_database.py          # إعداد قاعدة البيانات
├── 📄 start_server.py            # تشغيل الخادم
├── 📄 train_model.py             # تدريب النموذج
├── 📄 download_plant_images.py   # تحميل صور التدريب
├── 📄 HARDWARE_SETUP.md          # دليل إعداد الهاردوير
└── 📄 TRAINING_GUIDE.md          # دليل إضافة صور التدريب
```

#### شرح الملفات:

**📄 `setup_database.py`**
- **ما هو؟** سكربت لإعداد قاعدة البيانات
- **وظيفته:** ينشئ الجداول والبيانات الأولية
- **كيف تستخدمه؟** `python setup_database.py`

**📄 `start_server.py`**
- **ما هو؟** سكربت لتشغيل الخادم
- **وظيفته:** يبدأ الخادم على المنفذ 8000
- **كيف تستخدمه؟** `python start_server.py`

**📄 `train_model.py`**
- **ما هو؟** سكربت لتدريب النموذج
- **وظيفته:** يدرب النموذج على صور التدريب

**📄 `download_plant_images.py`**
- **ما هو؟** سكربت لتحميل صور النباتات
- **وظيفته:** يحمل صور من الإنترنت أو ينشئ صور نموذجية

---

## 🚀 كيف تبدأ؟

### الخطوة 1: تثبيت المتطلبات

**ما تحتاجه:**
- Python 3.10.6
- Flutter SDK
- MySQL (قاعدة البيانات)
- Arduino IDE (للهاردوير)

### الخطوة 2: إعداد قاعدة البيانات

```bash
python setup_database.py
```

**ما يحدث؟** ينشئ الجداول في قاعدة البيانات.

### الخطوة 3: تثبيت مكتبات Python

```bash
cd backend
pip install -r requirements.txt
```

**ما يحدث؟** يثبت كل المكتبات المطلوبة للخادم.

### الخطوة 4: تشغيل الخادم

```bash
python start_server.py
```

**ما يحدث؟** يبدأ الخادم على `http://localhost:8000`

### الخطوة 5: تشغيل التطبيق

```bash
cd mobile/smg_app
flutter pub get
flutter emulators --launch [ID_Your_Emulator]
flutter run
```

**ما يحدث؟** يثبت مكتبات Flutter ثم يشغل التطبيق.

---

## 📚 شرح مفصل لكل الأكواد - سطر بسطر

### 🔹 1. `backend/main.py` - الخادم الرئيسي (شرح كامل)

**ما هو؟** الملف الأهم في المشروع - الخادم الذي يستقبل الطلبات.

#### الجزء 1: الاستيرادات (Imports)

```python
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
import io
```

**شرح كل سطر:**
- `import os` - للتعامل مع الملفات والمجلدات (مثل معرفة مسار الملف)
- `import json` - لتحويل البيانات لصيغة JSON (مثل `{"name": "tomato"}`)
- `import logging` - لتسجيل الأحداث والأخطاء (مثل طباعة رسائل في السجل)
- `from typing import Dict, List, Optional, Any` - لتحديد نوع البيانات (مثل: هذا متغير نصي أم رقمي)
- `from datetime import datetime` - للتعامل مع التاريخ والوقت
- `import base64` - لتحويل الصور لنص (لإرسالها عبر الإنترنت)
- `import io` - للتعامل مع البيانات في الذاكرة (بدون حفظ في ملف)

```python
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
```

**شرح:**
- `uvicorn` - خادم ويب سريع لتشغيل FastAPI
- `FastAPI` - مكتبة لإنشاء API (واجهة برمجة التطبيقات)
- `HTTPException` - لإرسال أخطاء للعميل (مثل: المستخدم غير موجود)
- `CORSMiddleware` - للسماح للتطبيق بالاتصال بالخادم من أي مكان

```python
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
```

**شرح:**
- `torch` - مكتبة PyTorch للذكاء الاصطناعي
- `torch.nn.functional` - دوال جاهزة للشبكات العصبية
- `transforms` - لتحويل الصور (مثل تغيير الحجم)
- `PIL.Image` - لفتح ومعالجة الصور

#### الجزء 2: إعداد المسارات

```python
# إضافة مسار ml للاستيراد
ml_path = Path(__file__).parent.parent / 'ml'
sys.path.insert(0, str(ml_path))
```

**شرح:**
- `Path(__file__)` - مسار الملف الحالي (`main.py`)
- `.parent.parent` - المجلد الرئيسي (أعلى بمستويين)
- `/ 'ml'` - إضافة مجلد `ml` للمسار
- `sys.path.insert(0, ...)` - إضافة المسار لقائمة المسارات (ليتمكن Python من العثور على الملفات)

**مثال:**
```
المسار الحالي: C:\smg\backend\main.py
بعد .parent.parent: C:\smg\
بعد / 'ml': C:\smg\ml\
```

#### الجزء 3: استيراد الخدمات

```python
try:
    from weather_service import weather_service
    WEATHER_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ خدمة الطقس غير متوفرة")
    WEATHER_SERVICE_AVAILABLE = False
    weather_service = None
```

**شرح:**
- `try:` - جرب تنفيذ هذا الكود
- `from weather_service import weather_service` - استورد خدمة الطقس
- `WEATHER_SERVICE_AVAILABLE = True` - الخدمة متوفرة
- `except ImportError:` - إذا فشل الاستيراد (الملف غير موجود)
- `logger.warning(...)` - اطبع تحذير
- `weather_service = None` - لا يوجد خدمة

**لماذا try/except؟**
- إذا لم يكن ملف `weather_service.py` موجوداً، التطبيق لن يتوقف
- سيعمل بدون خدمة الطقس فقط

#### الجزء 4: إنشاء التطبيق

```python
app = FastAPI(
    title="SMG Plant Recognition API",
    description="API للتعرف على النباتات مع دمج بيانات الحساسات",
    version="1.0.0"
)
```

**شرح:**
- `app` - متغير يحتوي على التطبيق
- `FastAPI(...)` - أنشئ تطبيق FastAPI جديد
- `title` - اسم التطبيق
- `description` - وصف التطبيق
- `version` - رقم الإصدار

**ما هو FastAPI؟**
- مكتبة Python لإنشاء API
- API = طريقة للتواصل بين التطبيق والخادم
- مثل مطعم: التطبيق يطلب طلب، الخادم يرد

#### الجزء 5: إعداد CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح للجميع
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**شرح:**
- `add_middleware` - أضف طبقة أمان
- `CORSMiddleware` - للسماح بالاتصال من أي مكان
- `allow_origins=["*"]` - اسمح لأي موقع بالاتصال
- `allow_credentials=True` - اسمح بإرسال بيانات المصادقة
- `allow_methods=["*"]` - اسمح بكل أنواع الطلبات (GET, POST, إلخ)
- `allow_headers=["*"]` - اسمح بكل أنواع الرؤوس

**ما هو CORS؟**
- Cross-Origin Resource Sharing
- يمنع المتصفح من حظر الطلبات من مواقع أخرى
- **مهم:** بدون هذا، التطبيق لن يتمكن من الاتصال بالخادم

#### الجزء 6: نماذج البيانات (Data Models)

```python
class ScanRequest(BaseModel):
    image_base64: str
    device_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None
```

**شرح:**
- `class ScanRequest` - نموذج بيانات لطلب المسح
- `BaseModel` - من مكتبة Pydantic (للتحقق من البيانات)
- `image_base64: str` - الصورة بصيغة base64 (نص)
- `device_id: Optional[str] = None` - معرف الجهاز (اختياري، افتراضي None)
- `location: Optional[Dict[str, float]] = None` - الموقع (اختياري)

**مثال على البيانات:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANS...",
  "device_id": "ESP32-001",
  "location": {"latitude": 24.7136, "longitude": 46.6753}
}
```

#### الجزء 7: إعدادات قاعدة البيانات

```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'smg_user'),
    'password': os.getenv('DB_PASSWORD', 'smg_password'),
    'database': os.getenv('DB_NAME', 'smg_plants'),
    'charset': 'utf8mb4'
}
```

**شرح:**
- `DB_CONFIG` - قاموس يحتوي على إعدادات قاعدة البيانات
- `os.getenv('DB_HOST', 'localhost')` - اقرأ من متغير البيئة، إذا لم يوجد استخدم 'localhost'
- `'host'` - عنوان الخادم (مثل localhost أو IP)
- `'user'` - اسم المستخدم
- `'password'` - كلمة المرور
- `'database'` - اسم قاعدة البيانات
- `'charset'` - الترميز (utf8mb4 يدعم العربية)

**لماذا `os.getenv`؟**
- للسماح بتغيير الإعدادات بدون تعديل الكود
- يمكن وضعها في ملف `.env`

#### الجزء 8: دالة الاتصال بقاعدة البيانات

```python
def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        raise HTTPException(status_code=500, detail="خطأ في الاتصال بقاعدة البيانات")
```

**شرح سطر بسطر:**
- `def get_db_connection():` - دالة اسمها `get_db_connection`
- `"""..."""` - وصف الدالة (docstring)
- `try:` - جرب تنفيذ الكود
- `connection = mysql.connector.connect(**DB_CONFIG)` - اتصل بقاعدة البيانات
  - `**DB_CONFIG` - فك القاموس (مثل: `host='localhost', user='smg_user', ...`)
- `return connection` - أرجع الاتصال
- `except Error as e:` - إذا حدث خطأ
- `logger.error(...)` - سجل الخطأ
- `raise HTTPException(...)` - أرسل خطأ للعميل برمز 500

**مثال على الاستخدام:**
```python
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
```

#### الجزء 9: دالة تحميل النموذج

```python
def load_model():
    """تحميل نموذج التعلم الآلي"""
    global model, model_arch, species_classes, class_to_idx, idx_to_class
    
    try:
        # تحديد مسار النموذج - البحث في عدة مواقع
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'models', 'efficientnet_b4_v1.pt'),
            os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'efficientnet_b4_v1.pt'),
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
```

**شرح:**
- `def load_model():` - دالة لتحميل النموذج
- `global model, ...` - استخدم المتغيرات العامة (خارج الدالة)
- `possible_paths = [...]` - قائمة بمسارات محتملة للنموذج
- `os.path.join(...)` - اربط المسارات (مثل: `backend/models/efficientnet_b4_v1.pt`)
- `os.path.dirname(__file__)` - مجلد الملف الحالي
- `'..'` - مجلد أعلى (الوالد)

**لماذا عدة مسارات؟**
- النموذج قد يكون في أماكن مختلفة حسب طريقة التشغيل
- نبحث في كل الأماكن المحتملة

```python
        # تحميل النموذج
        checkpoint = torch.load(model_path, map_location='cpu')
        model_arch = checkpoint.get('arch', 'efficientnet_b4')
        
        # تحميل فئات الأنواع
        species_classes = checkpoint.get('species_classes', [])
        class_to_idx = checkpoint.get('class_to_idx', {})
        idx_to_class = checkpoint.get('idx_to_class', {})
        
        # تحميل النموذج
        model = checkpoint['model']
        model.eval()
```

**شرح:**
- `torch.load(...)` - حمّل الملف (النموذج المدرب)
- `map_location='cpu'` - استخدم المعالج (ليس GPU)
- `checkpoint.get('arch', 'efficientnet_b4')` - اقرأ نوع النموذج، افتراضي 'efficientnet_b4'
- `species_classes` - قائمة بأسماء النباتات
- `class_to_idx` - قاموس: اسم النبات → رقم (مثل: {'tomato': 0})
- `idx_to_class` - قاموس: رقم → اسم النبات (مثل: {0: 'tomato'})
- `model.eval()` - ضع النموذج في وضع التقييم (ليس التدريب)

#### الجزء 10: دالة معالجة الصورة

```python
def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """معالجة الصورة للتنبؤ"""
    try:
        # تحويل bytes إلى صورة
        image = Image.open(io.BytesIO(image_bytes))
        
        # تحويل إلى RGB إذا لزم الأمر
        if image.mode != 'RGB':
            image = image.convert('RGB')
```

**شرح:**
- `def preprocess_image(image_bytes: bytes) -> torch.Tensor:` - دالة تأخذ bytes وترجع Tensor
- `Image.open(io.BytesIO(image_bytes))` - افتح الصورة من البيانات في الذاكرة
- `image.mode != 'RGB'` - إذا لم تكن الصورة ملونة (RGB)
- `image.convert('RGB')` - حوّلها لـ RGB

```python
        # تحويلات الصورة
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # تطبيق التحويلات
        image_tensor = transform(image).unsqueeze(0)
        
        return image_tensor
```

**شرح:**
- `transforms.Compose([...])` - سلسلة من التحويلات
- `Resize((224, 224))` - غيّر الحجم لـ 224×224 (الحجم المطلوب للنموذج)
- `ToTensor()` - حوّل الصورة لـ Tensor (نوع بيانات PyTorch)
- `Normalize(...)` - طبيعي القيم (لتحسين الأداء)
- `unsqueeze(0)` - أضف بُعداً إضافياً (لأن النموذج يتوقع مجموعة صور)

#### الجزء 11: دالة التنبؤ

```python
def predict_species(image_tensor: torch.Tensor) -> Dict[str, Any]:
    """التنبؤ بنوع النبات"""
    global model, species_classes, idx_to_class
    
    if model is None:
        raise HTTPException(status_code=500, detail="النموذج غير محمل")
```

**شرح:**
- `def predict_species(...)` - دالة للتنبؤ بنوع النبات
- `if model is None:` - إذا لم يكن النموذج محملاً
- `raise HTTPException(...)` - أرسل خطأ للعميل

```python
    try:
        with torch.no_grad():
            # التنبؤ
            outputs = model(image_tensor)
            probabilities = F.softmax(outputs, dim=1)
```

**شرح:**
- `with torch.no_grad():` - لا تحسب المشتقات (أسرع، للتنبؤ فقط)
- `model(image_tensor)` - مرر الصورة للنموذج
- `F.softmax(...)` - حوّل النتائج لاحتمالات (0-1)

```python
            # الحصول على أفضل 3 توقعات
            top3_prob, top3_indices = torch.topk(probabilities, 3, dim=1)
            
            # تحويل النتائج
            predictions = []
            for i in range(3):
                idx = top3_indices[0][i].item()
                prob = top3_prob[0][i].item()
                species_name = idx_to_class.get(idx, f"Unknown_{idx}")
                
                predictions.append({
                    'species_name': species_name,
                    'confidence': prob,
                    'rank': i + 1
                })
```

**شرح:**
- `torch.topk(probabilities, 3, dim=1)` - احصل على أفضل 3 نتائج
- `top3_prob` - الاحتمالات
- `top3_indices` - الأرقام (الفئات)
- `for i in range(3):` - لكل من الثلاثة
- `idx = top3_indices[0][i].item()` - رقم الفئة
- `prob = top3_prob[0][i].item()` - الاحتمال
- `idx_to_class.get(idx, ...)` - احصل على الاسم، إذا لم يوجد استخدم "Unknown"
- `predictions.append({...})` - أضف النتيجة للقائمة

#### الجزء 12: API Endpoint - مسح النبات

```python
@app.post("/api/v1/scan")
async def scan_plant(scan_request: ScanRequest):
    """مسح النبات والتعرف عليه مع تحليل الصحة والطقس"""
    try:
        # تحويل الصورة من base64
        image_bytes = base64.b64decode(scan_request.image_base64)
```

**شرح:**
- `@app.post("/api/v1/scan")` - decorator يحدد المسار ونوع الطلب (POST)
- `async def scan_plant(...)` - دالة غير متزامنة (async)
- `scan_request: ScanRequest` - البيانات المرسلة (من نوع ScanRequest)
- `base64.b64decode(...)` - حوّل النص لـ bytes (الصورة الأصلية)

```python
        # معالجة الصورة
        image_tensor = preprocess_image(image_bytes)
        
        # التنبؤ بنوع النبات
        prediction_result = predict_species(image_tensor)
        
        # الحصول على معلومات النوع
        species_name = prediction_result['top_prediction']['species_name']
        species_info = get_species_info(species_name)
```

**شرح:**
- `preprocess_image(...)` - معالجة الصورة
- `predict_species(...)` - التنبؤ
- `prediction_result['top_prediction']` - أفضل نتيجة
- `get_species_info(...)` - احصل على معلومات النبات من قاعدة البيانات

#### الجزء 13: API Endpoint - تسجيل الدخول

```python
@app.post("/api/v1/auth/login")
async def login(login_request: LoginRequest):
    """تسجيل الدخول"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # البحث عن المستخدم
        query = "SELECT * FROM users WHERE username = %s OR email = %s"
        cursor.execute(query, (login_request.username, login_request.username))
        user = cursor.fetchone()
```

**شرح:**
- `@app.post("/api/v1/auth/login")` - مسار تسجيل الدخول
- `get_db_connection()` - احصل على اتصال
- `cursor(dictionary=True)` - أرجع النتائج كقاموس (ليس tuple)
- `query = "SELECT * FROM users WHERE ..."` - استعلام SQL
- `%s` - placeholder (يتم استبداله بالبيانات)
- `cursor.execute(query, (...))` - نفذ الاستعلام
- `cursor.fetchone()` - احصل على سجل واحد

```python
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
```

**شرح:**
- `if not user:` - إذا لم يوجد المستخدم
- `raise HTTPException(status_code=401, ...)` - أرسل خطأ 401 (غير مصرح)
- `verify_password(...)` - تحقق من كلمة المرور
- `create_access_token(...)` - أنشئ رمز JWT

#### الجزء 14: دوال المصادقة

```python
def hash_password(password: str) -> str:
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()
```

**شرح:**
- `hashlib.sha256(...)` - خوارزمية SHA256 للتشفير
- `password.encode()` - حوّل النص لـ bytes
- `.hexdigest()` - حوّل لـ hex string

**مثال:**
```python
hash_password("123456")
# النتيجة: "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
```

```python
def create_access_token(user_id: int, username: str) -> str:
    """إنشاء JWT token"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token
```

**شرح:**
- `datetime.utcnow()` - الوقت الحالي (UTC)
- `timedelta(hours=24)` - مدة 24 ساعة
- `payload` - البيانات المشفرة في الرمز
- `exp` - وقت انتهاء الصلاحية
- `iat` - وقت الإنشاء
- `jwt.encode(...)` - شفّر الرمز

**ما هو JWT？**
- JSON Web Token
- رمز مشفر يحتوي على بيانات المستخدم
- يستخدم للمصادقة

**المسارات (Endpoints) المهمة:**
- `/api/v1/scan` - مسح النبات
- `/api/v1/auth/login` - تسجيل الدخول
- `/api/v1/auth/register` - إنشاء حساب
- `/api/v1/sensor` - إرسال بيانات الحساسات
- `/api/v1/hardware/connect` - الاتصال بـ Arduino

---

### 🔹 2. `mobile/smg_app/lib/main.dart` - نقطة البداية (شرح كامل)

**ما هو؟** أول ملف يتم تشغيله في التطبيق.

#### الجزء 1: الاستيرادات

```dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
```

**شرح:**
- `flutter/material.dart` - مكتبة Flutter الأساسية (الأزرار، النصوص، إلخ)
- `flutter/services.dart` - خدمات النظام (مثل إخفاء شريط الحالة)
- `provider/provider.dart` - لإدارة الحالة (مثل بيانات المستخدم)
- `flutter_bloc` - نمط BLoC لإدارة الحالة (أفضل من Provider)

#### الجزء 2: دالة main

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
```

**شرح:**
- `void main()` - الدالة الرئيسية (تبدأ من هنا)
- `async` - غير متزامنة (يمكن انتظار عمليات)
- `WidgetsFlutterBinding.ensureInitialized()` - تهيئة Flutter (مهم قبل أي شيء)

```dart
  // إعداد وضع الشاشة
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Colors.black,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
```

**شرح:**
- `SystemChrome.setSystemUIOverlayStyle(...)` - إعدادات شريط الحالة
- `statusBarColor: Colors.transparent` - شفاف
- `statusBarIconBrightness: Brightness.light` - الأيقونات فاتحة

```dart
  // تهيئة الخدمات
  final apiService = ApiService();
  final storageService = StorageService();
  await storageService.init();
```

**شرح:**
- `final apiService = ApiService()` - أنشئ خدمة API
- `final storageService = StorageService()` - أنشئ خدمة التخزين
- `await storageService.init()` - انتظر التهيئة

```dart
  // اختبار الاتصال بالخادم
  print('🔍 اختبار الاتصال بالخادم...');
  final isConnected = await apiService.testConnection();
  if (isConnected) {
    print('✅ الاتصال بالخادم نجح');
  } else {
    print('❌ فشل الاتصال بالخادم');
  }
```

**شرح:**
- `print(...)` - اطبع في console
- `await apiService.testConnection()` - اختبر الاتصال
- `if (isConnected)` - إذا نجح الاتصال

```dart
  runApp(SMGApp(apiService: apiService, storageService: storageService));
}
```

**شرح:**
- `runApp(...)` - ابدأ التطبيق
- `SMGApp(...)` - التطبيق الرئيسي

#### الجزء 3: فئة SMGApp

```dart
class SMGApp extends StatelessWidget {
  final ApiService apiService;
  final StorageService storageService;

  const SMGApp({
    super.key,
    required this.apiService,
    required this.storageService,
  });
```

**شرح:**
- `class SMGApp extends StatelessWidget` - فئة التطبيق (لا تتغير)
- `final ApiService apiService` - متغير للخدمة (final = لا يتغير)
- `required this.apiService` - مطلوب عند الإنشاء

```dart
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<ApiService>.value(value: apiService),
        Provider<StorageService>.value(value: storageService),
        BlocProvider<AuthBloc>(
          create: (context) => AuthBloc(
            apiService: context.read<ApiService>(),
            storageService: context.read<StorageService>(),
          ),
        ),
```

**شرح:**
- `Widget build(BuildContext context)` - بناء الواجهة
- `MultiProvider` - مزود متعدد (يعطي خدمات للكل)
- `Provider<ApiService>.value(...)` - أعط خدمة API للكل
- `BlocProvider<AuthBloc>` - أنشئ BLoC للمصادقة
- `create: (context) => AuthBloc(...)` - أنشئ عند الحاجة

**التدفق:**
1. يبدأ من `main()`
2. ينشئ التطبيق `SMGApp`
3. يعرض شاشة البداية `SplashPage`
4. ينتقل للمستخدم حسب حالة تسجيل الدخول

---

### 🔹 3. `mobile/smg_app/lib/core/services/api_service.dart` - خدمة API

#### الفئة ApiService

```dart
class ApiService {
  late Dio _dio;
  String? _authToken;
```

**شرح:**
- `class ApiService` - فئة لإدارة الاتصال بالخادم
- `late Dio _dio` - متغير من نوع Dio (مكتبة HTTP)
- `String? _authToken` - رمز المصادقة (اختياري، `?` يعني قد يكون null)

```dart
  ApiService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: Duration(milliseconds: AppConstants.connectionTimeout),
        receiveTimeout: Duration(milliseconds: AppConstants.receiveTimeout),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _setupInterceptors();
  }
```

**شرح:**
- `ApiService()` - constructor (يعمل عند إنشاء الكائن)
- `BaseOptions(...)` - إعدادات أساسية
- `baseUrl` - عنوان الخادم (مثل: `http://localhost:8000/api/v1`)
- `connectTimeout` - وقت انتظار الاتصال (30 ثانية)
- `receiveTimeout` - وقت انتظار الاستجابة (30 ثانية)
- `headers` - رؤوس HTTP (يخبر الخادم بنوع البيانات)

#### دالة إعداد Interceptors

```dart
  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (_authToken != null) {
            options.headers['Authorization'] = 'Bearer $_authToken';
          }
          handler.next(options);
        },
```

**شرح:**
- `_setupInterceptors()` - دالة لإعداد interceptors (معالجات)
- `InterceptorsWrapper` - غلاف للمعالجات
- `onRequest` - قبل إرسال الطلب
- `if (_authToken != null)` - إذا كان هناك رمز مصادقة
- `options.headers['Authorization'] = 'Bearer $_authToken'` - أضف الرمز للرؤوس
- `handler.next(options)` - أكمل الطلب

**ما هو Interceptor؟**
- مثل مراقب: يفحص كل طلب قبل إرساله
- يضيف رمز المصادقة تلقائياً

#### دالة تسجيل الدخول

```dart
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await _dio.post(
        AppConstants.authLoginPath,
        data: {
          'username': email,
          'password': password,
        },
      );
      return response.data;
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }
```

**شرح:**
- `Future<Map<String, dynamic>>` - يرجع promise (عملية غير متزامنة)
- `async` - الدالة غير متزامنة
- `await _dio.post(...)` - أرسل طلب POST وانتظر الرد
- `AppConstants.authLoginPath` - المسار (`/auth/login`)
- `data: {...}` - البيانات المرسلة
- `return response.data` - أرجع البيانات
- `on DioException catch (e)` - إذا حدث خطأ
- `throw _handleDioError(e)` - أرسل خطأ معالج

**مثال على الاستخدام:**
```dart
final result = await apiService.login('user@example.com', 'password123');
print(result['access_token']); // يطبع رمز المصادقة
```

---

### 🔹 4. `mobile/smg_app/lib/features/auth/presentation/bloc/auth_bloc.dart` - BLoC المصادقة

#### Events (الأحداث)

```dart
abstract class AuthEvent extends Equatable {
  const AuthEvent();
  @override
  List<Object?> get props => [];
}
```

**شرح:**
- `abstract class` - فئة مجردة (لا يمكن إنشاء كائن منها مباشرة)
- `extends Equatable` - للمقارنة بين الأحداث
- `get props => []` - الخصائص للمقارنة (فارغة هنا)

```dart
class LoginEvent extends AuthEvent {
  final String email;
  final String password;
  final bool rememberMe;

  const LoginEvent({
    required this.email,
    required this.password,
    this.rememberMe = false,
  });

  @override
  List<Object?> get props => [email, password, rememberMe];
}
```

**شرح:**
- `class LoginEvent extends AuthEvent` - حدث تسجيل الدخول
- `final String email` - البريد الإلكتروني (final = لا يتغير)
- `required this.email` - مطلوب عند الإنشاء
- `this.rememberMe = false` - افتراضي false
- `get props => [email, password, rememberMe]` - للاستخدام في المقارنة

#### States (الحالات)

```dart
class AuthLoadingState extends AuthState {}
```

**شرح:**
- حالة التحميل (جاري تسجيل الدخول)

```dart
class AuthSuccessState extends AuthState {
  final Map<String, dynamic> userData;
  final String token;

  const AuthSuccessState({required this.userData, required this.token});
}
```

**شرح:**
- حالة النجاح
- `userData` - بيانات المستخدم
- `token` - رمز المصادقة

#### BLoC (Business Logic Component)

```dart
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final ApiService apiService;
  final StorageService storageService;

  AuthBloc({required this.apiService, required this.storageService})
    : super(AuthInitialState()) {
    on<LoginEvent>(_onLogin);
    on<RegisterEvent>(_onRegister);
    on<LogoutEvent>(_onLogout);
    on<CheckAuthStatusEvent>(_onCheckAuthStatus);
  }
```

**شرح:**
- `extends Bloc<AuthEvent, AuthState>` - BLoC يأخذ أحداث ويرجع حالات
- `super(AuthInitialState())` - الحالة الأولية
- `on<LoginEvent>(_onLogin)` - عند حدث Login، نفذ `_onLogin`

```dart
  Future<void> _onLogin(LoginEvent event, Emitter<AuthState> emit) async {
    emit(AuthLoadingState());

    try {
      final response = await apiService.login(event.email, event.password);

      if (response['access_token'] != null) {
        final token = response['access_token'] as String;
        final userData = {'id': response['user_id'], 'email': event.email};

        await storageService.saveAuthToken(token);
        await storageService.saveUserData(userData);

        apiService.setAuthToken(token);

        emit(AuthSuccessState(userData: userData, token: token));
      } else {
        emit(const AuthErrorState(message: 'فشل في تسجيل الدخول'));
      }
    } catch (e) {
      emit(AuthErrorState(message: e.toString()));
    }
  }
```

**شرح سطر بسطر:**
- `emit(AuthLoadingState())` - أرسل حالة التحميل (يظهر loading)
- `await apiService.login(...)` - انتظر تسجيل الدخول
- `if (response['access_token'] != null)` - إذا كان هناك رمز
- `await storageService.saveAuthToken(token)` - احفظ الرمز محلياً
- `apiService.setAuthToken(token)` - ضع الرمز في API service
- `emit(AuthSuccessState(...))` - أرسل حالة النجاح
- `catch (e)` - إذا حدث خطأ
- `emit(AuthErrorState(...))` - أرسل حالة الخطأ

**ما هو BLoC؟**
- نمط لإدارة الحالة
- يفصل المنطق عن الواجهة
- سهل الاختبار والصيانة

---

### 🔹 5. `ml/train_health_model.py` - تدريب نموذج الصحة

**ما هو؟** سكربت لتدريب النموذج على التعرف على حالة صحة النبات.

#### الاستيرادات

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import os
from pathlib import Path
```

**شرح:**
- `torch` - PyTorch (مكتبة الذكاء الاصطناعي)
- `torch.nn` - الشبكات العصبية
- `DataLoader` - لتحميل البيانات
- `Dataset` - مجموعة البيانات
- `transforms` - تحويلات الصور

#### فئة Dataset

```python
class PlantHealthDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.images = []
        self.labels = []
        
        # جمع الصور والتسميات
        for class_name in os.listdir(self.data_dir):
            class_path = self.data_dir / class_name
            if class_path.is_dir():
                for img_file in class_path.glob('*.jpg'):
                    self.images.append(img_file)
                    self.labels.append(class_name)
```

**شرح:**
- `class PlantHealthDataset(Dataset)` - فئة مجموعة البيانات
- `__init__(self, data_dir, ...)` - constructor
- `self.images = []` - قائمة الصور
- `self.labels = []` - قائمة التسميات
- `os.listdir(...)` - قائمة الملفات في المجلد
- `glob('*.jpg')` - كل ملفات jpg

```python
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        label = self.labels[idx]
        
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label
```

**شرح:**
- `__len__(self)` - طول المجموعة (عدد الصور)
- `__getitem__(self, idx)` - احصل على عنصر (صورة + تسمية)
- `Image.open(...)` - افتح الصورة
- `.convert('RGB')` - حوّل لـ RGB
- `self.transform(image)` - طبق التحويلات

#### دالة التدريب

```python
def train_model(model, train_loader, val_loader, epochs=10):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(epochs):
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
```

**شرح:**
- `nn.CrossEntropyLoss()` - دالة الخسارة (للتصنيف)
- `torch.optim.Adam(...)` - محسّن Adam
- `lr=0.001` - معدل التعلم
- `for epoch in range(epochs):` - لكل دورة تدريب
- `model.train()` - وضع التدريب
- `optimizer.zero_grad()` - امسح المشتقات السابقة
- `outputs = model(images)` - مرر الصور للنموذج
- `loss = criterion(outputs, labels)` - احسب الخسارة
- `loss.backward()` - احسب المشتقات
- `optimizer.step()` - حدّث الأوزان

**ما تحتاجه:**
- صور النباتات في `data/health/train/`
- كل نوع في مجلد منفصل

---

### 🔹 6. `hardware/arduino_esp32_code.ino` - كود Arduino (شرح كامل)

**ما هو؟** الكود الذي يقرأ الحساسات.

#### الإعدادات

```cpp
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <ArduinoJson.h>
```

**شرح:**
- `#include <Wire.h>` - مكتبة للتواصل I2C (للشاشة)
- `#include <LiquidCrystal_I2C.h>` - مكتبة للشاشة LCD
- `#include <DHT.h>` - مكتبة لحساس DHT22
- `#include <ArduinoJson.h>` - مكتبة لـ JSON

```cpp
#define SOIL_SENSOR_PIN A0
#define DHT_PIN 2
#define DHT_TYPE DHT22
```

**شرح:**
- `#define SOIL_SENSOR_PIN A0` - عرّف دبوس حساس التربة (A0)
- `#define DHT_PIN 2` - عرّف دبوس DHT22 (Pin 2)
- `#define DHT_TYPE DHT22` - نوع الحساس

#### دالة setup

```cpp
void setup() {
  Serial.begin(9600);
  
  // تهيئة LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("SMG Plant");
```

**شرح:**
- `void setup()` - تعمل مرة واحدة عند البدء
- `Serial.begin(9600)` - ابدأ Serial بسرعة 9600
- `lcd.init()` - تهيئة الشاشة
- `lcd.backlight()` - شغّل الإضاءة الخلفية
- `lcd.setCursor(0, 0)` - ضع المؤشر في البداية
- `lcd.print("SMG Plant")` - اطبع النص

#### دالة loop

```cpp
void loop() {
  // قراءة الحساسات كل 30 ثانية
  if (millis() - lastSensorRead >= sensorInterval) {
    readAndSendSensorData();
    lastSensorRead = millis();
  }
```

**شرح:**
- `void loop()` - تعمل باستمرار
- `millis()` - الوقت منذ البدء (بالميلي ثانية)
- `if (millis() - lastSensorRead >= sensorInterval)` - إذا مرت 30 ثانية
- `readAndSendSensorData()` - اقرأ وأرسل البيانات
- `lastSensorRead = millis()` - احفظ الوقت الحالي

```cpp
  // قراءة الأوامر من Serial
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "READ") {
      readAndSendSensorData();
    }
```

**شرح:**
- `Serial.available() > 0` - إذا كانت هناك بيانات
- `Serial.readStringUntil('\n')` - اقرأ حتى نهاية السطر
- `command.trim()` - احذف المسافات الزائدة
- `if (command == "READ")` - إذا كان الأمر "READ"

#### دالة قراءة وإرسال البيانات

```cpp
void readAndSendSensorData() {
  // قراءة حساس التربة (0-1023)
  int soilRaw = analogRead(SOIL_SENSOR_PIN);
  
  // قراءة درجة الحرارة والرطوبة
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
```

**شرح:**
- `analogRead(SOIL_SENSOR_PIN)` - اقرأ من دبوس تماثلي (0-1023)
- `dht.readTemperature()` - اقرأ الحرارة
- `dht.readHumidity()` - اقرأ الرطوبة

```cpp
  // إنشاء JSON
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["soil_raw"] = soilRaw;
  doc["temperature_c"] = temperature;
  doc["humidity_percent"] = humidity;
  doc["battery"] = battery;
  doc["timestamp"] = millis();
  
  // إرسال JSON
  serializeJson(doc, Serial);
  Serial.println();
```

**شرح:**
- `StaticJsonDocument<256>` - مستند JSON (256 بايت)
- `doc["device_id"] = deviceId` - أضف قيمة
- `serializeJson(doc, Serial)` - أرسل JSON عبر Serial
- `Serial.println()` - سطر جديد

---

### 🔹 7. `start_server.py` - سكربت التشغيل

#### دالة التحقق من المتطلبات

```python
def check_requirements():
    """التحقق من المتطلبات"""
    print("🔍 التحقق من المتطلبات...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'mysql-connector-python',
        ...
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
```

**شرح:**
- `required_packages` - قائمة المكتبات المطلوبة
- `missing_packages = []` - قائمة المفقودة
- `__import__(...)` - جرب استيراد المكتبة
- `package.replace('-', '_')` - استبدل `-` بـ `_` (مثل: `mysql-connector-python` → `mysql_connector_python`)

```python
    if missing_packages:
        print(f"\n📦 تثبيت الحزم المفقودة: {', '.join(missing_packages)}")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, check=True)
```

**شرح:**
- `', '.join(missing_packages)` - اربط بفواصل (مثل: "fastapi, uvicorn")
- `sys.executable` - مسار Python
- `'-m', 'pip', 'install'` - استخدم pip
- `+ missing_packages` - أضف المكتبات

---

### 🔹 8. `download_plant_images.py` - تحميل الصور

#### دالة تحميل الصورة

```python
def download_image(url, save_path):
    """تحميل صورة من URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
```

**شرح:**
- `def download_image(url, save_path):` - دالة لتحميل صورة
- `headers = {...}` - رؤوس HTTP (بعض المواقع تطلبها)
- `'User-Agent'` - نوع المتصفح (بعض المواقع ترفض بدونها)
- `requests.get(url, ...)` - احصل على الصورة
- `timeout=10` - انتظر 10 ثواني كحد أقصى

```python
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"[OK] تم تحميل: {save_path.name}")
            return True
```

**شرح:**
- `if response.status_code == 200:` - إذا نجح الطلب (200 = OK)
- `with open(save_path, 'wb') as f:` - افتح الملف للكتابة (wb = write binary)
- `f.write(response.content)` - اكتب محتوى الصورة
- `return True` - نجح التحميل

---

## 🔍 مصطلحات مهمة

- **API** - طريقة للتواصل بين التطبيق والخادم
- **Endpoint** - عنوان محدد في API (مثل `/api/v1/scan`)
- **Model** - النموذج (الذكاء الاصطناعي)
- **Training** - تدريب النموذج على الصور
- **Sensor** - الحساس (يقيس شيئاً مثل الحرارة)
- **LCD** - شاشة صغيرة لعرض النصوص
- **Backend** - الخادم (الجزء الذي يعمل على الكمبيوتر)
- **Frontend** - الواجهة (التطبيق الذي يراه المستخدم)
- **Database** - قاعدة البيانات (مخزن المعلومات)

---

## 📖 أدلة إضافية

- **`HARDWARE_SETUP.md`** - دليل إعداد الهاردوير (Arduino)
- **`TRAINING_GUIDE.md`** - دليل إضافة صور التدريب

---

## ❓ أسئلة شائعة

**س: أين أضع صور النباتات؟**
ج: في `data/health/train/` - كل نوع في مجلد منفصل.

**س: كيف أشغل الخادم؟**
ج: `python start_server.py` من المجلد الرئيسي.

**س: كيف أشغل التطبيق؟**
ج: `flutter run` من مجلد `mobile/smg_app/`.

**س: أين كود Arduino؟**
ج: في `hardware/arduino_esp32_code.ino`.

---

## 🎉 الخلاصة

هذا المشروع يتكون من:
1. **خادم Python** (`backend/`) - يعالج الطلبات
2. **تطبيق Flutter** (`mobile/`) - واجهة المستخدم
3. **نماذج AI** (`ml/`) - التعرف على النباتات
4. **هاردوير Arduino** (`hardware/`) - قراءة الحساسات

**ابدأ من:**
1. إعداد قاعدة البيانات
2. تشغيل الخادم
3. تشغيل التطبيق
4. إعداد الهاردوير (اختياري)

**للمزيد من التفاصيل، راجع الأدلة المذكورة أعلاه!**
