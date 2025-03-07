-- Script to recreate tables with auto-increment IDs
USE wrag;

-- Drop existing tables in the correct order
DROP TABLE IF EXISTS wrag_documents;
DROP TABLE IF EXISTS source_documents;

-- Table to store original documents and metadata
CREATE TABLE IF NOT EXISTS source_documents (
    pk_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    file_path VARCHAR(768),
    content_length BIGINT,
    ctime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    UNIQUE KEY(file_path)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Table to store Document class objects
CREATE TABLE IF NOT EXISTS wrag_documents (
    pk_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    id VARCHAR(255) UNIQUE,
    file_path VARCHAR(768) NOT NULL,
    page_number INT,
    split_idx_start INT,
    split_id VARCHAR(255),
    metadata JSON,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(file_path),
    FOREIGN KEY (file_path) REFERENCES source_documents(file_path) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Verify tables were created
SHOW TABLES;
DESCRIBE source_documents;
DESCRIBE wrag_documents; 