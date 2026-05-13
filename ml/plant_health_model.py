import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PlantHealthClassifier(nn.Module):
    
    def __init__(self, num_health_classes: int = 6, pretrained: bool = True):
        super(PlantHealthClassifier, self).__init__()
        
        # استخدام EfficientNet-B0 (أخف من B4 للتشغيل السريع)
        if pretrained:
            self.backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        else:
            self.backbone = models.efficientnet_b0(weights=None)
        
        # الحصول على عدد الميزات من آخر طبقة
        num_features = self.backbone.classifier[1].in_features
        
        # استبدال رأس التصنيف
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(512, num_health_classes)
        )
        
        self.num_health_classes = num_health_classes
        
        # أسماء الفئات
        self.health_classes = [
            'healthy',           # صحية
            'sick',             # مريضة
            'dry',              # جافة
            'overwatered',      # مروية بشكل زائد
            'pest_damage',      # تلف بسبب الآفات
            'nutrient_deficiency'  # نقص العناصر الغذائية
        ]
        
        # الأسماء بالعربية
        self.health_classes_ar = [
            'صحية',
            'مريضة',
            'جافة',
            'مروية زائد',
            'تلف آفات',
            'نقص غذائي'
        ]
    
    def forward(self, x):
        return self.backbone(x)
    
    def predict_health(self, x: torch.Tensor) -> Dict:
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            probabilities = F.softmax(outputs, dim=1)
            
            # الحصول على أعلى توقع
            confidence, predicted_idx = torch.max(probabilities, 1)
            
            predicted_class = self.health_classes[predicted_idx.item()]
            predicted_class_ar = self.health_classes_ar[predicted_idx.item()]
            
            # الحصول على جميع الاحتماليات
            all_probs = probabilities[0].cpu().numpy()
            
            predictions = []
            for i, (class_name, class_name_ar, prob) in enumerate(zip(
                self.health_classes, self.health_classes_ar, all_probs
            )):
                predictions.append({
                    'class': class_name,
                    'class_ar': class_name_ar,
                    'confidence': float(prob),
                    'rank': i + 1
                })
            
            # ترتيب حسب الثقة
            predictions.sort(key=lambda x: x['confidence'], reverse=True)
            
            # إعادة ترتيب الرتب
            for i, pred in enumerate(predictions):
                pred['rank'] = i + 1
            
            return {
                'predicted_class': predicted_class,
                'predicted_class_ar': predicted_class_ar,
                'confidence': float(confidence.item()),
                'all_predictions': predictions
            }


