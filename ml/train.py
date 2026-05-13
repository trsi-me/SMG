# سكربت تدريب نموذج التعرف على النباتات
# Plant Recognition Model Training Script

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights
import timm
import albumentations as A
from albumentations.pytorch import ToTensorV2
import pandas as pd
import numpy as np
from PIL import Image
import os
import json
import argparse
import shutil
from pathlib import Path
import logging
from tqdm import tqdm
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlantDataset(Dataset):
    
    def __init__(self, csv_file, data_dir, transform=None, is_training=True):
        self.data = pd.read_csv(csv_file)
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.is_training = is_training
        
        # إنشاء قاموس للتصنيفات
        self.classes = sorted(self.data['label'].unique())
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}
        
        logger.info(f"عدد الفئات: {len(self.classes)}")
        logger.info(f"عدد العينات: {len(self.data)}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        image_path = self.data_dir / row['image_path']
        
        # تحميل الصورة
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            logger.warning(f"خطأ في تحميل الصورة {image_path}: {e}")
            # إرجاع صورة فارغة في حالة الخطأ
            image = Image.new('RGB', (224, 224), color='black')
        
        # تطبيق التحويلات
        if self.transform:
            if isinstance(self.transform, A.Compose):
                # استخدام Albumentations
                image = np.array(image)
                transformed = self.transform(image=image)
                image = transformed['image']
            else:
                # استخدام torchvision transforms
                image = self.transform(image)
        
        # الحصول على التصنيف
        label = self.class_to_idx[row['label']]
        
        return image, label
    
def clear_torch_cache():
    cache_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print("✅ تم مسح cache PyTorch بنجاح")
        except Exception as e:
            print(f"⚠️ خطأ في مسح cache: {e}")

def convert_numpy_to_list(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    else:
        return obj

def check_data_distribution(dataset, class_names):
    print("📊 فحص توزيع البيانات:")
    
    # حساب عدد العينات لكل فئة
    class_counts = {}
    for i in range(len(dataset)):
        _, label = dataset[i]
        class_name = class_names[label]
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
    
    print(f"📈 إجمالي العينات: {len(dataset)}")
    print(f"📈 عدد الفئات: {len(class_counts)}")
    print("📊 توزيع العينات:")
    
    for class_name, count in class_counts.items():
        percentage = (count / len(dataset)) * 100
        print(f"   - {class_name}: {count} عينة ({percentage:.1f}%)")
    
    # تحذير إذا كانت البيانات غير متوازنة
    min_count = min(class_counts.values())
    max_count = max(class_counts.values())
    if max_count > min_count * 3:
        print("⚠️ تحذير: البيانات غير متوازنة بشكل كبير!")
        print("💡 يُنصح بإضافة المزيد من البيانات للفئات النادرة")
    
    return class_counts

    def get_class_weights(self):
        class_counts = self.data['label'].value_counts()
        total_samples = len(self.data)
        
        weights = []
        for cls in self.classes:
            count = class_counts.get(cls, 1)
            weight = total_samples / (len(self.classes) * count)
            weights.append(weight)
        
        return torch.FloatTensor(weights)

class PlantClassifier(nn.Module):
    
    def __init__(self, num_classes, model_name='efficientnet_b4', pretrained=True):
        super(PlantClassifier, self).__init__()
        
        self.num_classes = num_classes
        
        if model_name == 'efficientnet_b4':
            try:
                # محاولة تحميل النموذج مع الأوزان المسبقة
                self.backbone = efficientnet_b4(weights=EfficientNet_B4_Weights.IMAGENET1K_V1 if pretrained else None)
                self.backbone.classifier = nn.Linear(self.backbone.classifier[1].in_features, num_classes)
            except Exception as e:
                print(f"⚠️ خطأ في تحميل الأوزان المسبقة: {e}")
                print("🔄 محاولة تحميل النموذج باستخدام timm...")
                try:
                    # استخدام timm كبديل
                    self.backbone = timm.create_model('efficientnet_b4', pretrained=pretrained, num_classes=num_classes)
                except Exception as e2:
                    print(f"⚠️ خطأ في تحميل النموذج باستخدام timm: {e2}")
                    print("🔄 تحميل النموذج بدون أوزان مسبقة...")
                    self.backbone = efficientnet_b4(weights=None)
                    self.backbone.classifier = nn.Linear(self.backbone.classifier[1].in_features, num_classes)
        elif model_name == 'resnet50':
            from torchvision.models import resnet50, ResNet50_Weights
            self.backbone = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1 if pretrained else None)
            self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)
        elif model_name == 'convnext_base':
            self.backbone = timm.create_model('convnext_base', pretrained=pretrained, num_classes=num_classes)
        else:
            raise ValueError(f"نموذج غير مدعوم: {model_name}")
    
    def forward(self, x):
        return self.backbone(x)

