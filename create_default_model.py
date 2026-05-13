#!/usr/bin/env python3

import torch
import torch.nn as nn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'ml'))

from train import PlantClassifier

def create_default_model():
    print("🌱 إنشاء نموذج نباتات افتراضي...")
    
    # فئات النباتات الأساسية
    default_species = [
        "إكليل الجبل",      # Rosemary
        "الزعتر",           # Thyme
        "الريحان",          # Basil
        "النعناع",          # Mint
        "البقدونس",         # Parsley
        "الكزبرة",          # Coriander
        "الخس",             # Lettuce
        "الطماطم",          # Tomato
        "الفلفل",           # Pepper
        "الخيار"            # Cucumber
    ]
    
    num_classes = len(default_species)
    class_to_idx = {cls: idx for idx, cls in enumerate(default_species)}
    idx_to_class = {idx: cls for cls, idx in class_to_idx.items()}
    
    print(f"📊 عدد الفئات: {num_classes}")
    print(f"🌿 الفئات: {', '.join(default_species)}")
    
    # إنشاء النموذج
    print("🔨 إنشاء النموذج...")
    try:
        model = PlantClassifier(num_classes, 'efficientnet_b4', pretrained=True)
        print("✅ تم إنشاء النموذج بنجاح")
    except Exception as e:
        print(f"⚠️ خطأ في إنشاء النموذج مع pretrained=True: {e}")
        print("🔄 محاولة إنشاء النموذج بدون أوزان مسبقة...")
        try:
            model = PlantClassifier(num_classes, 'efficientnet_b4', pretrained=False)
            print("✅ تم إنشاء النموذج بدون أوزان مسبقة")
        except Exception as e2:
            print(f"❌ فشل في إنشاء النموذج: {e2}")
            return False
    
    # حفظ النموذج
    models_dir = Path(__file__).parent / 'ml' / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'efficientnet_b4_v1.pt'
    
    print(f"💾 حفظ النموذج في: {model_path}")
    
    model_data = {
        'model_state_dict': model.state_dict(),
        'architecture': 'efficientnet_b4',
        'num_classes': num_classes,
        'species_classes': default_species,
        'class_to_idx': class_to_idx,
        'idx_to_class': idx_to_class,
        'epoch': 0,
        'val_accuracy': 0.0,
        'train_accuracy': 0.0,
        'note': 'نموذج افتراضي غير مدرب - يحتاج للتدريب على بيانات حقيقية'
    }
    
    try:
        torch.save(model_data, model_path)
        print("✅ تم حفظ النموذج بنجاح!")
        print(f"\n📝 ملاحظة: هذا نموذج افتراضي غير مدرب.")
        print(f"💡 للتدريب على بيانات حقيقية، استخدم: python train_model.py")
        print(f"📂 ضع صور التدريب في: ml/data/train/")
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ النموذج: {e}")
        return False

if __name__ == "__main__":
    success = create_default_model()
    if success:
        print("\n🎉 تم إنشاء النموذج الافتراضي بنجاح!")
        print("🚀 يمكنك الآن تشغيل الخادم: python start_server.py")
    else:
        print("\n❌ فشل في إنشاء النموذج الافتراضي")
        sys.exit(1)

