-- Script to clear data from tables without dropping them
USE wrag;

-- Disable foreign key checks temporarily to allow truncating tables with foreign key relationships
SET FOREIGN_KEY_CHECKS = 0;

-- Clear all data from tables
TRUNCATE TABLE wrag_documents;
TRUNCATE TABLE source_documents;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify tables are empty
SELECT 'source_documents count:', COUNT(*) FROM source_documents;
SELECT 'wrag_documents count:', COUNT(*) FROM wrag_documents; 