class PlantHealthAnalyzer:
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        try:
            # إنشاء النموذج باستخدام EfficientNet-B0 (كما تم تدريبه)
            self.model = PlantHealthClassifier()
            logger.info("📦 إنشاء نموذج صحة النبات باستخدام EfficientNet-B0")
            
            # تحميل الأوزان
            checkpoint = torch.load(model_path, map_location=self.device)
            
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"✅ تم تحميل نموذج صحة النبات من {model_path}")
            logger.info("✅ النموذج يستخدم EfficientNet-B0 (يتوافق مع plant_health_v1.pt)")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل نموذج صحة النبات: {e}")
            logger.error(f"⚠️ تأكد أن النموذج المدرب على EfficientNet-B0 وليس B4")
            return False
    
    def analyze_from_image(self, image_tensor: torch.Tensor) -> Dict:
        if self.model is None:
            # إذا لم يكن النموذج محملاً، استخدم تحليل افتراضي
            return self._default_health_analysis()
        
        try:
            image_tensor = image_tensor.to(self.device)
            result = self.model.predict_health(image_tensor)
            return result
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحليل صحة النبات: {e}")
            return self._default_health_analysis()
    
    def analyze_comprehensive(
        self,
        image_tensor: torch.Tensor,
        sensor_data: Optional[Dict] = None,
        species_info: Optional[Dict] = None
    ) -> Dict:
        # تحليل الصورة
        image_analysis = self.analyze_from_image(image_tensor)
        
        # تحليل بيانات الحساسات
        sensor_analysis = self._analyze_sensor_data(sensor_data, species_info)
        
        # دمج التحليلات
        comprehensive_analysis = self._merge_analyses(
            image_analysis, 
            sensor_analysis, 
            species_info
        )
        
        return comprehensive_analysis
    
    def _analyze_sensor_data(
        self, 
        sensor_data: Optional[Dict],
        species_info: Optional[Dict]
    ) -> Dict:
        analysis = {
            'soil_status': 'unknown',
            'temperature_status': 'unknown',
            'humidity_status': 'unknown',
            'warnings': [],
            'recommendations': []
        }
        
        if not sensor_data:
            return analysis
        
        # تحليل رطوبة التربة
        soil_raw = sensor_data.get('soil_raw', 500)
        soil_percent = (1023 - soil_raw) / 1023 * 100
        
        if soil_percent < 20:
            analysis['soil_status'] = 'very_dry'
            analysis['warnings'].append('التربة جافة جداً')
        elif soil_percent < 40:
            analysis['soil_status'] = 'dry'
            analysis['recommendations'].append('النبات يحتاج سقي')
        elif soil_percent > 80:
            analysis['soil_status'] = 'very_wet'
            analysis['warnings'].append('التربة مروية بشكل زائد')
        elif soil_percent > 60:
            analysis['soil_status'] = 'wet'
            analysis['recommendations'].append('التربة رطبة، لا حاجة للسقي')
        else:
            analysis['soil_status'] = 'optimal'
        
        # تحليل درجة الحرارة
        temp = sensor_data.get('temperature_c', 25)
        
        if species_info:
            temp_min = species_info.get('temp_min', 15)
            temp_max = species_info.get('temp_max', 30)
            
            if temp < temp_min - 5:
                analysis['temperature_status'] = 'very_cold'
                analysis['warnings'].append(f'درجة الحرارة منخفضة جداً ({temp}°C)')
            elif temp < temp_min:
                analysis['temperature_status'] = 'cold'
                analysis['recommendations'].append(f'درجة الحرارة منخفضة ({temp}°C)')
            elif temp > temp_max + 5:
                analysis['temperature_status'] = 'very_hot'
                analysis['warnings'].append(f'درجة الحرارة مرتفعة جداً ({temp}°C)')
            elif temp > temp_max:
                analysis['temperature_status'] = 'hot'
                analysis['recommendations'].append(f'درجة الحرارة مرتفعة ({temp}°C)')
            else:
                analysis['temperature_status'] = 'optimal'
        
        return analysis
    
    def _merge_analyses(
        self,
        image_analysis: Dict,
        sensor_analysis: Dict,
        species_info: Optional[Dict]
    ) -> Dict:
        predicted_health = image_analysis.get('predicted_class', 'unknown')
        confidence = image_analysis.get('confidence', 0.0)
        
        # تعديل التنبؤ بناءً على بيانات الحساسات
        if sensor_analysis['soil_status'] == 'very_dry' and predicted_health != 'dry':
            # إذا كانت التربة جافة جداً، ارفع احتمالية "جافة"
            for pred in image_analysis['all_predictions']:
                if pred['class'] == 'dry':
                    pred['confidence'] = min(pred['confidence'] + 0.2, 1.0)
        
        if sensor_analysis['soil_status'] == 'very_wet' and predicted_health != 'overwatered':
            # إذا كانت التربة مروية زائد، ارفع احتمالية "مروية زائد"
            for pred in image_analysis['all_predictions']:
                if pred['class'] == 'overwatered':
                    pred['confidence'] = min(pred['confidence'] + 0.2, 1.0)
        
        # إعادة ترتيب التنبؤات
        image_analysis['all_predictions'].sort(key=lambda x: x['confidence'], reverse=True)
        
        # تحديث التنبؤ الأعلى
        top_prediction = image_analysis['all_predictions'][0]
        image_analysis['predicted_class'] = top_prediction['class']
        image_analysis['predicted_class_ar'] = top_prediction['class_ar']
        image_analysis['confidence'] = top_prediction['confidence']
        
        # دمج التوصيات
        all_recommendations = []
        all_warnings = []
        
        # إضافة توصيات بناءً على حالة الصحة
        health_recommendations = self._get_health_recommendations(
            image_analysis['predicted_class'],
            species_info
        )
        all_recommendations.extend(health_recommendations)
        
        # إضافة توصيات الحساسات
        all_recommendations.extend(sensor_analysis.get('recommendations', []))
        all_warnings.extend(sensor_analysis.get('warnings', []))
        
        return {
            'health_status': image_analysis['predicted_class'],
            'health_status_ar': image_analysis['predicted_class_ar'],
            'confidence': image_analysis['confidence'],
            'all_predictions': image_analysis['all_predictions'],
            'sensor_analysis': sensor_analysis,
            'recommendations': all_recommendations,
            'warnings': all_warnings
        }
    
    def _get_health_recommendations(
        self,
        health_status: str,
        species_info: Optional[Dict]
    ) -> List[str]:
        recommendations = []
        
        if health_status == 'healthy':
            recommendations.append('✅ النبات في حالة صحية جيدة')
            recommendations.append('استمر في العناية الحالية')
        
        elif health_status == 'sick':
            recommendations.append('⚠️ النبات يظهر علامات مرض')
            recommendations.append('افحص الأوراق بحثاً عن بقع أو تغير في اللون')
            recommendations.append('قد تحتاج لاستخدام مبيد فطري')
        
        elif health_status == 'dry':
            recommendations.append('💧 النبات يحتاج سقي فوري')
            recommendations.append('تحقق من رطوبة التربة بانتظام')
        
        elif health_status == 'overwatered':
            recommendations.append('⚠️ النبات مروي بشكل زائد')
            recommendations.append('قلل كمية الماء وتأكد من تصريف التربة')
            recommendations.append('راقب علامات تعفن الجذور')
        
        elif health_status == 'pest_damage':
            recommendations.append('🐛 يوجد تلف بسبب الآفات')
            recommendations.append('افحص النبات بحثاً عن حشرات')
            recommendations.append('استخدم مبيد حشري مناسب')
        
        elif health_status == 'nutrient_deficiency':
            recommendations.append('🌱 النبات يعاني من نقص غذائي')
            recommendations.append('استخدم سماد متوازن')
            recommendations.append('تحقق من pH التربة')
        
        return recommendations
    
    def _default_health_analysis(self) -> Dict:
        return {
            'predicted_class': 'unknown',
            'predicted_class_ar': 'غير معروف',
            'confidence': 0.0,
            'all_predictions': [
                {
                    'class': 'unknown',
                    'class_ar': 'غير معروف',
                    'confidence': 1.0,
                    'rank': 1
                }
            ],
            'note': 'نموذج صحة النبات غير محمل. يتم استخدام تحليل افتراضي.'
        }


# إنشاء نسخة عامة من المحلل
plant_health_analyzer = PlantHealthAnalyzer()
