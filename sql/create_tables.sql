-- SMG Plant Recognition Database Schema
-- قاعدة بيانات نظام التعرف على النباتات SMG

-- إنشاء قاعدة البيانات
CREATE DATABASE IF NOT EXISTS smg_plants CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smg_plants;

-- جدول المستخدمين
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- جدول أنواع النباتات
CREATE TABLE species (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    common_name_ar VARCHAR(255) NOT NULL,
    common_name_en VARCHAR(255) NOT NULL,
    watering_days_default INT DEFAULT 7,
    sunlight_requirements ENUM('low', 'medium', 'high') DEFAULT 'medium',
    temp_min DECIMAL(5,2) DEFAULT 15.0,
    temp_max DECIMAL(5,2) DEFAULT 30.0,
    care_text_ar TEXT,
    care_text_en TEXT,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_scientific_name (scientific_name),
    INDEX idx_common_name_ar (common_name_ar)
);

-- جدول قياسات الحساسات
CREATE TABLE sensor_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    soil_raw INT NOT NULL,
    soil_percent DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN soil_raw < 200 THEN 0
            WHEN soil_raw > 800 THEN 100
            ELSE ((soil_raw - 200) / 6.0)
        END
    ) STORED,
    temperature_c DECIMAL(5,2) NOT NULL,
    humidity_percent DECIMAL(5,2) NOT NULL,
    battery DECIMAL(4,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_timestamp (timestamp)
);

-- جدول عمليات المسح
CREATE TABLE scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    species_id INT,
    image_path VARCHAR(500) NOT NULL,
    prediction_json JSON,
    confidence DECIMAL(5,4),
    plant_health_status ENUM('healthy', 'sick', 'dry', 'overwatered', 'pest_damage', 'nutrient_deficiency', 'unknown') DEFAULT 'unknown',
    health_confidence DECIMAL(5,4),
    health_details JSON,
    sensor_snapshot_id INT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    weather_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (species_id) REFERENCES species(id) ON DELETE SET NULL,
    FOREIGN KEY (sensor_snapshot_id) REFERENCES sensor_snapshots(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_species_id (species_id),
    INDEX idx_health_status (plant_health_status),
    INDEX idx_created_at (created_at)
);

-- جدول التغذية الراجعة
CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_id INT NOT NULL,
    user_correction_species_id INT,
    correct_flag BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    FOREIGN KEY (user_correction_species_id) REFERENCES species(id) ON DELETE SET NULL,
    INDEX idx_scan_id (scan_id)
);

-- جدول إصدارات النماذج
CREATE TABLE model_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version_tag VARCHAR(50) NOT NULL,
    architecture VARCHAR(100) NOT NULL,
    train_date TIMESTAMP NOT NULL,
    metrics_json JSON,
    model_path VARCHAR(500),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_version_tag (version_tag),
    INDEX idx_is_active (is_active)
);

-- جدول مهام التدريب
CREATE TABLE training_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP NULL,
    params_json JSON,
    metrics_json JSON,
    logs_path VARCHAR(500),
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

-- جدول إعدادات الأجهزة
CREATE TABLE device_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    device_name VARCHAR(255),
    soil_raw_dry INT DEFAULT 200,
    soil_raw_wet INT DEFAULT 800,
    calibration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id)
);

-- إدراج بيانات تجريبية لأنواع النباتات الشائعة
INSERT INTO species (scientific_name, common_name_ar, common_name_en, watering_days_default, sunlight_requirements, temp_min, temp_max, care_text_ar, care_text_en) VALUES
('Rosa damascena', 'الورد الجوري', 'Damask Rose', 3, 'high', 15.0, 25.0, 'الورد الجوري يحتاج إلى سقي منتظم كل 3 أيام مع ضوء شمس كامل. تأكد من تصريف التربة جيداً.', 'Damask rose needs regular watering every 3 days with full sunlight. Ensure good soil drainage.'),
('Mentha spicata', 'النعناع', 'Spearmint', 2, 'medium', 10.0, 30.0, 'النعناع ينمو بسرعة ويحتاج سقي متكرر كل يومين. يحب التربة الرطبة والظل الجزئي.', 'Spearmint grows quickly and needs frequent watering every 2 days. Prefers moist soil and partial shade.'),
('Ocimum basilicum', 'الريحان', 'Basil', 2, 'high', 15.0, 30.0, 'الريحان يحتاج ضوء شمس كامل وسقي منتظم. لا تبلل الأوراق مباشرة.', 'Basil needs full sunlight and regular watering. Avoid wetting leaves directly.'),
('Lavandula angustifolia', 'اللافندر', 'Lavender', 7, 'high', 5.0, 25.0, 'اللافندر مقاوم للجفاف ويحتاج سقي قليل. يحب التربة الجافة والضوء الكامل.', 'Lavender is drought-resistant and needs minimal watering. Prefers dry soil and full light.'),
('Rosmarinus officinalis', 'إكليل الجبل', 'Rosemary', 5, 'high', 5.0, 30.0, 'إكليل الجبل مقاوم للجفاف ويحتاج سقي قليل. يحب التربة الجافة والضوء الكامل.', 'Rosemary is drought-resistant and needs minimal watering. Prefers dry soil and full light.'),
('Thymus vulgaris', 'الزعتر', 'Thyme', 5, 'high', 5.0, 25.0, 'الزعتر مقاوم للجفاف ويحتاج سقي قليل. يحب التربة الجافة والضوء الكامل.', 'Thyme is drought-resistant and needs minimal watering. Prefers dry soil and full light.'),
('Petroselinum crispum', 'البقدونس', 'Parsley', 3, 'medium', 10.0, 25.0, 'البقدونس يحتاج سقي منتظم كل 3 أيام مع ضوء متوسط. يحب التربة الرطبة.', 'Parsley needs regular watering every 3 days with medium light. Prefers moist soil.'),
('Coriandrum sativum', 'الكزبرة', 'Cilantro', 2, 'medium', 10.0, 25.0, 'الكزبرة تحتاج سقي متكرر كل يومين مع ضوء متوسط. تحب التربة الرطبة.', 'Cilantro needs frequent watering every 2 days with medium light. Prefers moist soil.'),
('Allium schoenoprasum', 'الثوم المعمر', 'Chives', 4, 'high', 5.0, 25.0, 'الثوم المعمر يحتاج سقي كل 4 أيام مع ضوء كامل. مقاوم للبرد.', 'Chives need watering every 4 days with full light. Cold-resistant.'),
('Salvia officinalis', 'المريمية', 'Sage', 7, 'high', 5.0, 25.0, 'المريمية مقاومة للجفاف وتحتاج سقي قليل. تحب التربة الجافة والضوء الكامل.', 'Sage is drought-resistant and needs minimal watering. Prefers dry soil and full light.');

-- إنشاء مستخدم تجريبي
INSERT INTO users (username, name, email, password, full_name) VALUES 
('testuser', 'مستخدم تجريبي', 'test@smg.com', 'test123', 'مستخدم تجريبي');

-- إدراج إصدار نموذج افتراضي
INSERT INTO model_versions (version_tag, architecture, train_date, metrics_json, model_path, is_active) VALUES 
('v1.0.0', 'EfficientNet-B4', NOW(), '{"accuracy": 0.85, "top3_accuracy": 0.95}', '/models/efficientnet_b4_v1.pt', TRUE);

-- إنشاء إعدادات جهاز تجريبي
INSERT INTO device_settings (device_id, device_name, soil_raw_dry, soil_raw_wet) VALUES 
('esp32-001', 'جهاز الحساس التجريبي', 200, 800);
