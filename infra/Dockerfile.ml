# Dockerfile لتدريب النماذج
FROM python:3.10-slim

# تعيين متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# تحديث النظام وتثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات
COPY ml/requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود التدريب
COPY ml/ .

# إنشاء مجلدات البيانات والنماذج
RUN mkdir -p data models results

# تعيين الصلاحيات
RUN chmod +x train.py evaluate.py convert_model.py

# أمر التشغيل الافتراضي
CMD ["python", "train.py", "--help"]
