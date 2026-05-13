#!/usr/bin/env python3
"""ينشئ نموذج efficientnet افتراضياً — يحمّل plant_classifier مباشرة دون استيراد train (لا يحتاج albumentations)."""

import importlib.util
import sys
from pathlib import Path

import torch


def _plant_classifier_cls():
    root = Path(__file__).resolve().parent
    path = root / "backend" / "plant_classifier.py"
    if not path.is_file():
        path = root / "ml" / "plant_classifier.py"
    if not path.is_file():
        raise FileNotFoundError(
            f"plant_classifier.py missing: add backend/plant_classifier.py to the repo (tried {root / 'backend' / 'plant_classifier.py'})"
        )
    spec = importlib.util.spec_from_file_location("smg_plant_classifier", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plant_classifier from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PlantClassifier


def create_default_model():
    PlantClassifier = _plant_classifier_cls()
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
