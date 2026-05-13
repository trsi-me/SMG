import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from PIL import Image
import os
import json
import argparse
from pathlib import Path
import logging
from tqdm import tqdm
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlantHealthDataset(Dataset):
    
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        
        # فئات الصحة
        self.health_classes = [
            'healthy',
            'sick',
            'dry',
            'overwatered',
            'pest_damage',
            'nutrient_deficiency'
        ]
        
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.health_classes)}
        
        # جمع الصور
        self.samples = []
        for class_name in self.health_classes:
            class_dir = self.data_dir / class_name
            if class_dir.exists():
                for img_path in class_dir.glob('*.jpg'):
                    self.samples.append((img_path, self.class_to_idx[class_name]))
                for img_path in class_dir.glob('*.png'):
                    self.samples.append((img_path, self.class_to_idx[class_name]))
        
        logger.info(f"عدد العينات: {len(self.samples)}")
        logger.info(f"عدد الفئات: {len(self.health_classes)}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            logger.warning(f"خطأ في تحميل الصورة {img_path}: {e}")
            image = Image.new('RGB', (224, 224), color='black')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def create_model(num_classes=6, pretrained=True):
    if pretrained:
        model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
    else:
        model = efficientnet_b0(weights=None)
    
    # استبدال رأس التصنيف
    num_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(num_features, 512),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(512, num_classes)
    )
    
    return model


def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc='Training')
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
            'loss': running_loss / (pbar.n + 1),
            'acc': 100 * correct / total
        })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc='Validation'):
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    val_loss = running_loss / len(dataloader)
    val_acc = 100 * correct / total
    
    return val_loss, val_acc, all_preds, all_labels


def main():
    parser = argparse.ArgumentParser(description='تدريب نموذج صحة النبات')
    parser.add_argument('--data-dir', type=str, required=True, help='مجلد البيانات')
    parser.add_argument('--epochs', type=int, default=50, help='عدد العصور')
    parser.add_argument('--batch-size', type=int, default=32, help='حجم الدفعة')
    parser.add_argument('--lr', type=float, default=0.001, help='معدل التعلم')
    parser.add_argument('--output', type=str, default='plant_health_v1.pt', help='مسار حفظ النموذج')
    
    args = parser.parse_args()
    
    # إعداد الجهاز
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"استخدام الجهاز: {device}")
    
    # إعداد التحويلات
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # تحميل البيانات
    train_dataset = PlantHealthDataset(
        Path(args.data_dir) / 'train',
        transform=train_transform
    )
    
    val_dataset = PlantHealthDataset(
        Path(args.data_dir) / 'val',
        transform=val_transform
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=4
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4
    )
    
    # إنشاء النموذج
    model = create_model(num_classes=6, pretrained=True)
    model = model.to(device)
    
    # إعداد التدريب
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True
    )
    
    # التدريب
    best_val_acc = 0.0
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }
    
    logger.info("=" * 50)
    logger.info("بدء التدريب")
    logger.info("=" * 50)
    
    for epoch in range(args.epochs):
        logger.info(f"\nEpoch {epoch+1}/{args.epochs}")
        
        # التدريب
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device
        )
        
        # التحقق
        val_loss, val_acc, val_preds, val_labels = validate(
            model, val_loader, criterion, device
        )
        
        # تحديث معدل التعلم
        scheduler.step(val_loss)
        
        # حفظ السجل
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        logger.info(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        logger.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # حفظ أفضل نموذج
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'health_classes': train_dataset.health_classes,
                'class_to_idx': train_dataset.class_to_idx
            }, args.output)
            logger.info(f"✅ تم حفظ أفضل نموذج - Val Acc: {val_acc:.2f}%")
    
    logger.info("=" * 50)
    logger.info(f"✅ انتهى التدريب - أفضل دقة: {best_val_acc:.2f}%")
    logger.info("=" * 50)
    
    # حفظ السجل
    history_path = Path(args.output).parent / 'health_training_history.json'
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
    
    logger.info(f"تم حفظ سجل التدريب في: {history_path}")


if __name__ == "__main__":
    main()