def get_transforms():
    # تحويلات التدريب مع زيادة البيانات
    train_transform = A.Compose([
        A.Resize(256, 256),
        A.RandomCrop(224, 224),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.3),
        A.Rotate(limit=45, p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.5),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
        A.GaussianBlur(blur_limit=3, p=0.3),
        A.CoarseDropout(max_holes=8, max_height=32, max_width=32, p=0.3),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2()
    ])
    
    # تحويلات التحقق
    val_transform = A.Compose([
        A.Resize(224, 224),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2()
    ])
    
    return train_transform, val_transform

def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc="التدريب")
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        pbar.set_postfix({
            'Loss': f'{loss.item():.4f}',
            'Acc': f'{100.*correct/total:.2f}%'
        })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc

def validate_epoch(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_predictions = []
    all_labels = []
    
    with torch.no_grad():
        pbar = tqdm(dataloader, desc="التحقق")
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            pbar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100.*correct/total:.2f}%'
            })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc, all_predictions, all_labels

def evaluate_model(model, dataloader, device, class_names):
    model.eval()
    all_predictions = []
    all_labels = []
    all_probabilities = []
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="التقييم"):
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            probabilities = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs, 1)
            
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probabilities.extend(probabilities.cpu().numpy())
    
    # حساب المقاييس
    accuracy = accuracy_score(all_labels, all_predictions)
    
    # حساب Top-3 Accuracy
    top3_correct = 0
    for i, true_label in enumerate(all_labels):
        probs = all_probabilities[i]
        top3_indices = np.argsort(probs)[-3:]
        if true_label in top3_indices:
            top3_correct += 1
    top3_accuracy = top3_correct / len(all_labels)
    
    # تقرير التصنيف
    # الحصول على الفئات الفعلية الموجودة في البيانات
    unique_labels = np.unique(all_labels)
    unique_predictions = np.unique(all_predictions)
    all_unique_classes = np.unique(np.concatenate([unique_labels, unique_predictions]))
    
    # تحديد أسماء الفئات الموجودة فقط
    available_class_names = [class_names[i] for i in all_unique_classes if i < len(class_names)]
    
    try:
        report = classification_report(all_labels, all_predictions, 
                                     labels=all_unique_classes,
                                     target_names=available_class_names, 
                                     output_dict=True)
    except ValueError as e:
        print(f"⚠️ خطأ في classification_report: {e}")
        print(f"📊 الفئات الموجودة في البيانات: {all_unique_classes}")
        print(f"📊 عدد الفئات المتوقع: {len(class_names)}")
        # إنشاء تقرير بسيط
        report = {
            'accuracy': accuracy,
            'macro avg': {'precision': accuracy, 'recall': accuracy, 'f1-score': accuracy},
            'weighted avg': {'precision': accuracy, 'recall': accuracy, 'f1-score': accuracy}
        }
    
    # مصفوفة الالتباس
    cm = confusion_matrix(all_labels, all_predictions)
    
    return {
        'accuracy': accuracy,
        'top3_accuracy': top3_accuracy,
        'classification_report': report,
        'confusion_matrix': cm,
        'predictions': all_predictions,
        'labels': all_labels,
        'probabilities': all_probabilities
    }

