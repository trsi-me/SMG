"""
سكربت إضافة صور التدريب إلى قاعدة البيانات
Script to add training images to database
"""
import sqlite3
import os
import hashlib
from pathlib import Path
from PIL import Image
from datetime import datetime
import argparse
import json

class TrainingImageManager:
    
    def __init__(self, db_path: str, data_dir: str):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.connection = None
        
        # فئات الصحة المدعومة
        self.health_categories = [
            'healthy', 'sick', 'dry', 'overwatered', 
            'pest_damage', 'nutrient_deficiency'
        ]
        
        # أنواع البيانات
        self.dataset_types = ['train', 'val']
    
    def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            print(f"✅ تم الاتصال بقاعدة البيانات: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
            return False
    
    def disconnect(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()
            print("✅ تم إغلاق الاتصال بقاعدة البيانات")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """حساب hash للملف لتجنب التكرار"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_image_info(self, image_path: Path) -> dict:
        """الحصول على معلومات الصورة"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = image_path.stat().st_size
                return {
                    'width': width,
                    'height': height,
                    'file_size': file_size
                }
        except Exception as e:
            print(f"⚠️ خطأ في قراءة الصورة {image_path}: {e}")
            return {
                'width': None,
                'height': None,
                'file_size': image_path.stat().st_size if image_path.exists() else 0
            }
    
    def image_exists(self, file_hash: str) -> bool:
        """التحقق من وجود الصورة في قاعدة البيانات"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM training_images WHERE file_hash = ?", (file_hash,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def add_image(self, image_path: Path, health_category: str, dataset_type: str, 
                  relative_path: str = None) -> bool:
        """إضافة صورة إلى قاعدة البيانات"""
        try:
            # حساب hash للملف
            file_hash = self.calculate_file_hash(image_path)
            
            # التحقق من وجود الصورة
            if self.image_exists(file_hash):
                print(f"⏭️ الصورة موجودة مسبقاً: {image_path.name}")
                return False
            
            # الحصول على معلومات الصورة
            image_info = self.get_image_info(image_path)
            
            # استخدام المسار النسبي إذا تم توفيره
            if relative_path:
                db_path = relative_path
            else:
                # حساب المسار النسبي من مجلد البيانات
                try:
                    db_path = str(image_path.relative_to(self.data_dir))
                except ValueError:
                    db_path = str(image_path)
            
            # إدراج الصورة في قاعدة البيانات
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO training_images 
                (image_path, health_category, dataset_type, file_size, 
                 image_width, image_height, file_hash, added_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                db_path,
                health_category,
                dataset_type,
                image_info['file_size'],
                image_info['width'],
                image_info['height'],
                file_hash,
                datetime.now(),
                1
            ))
            self.connection.commit()
            cursor.close()
            
            print(f"✅ تمت إضافة الصورة: {image_path.name} ({health_category}/{dataset_type})")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إضافة الصورة {image_path}: {e}")
            return False
    
    def scan_and_add_images(self, dataset_type: str = 'train', 
                           update_existing: bool = False) -> dict:
        """فحص مجلد التدريب وإضافة الصور الجديدة"""
        stats = {
            'total_found': 0,
            'added': 0,
            'skipped': 0,
            'errors': 0,
            'by_category': {}
        }
        
        dataset_dir = self.data_dir / dataset_type
        
        if not dataset_dir.exists():
            print(f"❌ المجلد غير موجود: {dataset_dir}")
            return stats
        
        print(f"\n🔍 فحص مجلد: {dataset_dir}")
        print("=" * 60)
        
        # فحص كل فئة صحة
        for category in self.health_categories:
            category_dir = dataset_dir / category
            
            if not category_dir.exists():
                print(f"⚠️ مجلد الفئة غير موجود: {category_dir}")
                continue
            
            stats['by_category'][category] = {
                'found': 0,
                'added': 0,
                'skipped': 0
            }
            
            print(f"\n📁 فحص فئة: {category}")
            
            # البحث عن جميع الصور
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
            images = []
            for ext in image_extensions:
                images.extend(category_dir.glob(f'*{ext}'))
                images.extend(category_dir.glob(f'*{ext.upper()}'))
            
            stats['by_category'][category]['found'] = len(images)
            stats['total_found'] += len(images)
            
            print(f"   📸 عدد الصور الموجودة: {len(images)}")
            
            # إضافة كل صورة
            for image_path in images:
                relative_path = f"{dataset_type}/{category}/{image_path.name}"
                
                if self.add_image(image_path, category, dataset_type, relative_path):
                    stats['added'] += 1
                    stats['by_category'][category]['added'] += 1
                else:
                    stats['skipped'] += 1
                    stats['by_category'][category]['skipped'] += 1
        
        return stats
    
    def get_statistics(self) -> dict:
        """الحصول على إحصائيات قاعدة البيانات"""
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
    
    def print_statistics(self):
        """طباعة إحصائيات قاعدة البيانات"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("📊 إحصائيات قاعدة البيانات")
        print("=" * 60)
        print(f"إجمالي الصور: {stats['total']}")
        print("\n📁 حسب الفئة:")
        for category, count in stats['by_category'].items():
            print(f"   - {category}: {count} صورة")
        print("\n📂 حسب نوع البيانات:")
        for dataset_type, count in stats['by_dataset'].items():
            print(f"   - {dataset_type}: {count} صورة")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='إضافة صور التدريب إلى قاعدة البيانات',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:
  # إضافة صور التدريب
  python add_training_images_to_db.py --data-dir data/health --dataset-type train
  
  # إضافة صور التحقق
  python add_training_images_to_db.py --data-dir data/health --dataset-type val
  
  # عرض الإحصائيات فقط
  python add_training_images_to_db.py --data-dir data/health --stats-only
        """
    )
    
    parser.add_argument('--data-dir', type=str, 
                       default='data/health',
                       help='مسار مجلد بيانات التدريب')
    parser.add_argument('--db-path', type=str, 
                       default=None,
                       help='مسار قاعدة البيانات (افتراضي: data/smg_plants.db)')
    parser.add_argument('--dataset-type', type=str, 
                       choices=['train', 'val', 'both'],
                       default='both',
                       help='نوع البيانات المراد إضافتها')
    parser.add_argument('--stats-only', action='store_true',
                       help='عرض الإحصائيات فقط بدون إضافة صور')
    
    args = parser.parse_args()
    
    # تحديد مسار قاعدة البيانات
    if args.db_path:
        db_path = args.db_path
    else:
        # المسار الافتراضي
        base_dir = Path(__file__).parent.parent
        db_dir = base_dir / "data"
        db_dir.mkdir(exist_ok=True)
        db_path = str(db_dir / "smg_plants.db")
    
    # إنشاء المدير
    manager = TrainingImageManager(db_path, args.data_dir)
    
    if not manager.connect():
        return
    
    try:
        if args.stats_only:
            # عرض الإحصائيات فقط
            manager.print_statistics()
        else:
            # إضافة الصور
            if args.dataset_type in ['train', 'both']:
                print("\n" + "=" * 60)
                print("🚀 بدء إضافة صور التدريب")
                print("=" * 60)
                train_stats = manager.scan_and_add_images('train')
                
                print("\n📊 نتائج إضافة صور التدريب:")
                print(f"   - إجمالي الصور: {train_stats['total_found']}")
                print(f"   - تمت الإضافة: {train_stats['added']}")
                print(f"   - تم التخطي: {train_stats['skipped']}")
            
            if args.dataset_type in ['val', 'both']:
                print("\n" + "=" * 60)
                print("🚀 بدء إضافة صور التحقق")
                print("=" * 60)
                val_stats = manager.scan_and_add_images('val')
                
                print("\n📊 نتائج إضافة صور التحقق:")
                print(f"   - إجمالي الصور: {val_stats['total_found']}")
                print(f"   - تمت الإضافة: {val_stats['added']}")
                print(f"   - تم التخطي: {val_stats['skipped']}")
            
            # عرض الإحصائيات النهائية
            manager.print_statistics()
            
    finally:
        manager.disconnect()


if __name__ == "__main__":
    main()
