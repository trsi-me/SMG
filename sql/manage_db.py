import sqlite3
import json
import os
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class SMGDatabaseManager:
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            # المسار الافتراضي
            db_dir = Path(__file__).parent.parent / "data"
            db_dir.mkdir(exist_ok=True)
            self.db_path = str(db_dir / "smg_plants.db")
        self.connection = None
    
    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # للحصول على نتائج كـ dict
            print(f"تم الاتصال بقاعدة البيانات SQLite: {self.db_path}")
            return True
        except Exception as err:
            print(f"خطأ في الاتصال بقاعدة البيانات: {err}")
            return False
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("تم إغلاق الاتصال بقاعدة البيانات")
    
    def execute_sql_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            cursor = self.connection.cursor()
            cursor.executescript(sql_content)
            self.connection.commit()
            cursor.close()
            print(f"تم تنفيذ ملف SQL: {file_path}")
            return True
            
        except Exception as e:
            print(f"خطأ في تنفيذ ملف SQL: {e}")
            return False
    
    def get_species_count(self) -> int:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM species")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            print(f"خطأ في جلب عدد الأنواع: {e}")
            return 0
    
    def get_active_model_version(self) -> Optional[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM model_versions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"خطأ في جلب إصدار النموذج: {e}")
            return None
    
    def add_sensor_snapshot(self, device_id: str, soil_raw: int, temperature_c: float, 
                           humidity_percent: float, battery: Optional[float] = None) -> bool:
        try:
            # حساب soil_percent
            if soil_raw < 200:
                soil_percent = 0.0
            elif soil_raw > 800:
                soil_percent = 100.0
            else:
                soil_percent = ((soil_raw - 200) / 6.0)
            
            cursor = self.connection.cursor()
            query = """
            INSERT INTO sensor_snapshots (device_id, soil_raw, soil_percent, temperature_c, humidity_percent, battery)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (device_id, soil_raw, soil_percent, temperature_c, humidity_percent, battery))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"خطأ في إضافة قياس الحساس: {e}")
            return False
    
    def get_latest_sensor_data(self, device_id: str, limit: int = 10) -> list:
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT * FROM sensor_snapshots 
            WHERE device_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            cursor.execute(query, (device_id, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"خطأ في جلب بيانات الحساس: {e}")
            return []
    
    def add_scan(self, user_id: Optional[int], species_id: Optional[int], image_path: str, 
                 prediction_json: Dict, confidence: float, sensor_snapshot_id: Optional[int] = None,
                 latitude: Optional[float] = None, longitude: Optional[float] = None) -> Optional[int]:
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO scans (user_id, species_id, image_path, prediction_json, confidence, 
                             sensor_snapshot_id, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (user_id, species_id, image_path, json.dumps(prediction_json), 
                                 confidence, sensor_snapshot_id, latitude, longitude))
            self.connection.commit()
            scan_id = cursor.lastrowid
            cursor.close()
            return scan_id
        except Exception as e:
            print(f"خطأ في إضافة المسح: {e}")
            return None
    
    def add_feedback(self, scan_id: int, user_correction_species_id: Optional[int], 
                    correct_flag: bool, comment: Optional[str] = None) -> bool:
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO feedbacks (scan_id, correct_species_id, is_correct, feedback_text)
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(query, (scan_id, user_correction_species_id, 1 if correct_flag else 0, comment))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"خطأ في إضافة التغذية الراجعة: {e}")
            return False
    
    def get_training_images_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات صور التدريب"""
        try:
            cursor = self.connection.cursor()
            
            # إجمالي الصور
            cursor.execute("SELECT COUNT(*) FROM training_images WHERE is_active = 1")
            total = cursor.fetchone()[0]
            
            # حسب الفئة
            cursor.execute("""
                SELECT health_category, COUNT(*) as count 
                FROM training_images 
                WHERE is_active = 1 
                GROUP BY health_category
            """)
            by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            # حسب نوع البيانات
            cursor.execute("""
                SELECT dataset_type, COUNT(*) as count 
                FROM training_images 
                WHERE is_active = 1 
                GROUP BY dataset_type
            """)
            by_dataset = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.close()
            
            return {
                'total': total,
                'by_category': by_category,
                'by_dataset': by_dataset
            }
        except Exception as e:
            print(f"خطأ في جلب إحصائيات صور التدريب: {e}")
            return {'total': 0, 'by_category': {}, 'by_dataset': {}}

def main():
    parser = argparse.ArgumentParser(description='إدارة قاعدة بيانات SMG (SQLite)')
    parser.add_argument('--init', action='store_true', help='تهيئة قاعدة البيانات')
    parser.add_argument('--db-path', default=None, help='مسار قاعدة البيانات SQLite')
    
    args = parser.parse_args()
    
    # إنشاء مدير قاعدة البيانات
    db_manager = SMGDatabaseManager(db_path=args.db_path)
    
    if args.init:
        print("بدء تهيئة قاعدة البيانات SQLite...")
        
        # الاتصال بقاعدة البيانات
        if not db_manager.connect():
            return
        
        # تنفيذ ملف إنشاء الجداول
        sql_file_path = Path(__file__).parent / 'create_tables_sqlite.sql'
        if sql_file_path.exists():
            db_manager.execute_sql_file(str(sql_file_path))
        else:
            print(f"ملف SQL غير موجود: {sql_file_path}")
        
        # عرض إحصائيات قاعدة البيانات
        species_count = db_manager.get_species_count()
        print(f"عدد أنواع النباتات في قاعدة البيانات: {species_count}")
        
        # عرض إصدار النموذج النشط
        active_model = db_manager.get_active_model_version()
        if active_model:
            print(f"إصدار النموذج النشط: {active_model.get('version_tag', 'غير معروف')}")
        
        db_manager.disconnect()
        print("تمت تهيئة قاعدة البيانات بنجاح!")
    
    else:
        print("استخدم --init لتهيئة قاعدة البيانات")

if __name__ == "__main__":
    main()
