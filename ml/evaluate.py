# سكربت تقييم نموذج التعرف على النباتات
# Plant Recognition Model Evaluation Script

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
from PIL import Image
import json
import argparse
from pathlib import Path
import logging
from tqdm import tqdm
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# استيراد النموذج من backend (مرفوع مع الريبو) ثم ml للتدريب
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
sys.path.insert(0, str(Path(__file__).parent))
from plant_classifier import PlantClassifier
from train import PlantDataset, get_transforms

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_model_weights(model_path):
    try:
        saved_data = torch.load(model_path, map_location='cpu')
        
        # التحقق من التنسيق الجديد
        if isinstance(saved_data, dict) and 'model_state_dict' in saved_data:
            print("🔍 فحص أوزان النموذج (تنسيق جديد):")
            state_dict = saved_data['model_state_dict']
            print(f"📊 عدد المعاملات: {len(state_dict)}")
            print(f"🏗️ المعمارية: {saved_data.get('architecture', 'غير معروف')}")
            print(f"📈 عدد الفئات: {saved_data.get('num_classes', 'غير معروف')}")
            print(f"🔄 العصر: {saved_data.get('epoch', 'غير معروف')}")
            print(f"📊 دقة التحقق: {saved_data.get('val_accuracy', 'غير معروف')}")
        else:
            print("🔍 فحص أوزان النموذج (تنسيق قديم):")
            state_dict = saved_data
            print(f"📊 عدد المعاملات: {len(state_dict)}")
        
        # عرض أول 10 معاملات
        print("📋 أول 10 معاملات:")
        for i, (key, value) in enumerate(state_dict.items()):
            if i < 10:
                print(f"   {key}: {value.shape}")
            else:
                break
        
        # البحث عن معاملات محددة
        problematic_keys = [k for k in state_dict.keys() if 'running_var' in k or 'num_batches_tracked' in k]
        if problematic_keys:
            print(f"⚠️ معاملات قد تسبب مشاكل: {problematic_keys}")
        
        return state_dict
    except Exception as e:
        print(f"❌ خطأ في فحص أوزان النموذج: {e}")
        return None

def load_model(model_path, num_classes, arch='efficientnet_b4', device='cpu'):
    # فحص أوزان النموذج أولاً
    state_dict = inspect_model_weights(model_path)
    if state_dict is None:
        raise ValueError("لا يمكن فحص أوزان النموذج")
    
    # محاولة تحميل النموذج مع pretrained=True أولاً
    try:
        model = PlantClassifier(num_classes, arch, pretrained=True)
        model.load_state_dict(state_dict)
        model.eval()
        return model
    except Exception as e:
        print(f"⚠️ خطأ في تحميل النموذج مع pretrained=True: {e}")
        print("🔄 محاولة تحميل النموذج مع pretrained=False...")
        try:
            model = PlantClassifier(num_classes, arch, pretrained=False)
            model.load_state_dict(state_dict)
            model.eval()
            return model
        except Exception as e2:
            print(f"❌ خطأ في تحميل النموذج مع pretrained=False: {e2}")
            print("🔄 محاولة تحميل النموذج مع strict=False...")
            try:
                model = PlantClassifier(num_classes, arch, pretrained=False)
                model.load_state_dict(state_dict, strict=False)
                model.eval()
                return model
            except Exception as e3:
                print(f"❌ خطأ في تحميل النموذج مع strict=False: {e3}")
                raise e3

