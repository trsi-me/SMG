# دليل التدريب - إضافة صور النباتات
# Training Guide - Adding Plant Images

## أين تضيف صور التدريب؟

### المسار الأساسي:
```
smg/
└── data/
    └── health/
        ├── train/
        │   ├── healthy/          ← أضف صور النباتات الصحية هنا
        │   ├── sick/             ← أضف صور النباتات المريضة هنا
        │   ├── dry/              ← أضف صور النباتات الجافة هنا
        │   ├── overwatered/      ← أضف صور النباتات المروية زائد هنا
        │   ├── pest_damage/      ← أضف صور تلف الآفات هنا
        │   └── nutrient_deficiency/ ← أضف صور نقص العناصر هنا
        └── val/
            ├── healthy/          ← صور التحقق (10-20% من البيانات)
            ├── sick/
            ├── dry/
            ├── overwatered/
            ├── pest_damage/
            └── nutrient_deficiency/
```

### للمزيد من النباتات (أنواع مختلفة):
```
smg/
└── ml/
    └── data/
        ├── train/
        │   ├── tomato/           ← صور الطماطم
        │   ├── pepper/           ← صور الفلفل
        │   ├── cucumber/         ← صور الخيار
        │   ├── basil/            ← صور الريحان
        │   └── ... (أضف أنواع أخرى)
        └── val/
            ├── tomato/
            ├── pepper/
            └── ...
```

## كيفية إضافة الصور


### الطريقة 2: إضافة يدوي
1. التقط صوراً للنباتات أو حمّل من الإنترنت
2. سمّي الصور بشكل واضح: `plant_name_1.jpg`, `plant_name_2.jpg`
3. ضعها في المجلد المناسب حسب الحالة الصحية

### الطريقة 3: استخدام Kaggle Datasets
```python
# أمثلة على datasets جيدة:
# - PlantVillage Dataset
# - Plant Pathology 2020
# - New Plant Diseases Dataset
```

## النباتات المقترحة للإضافة

### نباتات شائعة في المنطقة العربية:

#### 1. الخضروات:
- **طماطم** (Tomato) - Solanum lycopersicum
- **فلفل** (Pepper) - Capsicum annuum
- **خيار** (Cucumber) - Cucumis sativus
- **باذنجان** (Eggplant) - Solanum melongena
- **كوسا** (Zucchini) - Cucurbita pepo
- **بصل** (Onion) - Allium cepa
- **ثوم** (Garlic) - Allium sativum

#### 2. الأعشاب:
- **ريحان** (Basil) - Ocimum basilicum
- **نعناع** (Mint) - Mentha
- **بقدونس** (Parsley) - Petroselinum crispum
- **كزبرة** (Coriander) - Coriandrum sativum
- **شبت** (Dill) - Anethum graveolens

#### 3. الفواكه:
- **ليمون** (Lemon) - Citrus limon
- **برتقال** (Orange) - Citrus sinensis
- **رمان** (Pomegranate) - Punica granatum
- **تين** (Fig) - Ficus carica
- **زيتون** (Olive) - Olea europaea

#### 4. نباتات الزينة:
- **ورد** (Rose) - Rosa
- **جاردينيا** (Gardenia) - Gardenia jasminoides
- **ياسمين** (Jasmine) - Jasminum
- **لافندر** (Lavender) - Lavandula
- **صبار** (Cactus) - Cactaceae

#### 5. نباتات محلية:
- **نخيل** (Date Palm) - Phoenix dactylifera
- **أكاسيا** (Acacia) - Acacia
- **شجرة المورينجا** (Moringa) - Moringa oleifera
- **الزعتر** (Thyme) - Thymus vulgaris

## نصائح لجمع الصور

### 1. جودة الصور:
- **الدقة**: على الأقل 224x224 بكسل (الأفضل 512x512 أو أكبر)
- **الإضاءة**: صور في ضوء النهار الطبيعي
- **الخلفية**: خلفية بسيطة (أفضل: خلفية بيضاء أو خضراء)
- **الزاوية**: صور من زوايا مختلفة (أعلى، جانب، قريب)

### 2. عدد الصور المطلوب:
- **الحد الأدنى**: 50-100 صورة لكل فئة
- **المثالي**: 200-500 صورة لكل فئة
- **للتدريب الجيد**: 1000+ صورة لكل فئة

### 3. مصادر الصور:
- **PlantVillage Dataset**: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset
- **Plant Pathology 2020**: https://www.kaggle.com/c/plant-pathology-2020-fgvc7
- **iNaturalist**: https://www.inaturalist.org/
- **Google Images**: ابحث عن "plant name leaf" أو "plant name disease"

## خطوات التدريب

### 1. إعداد البيانات:
```bash
cd smg/ml
python -m data.prepare_data
```

### 2. تدريب النموذج:
```bash
python train_health_model.py --data-dir ../data/health --epochs 20 --batch-size 32
```

### 3. تقييم النموذج:
```bash
python evaluate.py --model-path models/efficientnet_b4_v1.pt --data-dir ../data/health/val
```

## تحسين الدقة

### 1. Data Augmentation:
- تدوير الصور (±15 درجة)
- تغيير السطوع (±20%)
- تغيير التباين (±10%)
- Flip أفقياً

### 2. Transfer Learning:
- استخدام نماذج مدربة مسبقاً (EfficientNet, ResNet)
- Fine-tuning على بياناتك

### 3. Regularization:
- Dropout (0.3-0.5)
- Weight Decay
- Early Stopping

## مراقبة التدريب

### استخدام TensorBoard:
```bash
tensorboard --logdir ml/results
```

### المقاييس المهمة:
- **Accuracy**: نسبة التصنيف الصحيح
- **Loss**: قيمة الخطأ
- **Precision/Recall**: لكل فئة
- **F1-Score**: متوسط Precision و Recall

## نصائح إضافية

1. **ابدأ صغيراً**: ابدأ بـ 3-5 أنواع نباتات شائعة
2. **ركز على الجودة**: صور جيدة أفضل من صور كثيرة سيئة
3. **تنويع البيانات**: صور من بيئات مختلفة (داخلية، خارجية، إضاءة مختلفة)
4. **توثيق البيانات**: احتفظ بسجل بالصور المضافة
5. **اختبار مستمر**: اختبر النموذج على صور جديدة بانتظام

## استكشاف الأخطاء

### المشكلة: دقة منخفضة
- **الحل**: أضف المزيد من الصور المتنوعة
- تحقق من توازن البيانات بين الفئات

### المشكلة: Overfitting
- **الحل**: استخدم Data Augmentation
- أضف Dropout layers
- استخدم Early Stopping

### المشكلة: النموذج لا يتعرف على نباتات جديدة
- **الحل**: أضف صور لهذه النباتات في بيانات التدريب
- استخدم Transfer Learning

## موارد إضافية

- [PlantNet](https://plantnet.org/) - قاعدة بيانات نباتات
- [iNaturalist](https://www.inaturalist.org/) - صور نباتات من المجتمع
- [PlantVillage](https://plantvillage.psu.edu/) - قاعدة بيانات أمراض النباتات

