#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def check_ml_dependencies():
    requirements_file = Path(__file__).parent / "ml" / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ ملف ml/requirements.txt غير موجود")
        return False
    
    print("✅ ملف متطلبات ML موجود")
    return True

def install_ml_dependencies():
    requirements_file = Path(__file__).parent / "ml" / "requirements.txt"
    
    print("📦 تثبيت متطلبات ML...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ تم تثبيت متطلبات ML بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت متطلبات ML: {e}")
        return False

def check_data_structure():
    ml_dir = Path(__file__).parent / "ml"
    samples_dir = Path(__file__).parent / "samples"
    
    # التحقق من ملف CSV
    csv_file = samples_dir / "plant_care_data.csv"
    if not csv_file.exists():
        print("❌ ملف plant_care_data.csv غير موجود")
        return False
    
    print("✅ ملف البيانات موجود")
    
    # إنشاء مجلد البيانات إذا لم يكن موجوداً
    data_dir = ml_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    test_dir = data_dir / "test"
    
    for dir_path in [train_dir, val_dir, test_dir]:
        dir_path.mkdir(exist_ok=True)
    
    print("✅ مجلدات البيانات جاهزة")
    return True

def get_training_params():
    print("\n⚙️ إعداد معاملات التدريب:")
    
    arch = input("معمارية النموذج [efficientnet_b4]: ").strip() or "efficientnet_b4"
    epochs = input("عدد العصور [50]: ").strip() or "50"
    batch_size = input("حجم الدفعة [32]: ").strip() or "32"
    lr = input("معدل التعلم [0.001]: ").strip() or "0.001"
    
    return {
        'arch': arch,
        'epochs': int(epochs),
        'batch_size': int(batch_size),
        'lr': float(lr)
    }

def train_model(params):
    ml_dir = Path(__file__).parent / "ml"
    samples_dir = Path(__file__).parent / "samples"
    
    train_script = ml_dir / "train.py"
    csv_file = samples_dir / "plant_care_data.csv"
    data_dir = ml_dir / "data"
    
    # إنشاء مجلد النماذج
    models_dir = ml_dir / "models"
    models_dir.mkdir(exist_ok=True)
    
    output_path = models_dir / f"{params['arch']}_v1.pt"
    
    print("🚀 بدء تدريب النموذج...")
    print(f"📊 المعمارية: {params['arch']}")
    print(f"🔄 العصور: {params['epochs']}")
    print(f"📦 حجم الدفعة: {params['batch_size']}")
    print(f"📈 معدل التعلم: {params['lr']}")
    print("-" * 50)
    
    try:
        cmd = [
            sys.executable, str(train_script),
            '--data-dir', str(data_dir),
            '--csv-file', str(csv_file),
            '--arch', params['arch'],
            '--epochs', str(params['epochs']),
            '--batch-size', str(params['batch_size']),
            '--lr', str(params['lr']),
            '--output', str(output_path)
        ]
        
        subprocess.run(cmd, check=True)
        print(f"✅ تم تدريب النموذج بنجاح: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تدريب النموذج: {e}")
        return False

def evaluate_model(params):
    ml_dir = Path(__file__).parent / "ml"
    samples_dir = Path(__file__).parent / "samples"
    
    eval_script = ml_dir / "evaluate.py"
    csv_file = samples_dir / "plant_care_data.csv"
    data_dir = ml_dir / "data"
    models_dir = ml_dir / "models"
    
    model_path = models_dir / f"{params['arch']}_v1.pt"
    output_dir = ml_dir / "results"
    
    if not model_path.exists():
        print("❌ ملف النموذج غير موجود")
        return False
    
    print("📊 تقييم النموذج...")
    
    try:
        cmd = [
            sys.executable, str(eval_script),
            '--model-path', str(model_path),
            '--data-dir', str(data_dir),
            '--csv-file', str(csv_file),
            '--arch', params['arch'],
            '--output-dir', str(output_dir)
        ]
        
        subprocess.run(cmd, check=True)
        print(f"✅ تم تقييم النموذج بنجاح: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تقييم النموذج: {e}")
        return False

def convert_model(params):
    ml_dir = Path(__file__).parent / "ml"
    models_dir = ml_dir / "models"
    
    convert_script = ml_dir / "convert_model.py"
    model_path = models_dir / f"{params['arch']}_v1.pt"
    output_dir = models_dir / "converted"
    
    if not model_path.exists():
        print("❌ ملف النموذج غير موجود")
        return False
    
    print("🔄 تحويل النموذج...")
    
    try:
        cmd = [
            sys.executable, str(convert_script),
            '--model-path', str(model_path),
            '--output-dir', str(output_dir),
            '--arch', params['arch'],
            '--formats', 'onnx', 'mobile', 'quantized'
        ]
        
        subprocess.run(cmd, check=True)
        print(f"✅ تم تحويل النموذج بنجاح: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تحويل النموذج: {e}")
        return False

def main():
    print("🤖 SMG Model Training")
    print("=" * 25)
    
    # التحقق من المتطلبات
    if not check_ml_dependencies():
        return
    
    # تثبيت المتطلبات
    if not install_ml_dependencies():
        return
    
    # التحقق من هيكل البيانات
    if not check_data_structure():
        return
    
    # الحصول على معاملات التدريب
    params = get_training_params()
    
    # تدريب النموذج
    if not train_model(params):
        return
    
    # تقييم النموذج
    if not evaluate_model(params):
        return
    
    # تحويل النموذج
    if not convert_model(params):
        return
    
    print("\n🎉 تم تدريب النموذج بنجاح!")
    print("📁 النماذج محفوظة في: ml/models/")
    print("📊 النتائج محفوظة في: ml/results/")
    print("🔄 النماذج المحولة في: ml/models/converted/")

if __name__ == "__main__":
    main()
