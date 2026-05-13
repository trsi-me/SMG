# سكربت تحويل النماذج إلى تنسيقات مختلفة
# Model Conversion Script for Different Formats

import torch
import torch.onnx
import numpy as np
from pathlib import Path
import argparse
import logging
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
from plant_classifier import PlantClassifier

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_onnx(model_path, output_path, num_classes, arch='efficientnet_b4'):
    logger.info("تحويل النموذج إلى ONNX...")
    
    # تحميل النموذج
    model = PlantClassifier(num_classes, arch, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    # إنشاء عينة إدخال
    dummy_input = torch.randn(1, 3, 224, 224)
    
    # تصدير إلى ONNX
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    
    logger.info(f"تم حفظ نموذج ONNX في: {output_path}")

def convert_to_tflite(model_path, output_path, num_classes, arch='efficientnet_b4'):
    try:
        import tensorflow as tf
        from tensorflow import keras
        
        logger.info("تحويل النموذج إلى TensorFlow Lite...")
        
        # تحميل النموذج PyTorch
        model = PlantClassifier(num_classes, arch, pretrained=False)
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        model.eval()
        
        # تحويل إلى TensorFlow
        # ملاحظة: هذا يتطلب تحويل معقد، لذا سنستخدم نموذج مبسط
        logger.warning("تحويل TensorFlow Lite يتطلب إعدادات إضافية")
        logger.info("يُنصح باستخدام ONNX للاستخدام في التطبيقات المحمولة")
        
    except ImportError:
        logger.error("TensorFlow غير مثبت. يرجى تثبيته لاستخدام TensorFlow Lite")
        logger.info("يمكنك تثبيته باستخدام: pip install tensorflow")

def optimize_model_for_mobile(model_path, output_path, num_classes, arch='efficientnet_b4'):
    logger.info("تحسين النموذج للاستخدام المحمول...")
    
    # تحميل النموذج
    model = PlantClassifier(num_classes, arch, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    # تحسين النموذج
    model_optimized = torch.jit.script(model)
    
    # حفظ النموذج المحسن
    torch.jit.save(model_optimized, output_path)
    
    logger.info(f"تم حفظ النموذج المحسن في: {output_path}")

def quantize_model(model_path, output_path, num_classes, arch='efficientnet_b4'):
    logger.info("تكميم النموذج...")
    
    # تحميل النموذج
    model = PlantClassifier(num_classes, arch, pretrained=False)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    # تكميم النموذج
    model_quantized = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    
    # حفظ النموذج المكمم
    torch.save(model_quantized.state_dict(), output_path)
    
    logger.info(f"تم حفظ النموذج المكمم في: {output_path}")

def get_model_info(model_path):
    try:
        # محاولة تحميل معلومات النموذج
        model_dir = Path(model_path).parent
        info_file = model_dir / 'model_info.json'
        
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
            return info
        else:
            logger.warning("ملف معلومات النموذج غير موجود")
            return None
    except Exception as e:
        logger.error(f"خطأ في قراءة معلومات النموذج: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='تحويل النماذج إلى تنسيقات مختلفة')
    parser.add_argument('--model-path', type=str, required=True, help='مسار النموذج المدرب')
    parser.add_argument('--output-dir', type=str, required=True, help='مجلد حفظ النماذج المحولة')
    parser.add_argument('--arch', type=str, default='efficientnet_b4', 
                       choices=['efficientnet_b4', 'resnet50', 'convnext_base'],
                       help='معمارية النموذج')
    parser.add_argument('--num-classes', type=int, default=10, help='عدد الفئات')
    parser.add_argument('--formats', nargs='+', 
                      choices=['onnx', 'tflite', 'mobile', 'quantized'],
                      default=['onnx', 'mobile', 'quantized'],
                      help='التنسيقات المطلوبة')
    
    args = parser.parse_args()
    
    # إنشاء مجلد الحفظ
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # الحصول على معلومات النموذج
    model_info = get_model_info(args.model_path)
    if model_info:
        args.num_classes = model_info.get('num_classes', args.num_classes)
        args.arch = model_info.get('architecture', args.arch)
        logger.info(f"تم تحميل معلومات النموذج: {model_info['architecture']}, {args.num_classes} فئة")
    
    # تحويل النماذج
    for format_type in args.formats:
        logger.info(f"تحويل إلى تنسيق: {format_type}")
        
        if format_type == 'onnx':
            output_path = output_dir / f'model_{args.arch}.onnx'
            convert_to_onnx(args.model_path, output_path, args.num_classes, args.arch)
            
        elif format_type == 'tflite':
            output_path = output_dir / f'model_{args.arch}.tflite'
            convert_to_tflite(args.model_path, output_path, args.num_classes, args.arch)
            
        elif format_type == 'mobile':
            output_path = output_dir / f'model_{args.arch}_mobile.pt'
            optimize_model_for_mobile(args.model_path, output_path, args.num_classes, args.arch)
            
        elif format_type == 'quantized':
            output_path = output_dir / f'model_{args.arch}_quantized.pt'
            quantize_model(args.model_path, output_path, args.num_classes, args.arch)
    
    logger.info("تم الانتهاء من تحويل جميع النماذج!")

if __name__ == "__main__":
    main()
