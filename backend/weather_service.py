import os
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class WeatherService:
    
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY', '')
        self.api_url = os.getenv('WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5/weather')
        
        if not self.api_key:
            logger.warning("⚠️ مفتاح API الطقس غير موجود. سيتم استخدام بيانات افتراضية.")
    
    def get_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("لا يوجد مفتاح API للطقس")
            return self._get_default_weather()
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',  # درجة مئوية
                'lang': 'ar'  # اللغة العربية
            }
            
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # استخراج البيانات المهمة
            weather_data = {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'weather_main': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'weather_icon': data['weather'][0]['icon'],
                'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).isoformat(),
                'sunset': datetime.fromtimestamp(data['sys']['sunset']).isoformat(),
                'city': data.get('name', 'غير معروف'),
                'timestamp': datetime.now().isoformat()
            }
            
            # إضافة بيانات المطر إذا كانت موجودة
            if 'rain' in data:
                weather_data['rain_1h'] = data['rain'].get('1h', 0)
                weather_data['rain_3h'] = data['rain'].get('3h', 0)
            else:
                weather_data['rain_1h'] = 0
                weather_data['rain_3h'] = 0
            
            logger.info(f"✅ تم الحصول على بيانات الطقس لـ {weather_data['city']}")
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطأ في الاتصال بـ API الطقس: {e}")
            return self._get_default_weather()
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة بيانات الطقس: {e}")
            return self._get_default_weather()
    
    def _get_default_weather(self) -> Dict[str, Any]:
        return {
            'temperature': 25.0,
            'feels_like': 25.0,
            'humidity': 60,
            'pressure': 1013,
            'wind_speed': 5.0,
            'clouds': 20,
            'weather_main': 'Clear',
            'weather_description': 'سماء صافية',
            'weather_icon': '01d',
            'rain_1h': 0,
            'rain_3h': 0,
            'sunrise': datetime.now().replace(hour=6, minute=0).isoformat(),
            'sunset': datetime.now().replace(hour=18, minute=0).isoformat(),
            'city': 'غير معروف',
            'timestamp': datetime.now().isoformat(),
            'is_default': True
        }
    
    def generate_weather_advice(
        self, 
        weather_data: Dict[str, Any], 
        species_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        advice = {
            'recommendations': [],
            'warnings': [],
            'optimal_conditions': True,
            'weather_summary': weather_data.get('weather_description', 'غير معروف')
        }
        
        temp = weather_data.get('temperature', 25)
        humidity = weather_data.get('humidity', 60)
        wind_speed = weather_data.get('wind_speed', 0)
        rain = weather_data.get('rain_1h', 0)
        clouds = weather_data.get('clouds', 0)
        
        # تحليل درجة الحرارة
        if species_info:
            temp_min = species_info.get('temp_min', 10)
            temp_max = species_info.get('temp_max', 35)
            
            if temp < temp_min:
                advice['warnings'].append(f"⚠️ الجو بارد جداً ({temp}°C). أدخل النبتة للداخل")
                advice['optimal_conditions'] = False
            elif temp > temp_max:
                advice['warnings'].append(f"⚠️ الجو حار جداً ({temp}°C). ضع النبتة في الظل")
                advice['optimal_conditions'] = False
            elif temp_min <= temp <= temp_max:
                advice['recommendations'].append(f"✅ درجة الحرارة مثالية ({temp}°C)")
        else:
            if temp < 10:
                advice['warnings'].append(f"⚠️ الجو بارد جداً ({temp}°C)")
                advice['optimal_conditions'] = False
            elif temp > 35:
                advice['warnings'].append(f"⚠️ الجو حار جداً ({temp}°C)")
                advice['optimal_conditions'] = False
        
        # تحليل المطر
        if rain > 0:
            advice['recommendations'].append(f"🌧️ يوجد مطر ({rain}mm). لا حاجة للسقي اليوم")
            advice['recommendations'].append("💡 تأكد من تصريف الماء الزائد")
        
        # تحليل الرياح
        if wind_speed > 15:
            advice['warnings'].append(f"💨 رياح قوية ({wind_speed} م/ث). احمِ النباتات الضعيفة")
            advice['optimal_conditions'] = False
        elif wind_speed > 10:
            advice['recommendations'].append(f"🌬️ رياح معتدلة ({wind_speed} م/ث). راقب النباتات")
        
        # تحليل الرطوبة
        if humidity < 30:
            advice['recommendations'].append(f"💧 رطوبة منخفضة ({humidity}%). رش الأوراق بالماء")
        elif humidity > 80:
            advice['recommendations'].append(f"💦 رطوبة عالية ({humidity}%). راقب الأمراض الفطرية")
        
        # تحليل الغيوم والضوء
        if species_info:
            sunlight_req = species_info.get('sunlight_requirements', 'medium')
            
            if clouds > 80:
                if sunlight_req == 'high':
                    advice['warnings'].append("☁️ سماء غائمة. النبات يحتاج ضوء أكثر")
                    advice['optimal_conditions'] = False
                else:
                    advice['recommendations'].append("☁️ سماء غائمة. مناسب للنباتات التي تحب الظل")
            elif clouds < 20:
                if sunlight_req == 'low':
                    advice['warnings'].append("☀️ ضوء شمس قوي. ضع النبات في الظل")
                else:
                    advice['recommendations'].append("☀️ ضوء شمس ممتاز للنباتات")
        
        # نصائح عامة
        if not advice['recommendations'] and not advice['warnings']:
            advice['recommendations'].append("✅ الظروف الجوية مناسبة للنباتات")
        
        return advice
    
    def get_weather_forecast(self, lat: float, lon: float, days: int = 3) -> Optional[List[Dict[str, Any]]]:
        if not self.api_key:
            logger.warning("لا يوجد مفتاح API للطقس")
            return None
        
        try:
            forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ar',
                'cnt': days * 8  # 8 قراءات في اليوم (كل 3 ساعات)
            }
            
            response = requests.get(forecast_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            forecasts = []
            
            for item in data['list']:
                forecast = {
                    'datetime': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'weather_description': item['weather'][0]['description'],
                    'rain_probability': item.get('pop', 0) * 100,  # احتمالية المطر
                    'wind_speed': item['wind']['speed']
                }
                forecasts.append(forecast)
            
            logger.info(f"✅ تم الحصول على توقعات الطقس لـ {days} أيام")
            return forecasts
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على توقعات الطقس: {e}")
            return None
    
    def should_water_plant(
        self, 
        weather_data: Dict[str, Any],
        soil_moisture: Optional[float] = None,
        species_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        decision = {
            'should_water': False,
            'urgency': 'low',  # low, medium, high
            'reason': '',
            'best_time': 'morning'  # morning, evening, now
        }
        
        rain = weather_data.get('rain_1h', 0)
        temp = weather_data.get('temperature', 25)
        humidity = weather_data.get('humidity', 60)
        
        # إذا كان هناك مطر، لا حاجة للسقي
        if rain > 2:
            decision['should_water'] = False
            decision['reason'] = f"يوجد مطر ({rain}mm). لا حاجة للسقي"
            return decision
        
        # التحقق من رطوبة التربة
        if soil_moisture is not None:
            if soil_moisture < 20:
                decision['should_water'] = True
                decision['urgency'] = 'high'
                decision['reason'] = f"التربة جافة جداً ({soil_moisture}%)"
                decision['best_time'] = 'now'
            elif soil_moisture < 40:
                decision['should_water'] = True
                decision['urgency'] = 'medium'
                decision['reason'] = f"التربة تحتاج سقي ({soil_moisture}%)"
            elif soil_moisture > 70:
                decision['should_water'] = False
                decision['reason'] = f"التربة رطبة كافية ({soil_moisture}%)"
                return decision
        
        # تحليل الطقس
        if temp > 30 and humidity < 40:
            if not decision['should_water']:
                decision['should_water'] = True
                decision['urgency'] = 'medium'
            decision['reason'] += " الجو حار وجاف"
            decision['best_time'] = 'evening'
        elif temp < 15:
            decision['best_time'] = 'morning'
            if decision['urgency'] == 'low':
                decision['reason'] += " الجو بارد، قلل السقي"
        
        # نصائح بناءً على نوع النبات
        if species_info:
            watering_days = species_info.get('watering_days_default', 3)
            if watering_days <= 2:
                decision['reason'] += f" (النبات يحتاج سقي متكرر كل {watering_days} أيام)"
        
        if not decision['reason']:
            decision['reason'] = "الظروف طبيعية"
        
        return decision


# إنشاء نسخة عامة من الخدمة
weather_service = WeatherService()
