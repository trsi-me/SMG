# دليل التدريب - SMG

## طريقة إضافة الصور الجديدة وتدريب النموذج

### 1. إضافة الصور إلى قاعدة البيانات

```bash
cd ml
python add_training_images_to_db.py --data-dir ../data/health --dataset-type both
```

### 2. تدريب النموذج

```bash
python train_health_model.py --data-dir ../data/health --epochs 50 --batch-size 32 --lr 0.001 --output models/plant_health_v2.pt
```

### 3. عرض إحصائيات البيانات

```bash
python add_training_images_to_db.py --data-dir ../data/health --stats-only
```

---

## هيكل المجلدات

```
data/health/
├── train/
│   ├── healthy/
│   ├── sick/
│   ├── dry/
│   ├── overwatered/
│   ├── pest_damage/
│   └── nutrient_deficiency/
└── val/
    └── (نفس المجلدات)
```

ضع صورك في المجلدات المناسبة ثم شغل السكربتات أعلاه.