def evaluate_model_comprehensive(model, dataloader, device, class_names):
    model.eval()
    all_predictions = []
    all_labels = []
    all_probabilities = []
    all_top3_predictions = []
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="التقييم"):
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            probabilities = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs, 1)
            
            # Top-3 predictions
            top3_preds = torch.topk(probabilities, 3, dim=1)[1]
            
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probabilities.extend(probabilities.cpu().numpy())
            all_top3_predictions.extend(top3_preds.cpu().numpy())
    
    # حساب المقاييس الأساسية
    accuracy = accuracy_score(all_labels, all_predictions)
    
    # حساب Top-3 Accuracy
    top3_correct = 0
    for i, true_label in enumerate(all_labels):
        if true_label in all_top3_predictions[i]:
            top3_correct += 1
    top3_accuracy = top3_correct / len(all_labels)
    
    # تقرير التصنيف التفصيلي
    report = classification_report(all_labels, all_predictions, 
                                 target_names=class_names, 
                                 output_dict=True)
    
    # مصفوفة الالتباس
    cm = confusion_matrix(all_labels, all_predictions)
    
    # حساب Precision, Recall, F1 لكل فئة
    precision_per_class = []
    recall_per_class = []
    f1_per_class = []
    
    for i, class_name in enumerate(class_names):
        if i in report:
            precision_per_class.append(report[i]['precision'])
            recall_per_class.append(report[i]['recall'])
            f1_per_class.append(report[i]['f1-score'])
        else:
            precision_per_class.append(0.0)
            recall_per_class.append(0.0)
            f1_per_class.append(0.0)
    
    # حساب المتوسطات
    macro_precision = np.mean(precision_per_class)
    macro_recall = np.mean(recall_per_class)
    macro_f1 = np.mean(f1_per_class)
    
    # حساب AUC (للفئات المتعددة)
    try:
        auc_scores = []
        for i in range(len(class_names)):
            binary_labels = [1 if label == i else 0 for label in all_labels]
            binary_probs = [prob[i] for prob in all_probabilities]
            if len(set(binary_labels)) > 1:  # تأكد من وجود فئتين
                auc = roc_auc_score(binary_labels, binary_probs)
                auc_scores.append(auc)
        
        macro_auc = np.mean(auc_scores) if auc_scores else 0.0
    except:
        macro_auc = 0.0
    
    return {
        'accuracy': accuracy,
        'top3_accuracy': top3_accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'macro_auc': macro_auc,
        'classification_report': report,
        'confusion_matrix': cm,
        'precision_per_class': precision_per_class,
        'recall_per_class': recall_per_class,
        'f1_per_class': f1_per_class,
        'predictions': all_predictions,
        'labels': all_labels,
        'probabilities': all_probabilities,
        'class_names': class_names
    }

