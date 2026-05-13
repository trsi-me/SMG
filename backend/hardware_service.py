import serial
import serial.tools.list_ports
import logging
from typing import Dict, Optional, List
import json
import time

logger = logging.getLogger(__name__)

class HardwareService:
    
    def __init__(self):
        self.connected_devices = {}
        self.serial_connections = {}
    
    def list_available_ports(self) -> List[Dict[str, str]]:
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'manufacturer': port.manufacturer or 'Unknown'
            })
        return ports
    
    def connect_device(self, port: str, baudrate: int = 9600) -> bool:
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # انتظار تهيئة الجهاز
            
            self.serial_connections[port] = ser
            self.connected_devices[port] = {
                'port': port,
                'baudrate': baudrate,
                'connected': True,
                'last_update': time.time()
            }
            
            logger.info(f"✅ تم الاتصال بالجهاز على المنفذ: {port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بالجهاز: {e}")
            return False
    
    def disconnect_device(self, port: str) -> bool:
        try:
            if port in self.serial_connections:
                self.serial_connections[port].close()
                del self.serial_connections[port]
                del self.connected_devices[port]
                logger.info(f"✅ تم قطع الاتصال بالجهاز: {port}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في قطع الاتصال: {e}")
            return False
    
    def read_sensor_data(self, port: str) -> Optional[Dict]:
        if port not in self.serial_connections:
            return None
        
        try:
            ser = self.serial_connections[port]
            
            # إرسال طلب قراءة
            ser.write(b'READ\n')
            time.sleep(0.1)
            
            # قراءة البيانات
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                # محاولة تحليل JSON
                try:
                    data = json.loads(line)
                    self.connected_devices[port]['last_update'] = time.time()
                    return data
                except json.JSONDecodeError:
                    # إذا لم يكن JSON، محاولة تحليل نصي
                    return self._parse_text_data(line)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة البيانات: {e}")
            return None
    
    def _parse_text_data(self, line: str) -> Dict:
        # تنسيق متوقع: "SOIL:500,TEMP:25.5,HUMID:60.0"
        data = {}
        parts = line.split(',')
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                try:
                    data[key.lower()] = float(value)
                except ValueError:
                    data[key.lower()] = value
        
        return data
    
    def send_lcd_command(self, port: str, command: str, line1: str = "", line2: str = "") -> bool:
        if port not in self.serial_connections:
            return False
        
        try:
            ser = self.serial_connections[port]
            
            # تنسيق الأمر: LCD:LINE1:LINE2
            if line1 or line2:
                lcd_data = {
                    'command': 'LCD',
                    'line1': line1[:16],  # LCD 16x2
                    'line2': line2[:16]
                }
                ser.write(json.dumps(lcd_data).encode('utf-8'))
                ser.write(b'\n')
            else:
                # أمر بسيط
                ser.write(f'{command}\n'.encode('utf-8'))
            
            time.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال أمر LCD: {e}")
            return False
    
    def display_plant_info(self, port: str, plant_name: str, health_status: str) -> bool:
        return self.send_lcd_command(
            port,
            'LCD',
            f"Plant: {plant_name[:12]}",
            f"Status: {health_status[:12]}"
        )
    
    def display_sensor_data(self, port: str, soil: float, temp: float, humidity: float) -> bool:
        return self.send_lcd_command(
            port,
            'LCD',
            f"S:{soil:.0f}% T:{temp:.1f}C",
            f"H:{humidity:.0f}%"
        )
    
    def get_connected_devices(self) -> List[Dict]:
        return list(self.connected_devices.values())
    
    def is_connected(self, port: str) -> bool:
        return port in self.serial_connections and port in self.connected_devices

# إنشاء مثيل عام للخدمة
hardware_service = HardwareService()

