-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS wrag;
USE wrag;

-- Table to store original documents and metadata
CREATE TABLE IF NOT EXISTS source_documents (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT,
    file_path VARCHAR(1024),
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size BIGINT,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON,
    INDEX(file_path(255)),
    INDEX(file_type)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Table to store Document class objects
CREATE TABLE IF NOT EXISTS wrag_documents (
    id VARCHAR(255) PRIMARY KEY,
    source_id VARCHAR(255),
    content TEXT,
    embedding_vector LONGBLOB,  -- To store binary embedding data
    sparse_embedding_indices JSON,
    sparse_embedding_values JSON,
    metadata JSON,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source_documents(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a helper function to convert between Haystack Document objects and DB records
DELIMITER //
CREATE PROCEDURE store_document(
    IN p_id VARCHAR(255),
    IN p_source_id VARCHAR(255),
    IN p_content TEXT,
    IN p_score FLOAT,
    IN p_embedding_vector LONGBLOB,
    IN p_sparse_embedding_indices JSON,
    IN p_sparse_embedding_values JSON,
    IN p_metadata JSON
)
BEGIN
    INSERT INTO wrag_documents (
        id, 
        source_id, 
        content, 
        score, 
        embedding_vector,
        sparse_embedding_indices,
        sparse_embedding_values,
        metadata
    ) 
    VALUES (
        p_id,
        p_source_id,
        p_content,
        p_score,
        p_embedding_vector,
        p_sparse_embedding_indices,
        p_sparse_embedding_values,
        p_metadata
    )
    ON DUPLICATE KEY UPDATE
        source_id = p_source_id,
        content = p_content,
        score = p_score,
        embedding_vector = p_embedding_vector,
        sparse_embedding_indices = p_sparse_embedding_indices,
        sparse_embedding_values = p_sparse_embedding_values,
        metadata = p_metadata,
        last_modified = CURRENT_TIMESTAMP;
END //
DELIMITER ;

-- Create a procedure to store source documents
DELIMITER //
CREATE PROCEDURE store_source_document(
    IN p_id VARCHAR(255),
    IN p_content TEXT,
    IN p_file_path VARCHAR(1024),
    IN p_file_name VARCHAR(255),
    IN p_file_type VARCHAR(50),
    IN p_file_size BIGINT,
    IN p_metadata JSON
)
BEGIN
    INSERT INTO source_documents (
        id,
        content,
        file_path,
        file_name,
        file_type,
        file_size,
        metadata
    )
    VALUES (
        p_id,
        p_content,
        p_file_path,
        p_file_name,
        p_file_type,
        p_file_size,
        p_metadata
    )
    ON DUPLICATE KEY UPDATE
        content = p_content,
        file_path = p_file_path,
        file_name = p_file_name,
        file_type = p_file_type,
        file_size = p_file_size,
        metadata = p_metadata,
        last_modified = CURRENT_TIMESTAMP;
END //
DELIMITER ; 