def plot_confusion_matrix(cm, class_names, save_path):
    plt.figure(figsize=(15, 12))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('مصفوفة الالتباس - Confusion Matrix', fontsize=16)
    plt.xlabel('التوقعات المتوقعة', fontsize=14)
    plt.ylabel('التوقعات الفعلية', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_per_class_metrics(metrics, save_path):
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Precision لكل فئة
    axes[0, 0].bar(range(len(metrics['class_names'])), metrics['precision_per_class'])
    axes[0, 0].set_title('Precision لكل فئة')
    axes[0, 0].set_xlabel('الفئات')
    axes[0, 0].set_ylabel('Precision')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Recall لكل فئة
    axes[0, 1].bar(range(len(metrics['class_names'])), metrics['recall_per_class'])
    axes[0, 1].set_title('Recall لكل فئة')
    axes[0, 1].set_xlabel('الفئات')
    axes[0, 1].set_ylabel('Recall')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # F1-Score لكل فئة
    axes[1, 0].bar(range(len(metrics['class_names'])), metrics['f1_per_class'])
    axes[1, 0].set_title('F1-Score لكل فئة')
    axes[1, 0].set_xlabel('الفئات')
    axes[1, 0].set_ylabel('F1-Score')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # مقارنة المقاييس الإجمالية
    overall_metrics = ['Accuracy', 'Top-3 Accuracy', 'Macro Precision', 'Macro Recall', 'Macro F1']
    overall_values = [
        metrics['accuracy'],
        metrics['top3_accuracy'],
        metrics['macro_precision'],
        metrics['macro_recall'],
        metrics['macro_f1']
    ]
    
    axes[1, 1].bar(overall_metrics, overall_values)
    axes[1, 1].set_title('المقاييس الإجمالية')
    axes[1, 1].set_ylabel('القيمة')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_detailed_report(metrics, save_path):
    report_lines = []
    
    # العنوان
    report_lines.append("# تقرير تقييم نموذج التعرف على النباتات")
    report_lines.append(f"تاريخ التقييم: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # المقاييس الإجمالية
    report_lines.append("## المقاييس الإجمالية")
    report_lines.append(f"- **الدقة الإجمالية (Accuracy)**: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    report_lines.append(f"- **دقة Top-3**: {metrics['top3_accuracy']:.4f} ({metrics['top3_accuracy']*100:.2f}%)")
    report_lines.append(f"- **Precision المتوسط**: {metrics['macro_precision']:.4f}")
    report_lines.append(f"- **Recall المتوسط**: {metrics['macro_recall']:.4f}")
    report_lines.append(f"- **F1-Score المتوسط**: {metrics['macro_f1']:.4f}")
    report_lines.append(f"- **AUC المتوسط**: {metrics['macro_auc']:.4f}")
    report_lines.append("")
    
    # تقييم الأداء
    report_lines.append("## تقييم الأداء")
    if metrics['accuracy'] >= 0.8:
        report_lines.append("✅ **ممتاز**: النموذج يحقق دقة عالية (≥80%)")
    elif metrics['accuracy'] >= 0.7:
        report_lines.append("✅ **جيد**: النموذج يحقق دقة مقبولة (≥70%)")
    elif metrics['accuracy'] >= 0.6:
        report_lines.append("⚠️ **متوسط**: النموذج يحتاج تحسين (≥60%)")
    else:
        report_lines.append("❌ **ضعيف**: النموذج يحتاج إعادة تدريب (<60%)")
    
    if metrics['top3_accuracy'] >= 0.95:
        report_lines.append("✅ **ممتاز**: دقة Top-3 عالية جداً (≥95%)")
    elif metrics['top3_accuracy'] >= 0.9:
        report_lines.append("✅ **جيد**: دقة Top-3 جيدة (≥90%)")
    else:
        report_lines.append("⚠️ **يحتاج تحسين**: دقة Top-3 أقل من 90%")
    
    report_lines.append("")
    
    # تفاصيل كل فئة
    report_lines.append("## تفاصيل الأداء لكل فئة")
    report_lines.append("| الفئة | Precision | Recall | F1-Score | عدد العينات |")
    report_lines.append("|-------|-----------|--------|----------|-------------|")
    
    for i, class_name in enumerate(metrics['class_names']):
        if i in metrics['classification_report']:
            class_report = metrics['classification_report'][i]
            support = class_report['support']
            report_lines.append(f"| {class_name} | {class_report['precision']:.3f} | {class_report['recall']:.3f} | {class_report['f1-score']:.3f} | {support} |")
    
    report_lines.append("")
    
    # تحليل الأخطاء
    report_lines.append("## تحليل الأخطاء الشائعة")
    cm = metrics['confusion_matrix']
    
    # العثور على أكبر أخطاء التصنيف
    errors = []
    for i in range(len(metrics['class_names'])):
        for j in range(len(metrics['class_names'])):
            if i != j and cm[i, j] > 0:
                errors.append((cm[i, j], metrics['class_names'][i], metrics['class_names'][j]))
    
    errors.sort(reverse=True)
    
    if errors:
        report_lines.append("أكثر الأخطاء شيوعاً:")
        for count, true_class, pred_class in errors[:5]:
            report_lines.append(f"- {count} عينة من فئة '{true_class}' تم تصنيفها خطأ كـ '{pred_class}'")
    
    report_lines.append("")
    
    # التوصيات
    report_lines.append("## التوصيات")
    if metrics['accuracy'] < 0.8:
        report_lines.append("- زيادة عدد عينات التدريب")
        report_lines.append("- تحسين تقنيات زيادة البيانات")
        report_lines.append("- تجربة معماريات نماذج مختلفة")
    
    if metrics['top3_accuracy'] < 0.95:
        report_lines.append("- تحسين دقة Top-3 مهم للتطبيق العملي")
    
    if metrics['macro_f1'] < 0.7:
        report_lines.append("- معالجة عدم التوازن في البيانات")
        report_lines.append("- استخدام تقنيات معالجة الفئات النادرة")
    
    # حفظ التقرير
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

def main():
    parser = argparse.ArgumentParser(description='تقييم نموذج التعرف على النباتات')
    parser.add_argument('--model-path', type=str, required=True, help='مسار النموذج المدرب')
    parser.add_argument('--data-dir', type=str, required=True, help='مسار مجلد البيانات')
    parser.add_argument('--csv-file', type=str, required=True, help='مسار ملف CSV')
    parser.add_argument('--arch', type=str, default='efficientnet_b4', 
                       choices=['efficientnet_b4', 'resnet50', 'convnext_base'],
                       help='معمارية النموذج')
    parser.add_argument('--batch-size', type=int, default=32, help='حجم الدفعة')
    parser.add_argument('--output-dir', type=str, required=True, help='مجلد حفظ النتائج')
    parser.add_argument('--device', type=str, default='auto', help='جهاز التقييم')
    
    args = parser.parse_args()
    
    # تحديد الجهاز
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    logger.info(f"استخدام الجهاز: {device}")
    
    # إنشاء مجلد النتائج
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # تحميل البيانات
    logger.info("تحميل البيانات...")
    _, val_transform = get_transforms()
    dataset = PlantDataset(args.csv_file, args.data_dir, transform=val_transform, is_training=False)
    
    # إنشاء DataLoader
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    # تحميل النموذج
    logger.info("تحميل النموذج...")
    model = load_model(args.model_path, len(dataset.classes), args.arch, device)
    model = model.to(device)
    
    # التقييم الشامل
    logger.info("بدء التقييم الشامل...")
    metrics = evaluate_model_comprehensive(model, dataloader, device, dataset.classes)
    
    # طباعة النتائج
    logger.info("="*50)
    logger.info("نتائج التقييم:")
    logger.info(f"الدقة الإجمالية: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    logger.info(f"دقة Top-3: {metrics['top3_accuracy']:.4f} ({metrics['top3_accuracy']*100:.2f}%)")
    logger.info(f"Precision المتوسط: {metrics['macro_precision']:.4f}")
    logger.info(f"Recall المتوسط: {metrics['macro_recall']:.4f}")
    logger.info(f"F1-Score المتوسط: {metrics['macro_f1']:.4f}")
    logger.info(f"AUC المتوسط: {metrics['macro_auc']:.4f}")
    logger.info("="*50)
    
    # حفظ النتائج
    logger.info("حفظ النتائج...")
    
    # رسم مصفوفة الالتباس
    plot_confusion_matrix(metrics['confusion_matrix'], dataset.classes, 
                         output_dir / 'confusion_matrix.png')
    
    # رسم مقاييس كل فئة
    plot_per_class_metrics(metrics, output_dir / 'per_class_metrics.png')
    
    # توليد التقرير المفصل
    generate_detailed_report(metrics, output_dir / 'evaluation_report.md')
    
    # حفظ المقاييس كـ JSON
    metrics_to_save = {
        'accuracy': metrics['accuracy'],
        'top3_accuracy': metrics['top3_accuracy'],
        'macro_precision': metrics['macro_precision'],
        'macro_recall': metrics['macro_recall'],
        'macro_f1': metrics['macro_f1'],
        'macro_auc': metrics['macro_auc'],
        'precision_per_class': metrics['precision_per_class'],
        'recall_per_class': metrics['recall_per_class'],
        'f1_per_class': metrics['f1_per_class'],
        'class_names': metrics['class_names'],
        'confusion_matrix': metrics['confusion_matrix'].tolist(),
        'evaluation_date': datetime.now().isoformat()
    }
    
    with open(output_dir / 'evaluation_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics_to_save, f, ensure_ascii=False, indent=2)
    
    logger.info(f"تم حفظ جميع النتائج في: {output_dir}")
    logger.info("انتهى التقييم بنجاح!")

if __name__ == "__main__":
    main()