def plot_confusion_matrix(cm, class_names, save_path):
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('مصفوفة الالتباس - Confusion Matrix')
    plt.xlabel('التوقعات المتوقعة')
    plt.ylabel('التوقعات الفعلية')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def save_model_info(model, metrics, args, save_dir):
    model_info = {
        'architecture': args.arch,
        'num_classes': args.num_classes,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'learning_rate': args.lr,
        'accuracy': float(metrics['accuracy']),
        'top3_accuracy': float(metrics['top3_accuracy']),
        'training_date': datetime.now().isoformat(),
        'class_names': list(metrics['classification_report'].keys())[:-3]  # استبعاد المتوسطات
    }
    
    # تحويل numpy arrays إلى قوائم Python
    model_info_serializable = convert_numpy_to_list(model_info)
    
    with open(save_dir / 'model_info.json', 'w', encoding='utf-8') as f:
        json.dump(model_info_serializable, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description='تدريب نموذج التعرف على النباتات')
    parser.add_argument('--data-dir', type=str, required=True, help='مسار مجلد البيانات')
    parser.add_argument('--csv-file', type=str, required=True, help='مسار ملف CSV')
    parser.add_argument('--arch', type=str, default='efficientnet_b4', 
                       choices=['efficientnet_b4', 'resnet50', 'convnext_base'],
                       help='معمارية النموذج')
    parser.add_argument('--epochs', type=int, default=50, help='عدد العصور')
    parser.add_argument('--batch-size', type=int, default=32, help='حجم الدفعة')
    parser.add_argument('--lr', type=float, default=1e-3, help='معدل التعلم')
    parser.add_argument('--output', type=str, required=True, help='مسار حفظ النموذج')
    parser.add_argument('--val-split', type=float, default=0.2, help='نسبة بيانات التحقق')
    parser.add_argument('--num-workers', type=int, default=4, help='عدد العمال')
    parser.add_argument('--device', type=str, default='auto', help='جهاز التدريب')
    
    args = parser.parse_args()
    
    # تحديد الجهاز
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    logger.info(f"استخدام الجهاز: {device}")
    
    # مسح cache PyTorch إذا لزم الأمر
    if args.arch == 'efficientnet_b4':
        print("🧹 مسح cache PyTorch لحل مشاكل التحميل...")
        clear_torch_cache()
    
    # إنشاء مجلد الحفظ
    save_dir = Path(args.output).parent
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # تحميل البيانات
    logger.info("تحميل البيانات...")
    dataset = PlantDataset(args.csv_file, args.data_dir, is_training=True)
    args.num_classes = len(dataset.classes)
    
    # فحص توزيع البيانات
    check_data_distribution(dataset, dataset.classes)
    
    # تقسيم البيانات
    # إذا كانت البيانات قليلة، استخدم نسبة أقل للتحقق
    if len(dataset) < 50:
        val_split = min(0.1, args.val_split)  # استخدام 10% كحد أقصى للتحقق
        print(f"⚠️ البيانات قليلة ({len(dataset)} عينة)، استخدام {val_split*100:.0f}% للتحقق")
    else:
        val_split = args.val_split
    
    train_size = int((1 - val_split) * len(dataset))
    val_size = len(dataset) - train_size
    
    # التأكد من وجود عينات في كل مجموعة
    if val_size == 0:
        val_size = 1
        train_size = len(dataset) - 1
        print("⚠️ عينة واحدة فقط للتحقق بسبب قلة البيانات")
    
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    # تطبيق التحويلات
    train_transform, val_transform = get_transforms()
    train_dataset.dataset.transform = train_transform
    val_dataset.dataset.transform = val_transform
    
    # إنشاء DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, 
                            shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, 
                          shuffle=False, num_workers=args.num_workers)
    
    # إنشاء النموذج
    logger.info(f"إنشاء النموذج: {args.arch}")
    model = PlantClassifier(args.num_classes, args.arch, pretrained=True)
    model = model.to(device)
    
    # تحديد المعايير والمحسن
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # تدريب النموذج
    logger.info("بدء التدريب...")
    best_val_acc = 0.0
    train_losses = []
    train_accs = []
    val_losses = []
    val_accs = []
    
    for epoch in range(args.epochs):
        logger.info(f"العصر {epoch+1}/{args.epochs}")
        
        # التدريب
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # التحقق
        val_loss, val_acc, _, _ = validate_epoch(model, val_loader, criterion, device)
        
        # تحديث معدل التعلم
        scheduler.step()
        
        # حفظ المقاييس
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        logger.info(f"العصر {epoch+1}: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, "
                   f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # حفظ أفضل نموذج
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            # حفظ النموذج مع معلومات إضافية
            model_save_data = {
                'model_state_dict': model.state_dict(),
                'architecture': args.arch,
                'num_classes': args.num_classes,
                'species_classes': dataset.classes,
                'class_to_idx': dataset.class_to_idx,
                'idx_to_class': dataset.idx_to_class,
                'epoch': epoch,
                'val_accuracy': val_acc,
                'train_accuracy': train_acc
            }
            torch.save(model_save_data, args.output)
            logger.info(f"تم حفظ أفضل نموذج بدقة: {val_acc:.2f}%")
    
    # التقييم النهائي
    logger.info("التقييم النهائي...")
    # تحميل النموذج المحفوظ
    saved_data = torch.load(args.output, map_location=device)
    if isinstance(saved_data, dict) and 'model_state_dict' in saved_data:
        model.load_state_dict(saved_data['model_state_dict'])
        logger.info(f"تم تحميل النموذج من العصر {saved_data.get('epoch', 'غير معروف')}")
    else:
        # للنماذج القديمة
        model.load_state_dict(saved_data)
    
    metrics = evaluate_model(model, val_loader, device, dataset.classes)
    
    # حفظ النتائج
    logger.info(f"دقة النموذج: {metrics['accuracy']:.4f}")
    logger.info(f"دقة Top-3: {metrics['top3_accuracy']:.4f}")
    
    # رسم مصفوفة الالتباس
    plot_confusion_matrix(metrics['confusion_matrix'], dataset.classes, 
                         save_dir / 'confusion_matrix.png')
    
    # حفظ معلومات النموذج
    save_model_info(model, metrics, args, save_dir)
    
    # حفظ مقاييس التدريب
    training_metrics = {
        'train_losses': train_losses,
        'train_accuracies': train_accs,
        'val_losses': val_losses,
        'val_accuracies': val_accs,
        'final_metrics': metrics
    }
    
    # تحويل numpy arrays إلى قوائم Python
    training_metrics_serializable = convert_numpy_to_list(training_metrics)
    
    with open(save_dir / 'training_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(training_metrics_serializable, f, ensure_ascii=False, indent=2)
    
    logger.info("تم الانتهاء من التدريب!")

if __name__ == "__main__":
    main()
