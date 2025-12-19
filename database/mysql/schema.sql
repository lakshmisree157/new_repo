-- MySQL schema for pet adoption system
-- Clean, unified schema without conflicts

CREATE DATABASE IF NOT EXISTS dbms_db;
USE dbms_db;

-- ===============================
-- 1. USERS TABLE (Base table for all roles)
-- ===============================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'adopter', 'center') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===============================
-- 2. ADOPTION CENTERS TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS adoption_centers (
    center_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    center_name VARCHAR(100) NOT NULL,
    location VARCHAR(150),
    contact_number VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===============================
-- 3. ADOPTERS TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS adopters (
    adopter_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(100),
    address VARCHAR(255),
    phone_number VARCHAR(15),
    lifestyle ENUM('active', 'moderate', 'quiet'),
    home_environment ENUM('apartment', 'house', 'farm'),
    family_composition ENUM('alone', 'with family', 'with children', 'with other pets'),
    pet_experience ENUM('beginner', 'intermediate', 'expert') DEFAULT 'beginner',

    preferred_pet_age_min INT,
    preferred_pet_age_max INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===============================
-- 4. ADOPTION REQUESTS TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS adoption_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    adopter_id INT NOT NULL,
    center_id INT NOT NULL,
    animal_mongo_id VARCHAR(50) NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approval_date TIMESTAMP NULL,
    FOREIGN KEY (adopter_id) REFERENCES adopters(adopter_id) ON DELETE CASCADE,
    FOREIGN KEY (center_id) REFERENCES adoption_centers(center_id) ON DELETE CASCADE,
    INDEX idx_adopter_id (adopter_id),
    INDEX idx_center_id (center_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===============================
-- 5. POST-ADOPTION TRACKING TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS post_adoption_tracking (
    track_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    followup_date DATE,
    notes TEXT,
    health_status ENUM('good', 'average', 'poor'),
    FOREIGN KEY (request_id) REFERENCES adoption_requests(request_id) ON DELETE CASCADE,
    INDEX idx_request_id (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===============================
-- 6. ADMIN LOGS TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS admin_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action_type VARCHAR(50),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_admin_id (admin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;