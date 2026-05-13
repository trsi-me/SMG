-- SMG Plant Recognition Database Schema (SQLite)
-- قاعدة بيانات نظام التعرف على النباتات SMG

-- جدول المستخدمين
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_email ON users(email);

-- جدول أنواع النباتات
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL,
    common_name_ar TEXT NOT NULL,
    common_name_en TEXT NOT NULL,
    watering_days_default INTEGER DEFAULT 7,
    sunlight_requirements TEXT DEFAULT 'medium' CHECK(sunlight_requirements IN ('low', 'medium', 'high')),
    temp_min REAL DEFAULT 15.0,
    temp_max REAL DEFAULT 30.0,
    care_text_ar TEXT,
    care_text_en TEXT,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scientific_name ON species(scientific_name);
CREATE INDEX IF NOT EXISTS idx_common_name_ar ON species(common_name_ar);

-- جدول قياسات الحساسات
CREATE TABLE IF NOT EXISTS sensor_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    soil_raw INTEGER NOT NULL,
    soil_percent REAL,
    temperature_c REAL NOT NULL,
    humidity_percent REAL NOT NULL,
    battery REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_id ON sensor_snapshots(device_id);
CREATE INDEX IF NOT EXISTS idx_created_at_sensor ON sensor_snapshots(created_at);

-- جدول عمليات المسح
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    species_id INTEGER,
    image_path TEXT NOT NULL,
    prediction_json TEXT,
    confidence REAL,
    plant_health_status TEXT DEFAULT 'unknown' CHECK(plant_health_status IN ('healthy', 'sick', 'dry', 'overwatered', 'pest_damage', 'nutrient_deficiency', 'unknown')),
    health_confidence REAL,
    health_details TEXT,
    sensor_snapshot_id INTEGER,
    latitude REAL,
    longitude REAL,
    weather_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (species_id) REFERENCES species(id) ON DELETE SET NULL,
    FOREIGN KEY (sensor_snapshot_id) REFERENCES sensor_snapshots(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_species_id ON scans(species_id);
CREATE INDEX IF NOT EXISTS idx_health_status ON scans(plant_health_status);
CREATE INDEX IF NOT EXISTS idx_created_at_scan ON scans(created_at);

-- جدول التغذية الراجعة
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    is_correct INTEGER NOT NULL DEFAULT 0,
    correct_species_id INTEGER,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    FOREIGN KEY (correct_species_id) REFERENCES species(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_scan_id ON feedbacks(scan_id);

-- جدول إصدارات النماذج
CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_tag TEXT NOT NULL,
    architecture TEXT NOT NULL,
    train_date TIMESTAMP NOT NULL,
    metrics_json TEXT,
    model_path TEXT,
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_version_tag ON model_versions(version_tag);
CREATE INDEX IF NOT EXISTS idx_is_active ON model_versions(is_active);

-- جدول مهام التدريب
CREATE TABLE IF NOT EXISTS training_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    params_json TEXT,
    metrics_json TEXT,
    logs_path TEXT,
    status TEXT DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_status ON training_jobs(status);
CREATE INDEX IF NOT EXISTS idx_started_at ON training_jobs(started_at);

-- جدول إعدادات الأجهزة
CREATE TABLE IF NOT EXISTS device_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    device_name TEXT,
    soil_raw_dry INTEGER DEFAULT 200,
    soil_raw_wet INTEGER DEFAULT 800,
    calibration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_id_settings ON device_settings(device_id);

-- جدول صور التدريب
CREATE TABLE IF NOT EXISTS training_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT NOT NULL,
    health_category TEXT NOT NULL CHECK(health_category IN ('healthy', 'sick', 'dry', 'overwatered', 'pest_damage', 'nutrient_deficiency')),
    dataset_type TEXT NOT NULL CHECK(dataset_type IN ('train', 'val')),
    file_size INTEGER,
    image_width INTEGER,
    image_height INTEGER,
    file_hash TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_health_category ON training_images(health_category);
CREATE INDEX IF NOT EXISTS idx_dataset_type ON training_images(dataset_type);
CREATE INDEX IF NOT EXISTS idx_file_hash ON training_images(file_hash);
CREATE INDEX IF NOT EXISTS idx_is_active ON training_images(is_active);

-- إدراج بيانات تجريبية لأنواع النباتات الشائعة
INSERT OR IGNORE INTO species (scientific_name, common_name_ar, common_name_en, watering_days_default, sunlight_requirements, temp_min, temp_max, care_text_ar, care_text_en) VALUES
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
INSERT OR IGNORE INTO users (username, name, email, password, full_name) VALUES 
('testuser', 'مستخدم تجريبي', 'test@smg.com', 'test123', 'مستخدم تجريبي');

-- إدراج إصدار نموذج افتراضي
INSERT OR IGNORE INTO model_versions (version_tag, architecture, train_date, metrics_json, model_path, is_active) VALUES 
('v1.0.0', 'EfficientNet-B4', datetime('now'), '{"accuracy": 0.85, "top3_accuracy": 0.95}', '/models/efficientnet_b4_v1.pt', 1);

-- إنشاء إعدادات جهاز تجريبي
INSERT OR IGNORE INTO device_settings (device_id, device_name, soil_raw_dry, soil_raw_wet) VALUES 
('esp32-001', 'جهاز الحساس التجريبي', 200, 800);

