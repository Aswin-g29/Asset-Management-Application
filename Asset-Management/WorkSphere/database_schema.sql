CREATE DATABASE IF NOT EXISTS worksphere;
USE worksphere;

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'IT Manager', 'Viewer') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset_master (
    asset_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_name VARCHAR(150) NOT NULL,
    asset_type ENUM('Laptop', 'Desktop', 'Server', 'Furniture', 'Printer', 'Phone', 'Monitor', 'UPS', 'Other') NOT NULL,
    category ENUM('IT', 'Non-IT') NOT NULL,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    qr_code_value VARCHAR(255),
    qr_code_image_url TEXT,
    model VARCHAR(100),
    brand VARCHAR(100),
    specifications TEXT,
    purchase_date DATE,
    purchase_cost DECIMAL(10, 2),
    vendor_name VARCHAR(150),
    invoice_number VARCHAR(100),
    warranty_start_date DATE,
    warranty_expiry INT,
    asset_status ENUM('Available', 'Assigned', 'In Repair', 'Retired', 'Lost') NOT NULL DEFAULT 'Available',
    condition_status ENUM('New', 'Good', 'Damaged') NOT NULL DEFAULT 'New',
    location VARCHAR(150),
    department VARCHAR(150),
    is_retired BOOLEAN NOT NULL DEFAULT FALSE,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    modified_by INT NULL,
    CONSTRAINT fk_asset_created_by FOREIGN KEY (created_by) REFERENCES users(user_id),
    CONSTRAINT fk_asset_modified_by FOREIGN KEY (modified_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS asset_transaction (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT NOT NULL,
    asset_type ENUM('Laptop', 'Desktop', 'Server', 'Furniture', 'Printer', 'Phone', 'Monitor', 'UPS', 'Other') NOT NULL,
    from_employee INT NULL,
    to_assignee INT NOT NULL,
    action_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_type ENUM('New Asset', 'Asset Transfer') NOT NULL,
    remarks TEXT,
    performed_by INT NOT NULL,
    created_by INT NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transaction_asset FOREIGN KEY (asset_id) REFERENCES asset_master(asset_id),
    CONSTRAINT fk_transaction_from_employee FOREIGN KEY (from_employee) REFERENCES users(user_id),
    CONSTRAINT fk_transaction_to_assignee FOREIGN KEY (to_assignee) REFERENCES users(user_id),
    CONSTRAINT fk_transaction_performed_by FOREIGN KEY (performed_by) REFERENCES users(user_id),
    CONSTRAINT fk_transaction_created_by FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT NOT NULL,
    issue_description TEXT NOT NULL,
    issue_type ENUM('Repair', 'Physical Damage', 'Theft', 'Software Issue') NOT NULL,
    warranty_applicable BOOLEAN NOT NULL DEFAULT FALSE,
    maintenance_status ENUM('Open', 'In Progress', 'Closed') NOT NULL DEFAULT 'Open',
    vendor VARCHAR(150),
    resolution_notes TEXT,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_maintenance_asset FOREIGN KEY (asset_id) REFERENCES asset_master(asset_id)
);

CREATE TABLE IF NOT EXISTS asset_category (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alert_asset FOREIGN KEY (asset_id) REFERENCES asset_master(asset_id)
);

INSERT INTO asset_category (category_name, description)
VALUES
    ('Laptop', 'Portable computing devices'),
    ('Monitor', 'Display devices'),
    ('Mouse', 'Input devices'),
    ('Keyboard', 'Typing devices'),
    ('Printer', 'Printing devices'),
    ('Phone', 'Mobile and desk phones'),
    ('UPS', 'Power backup devices'),
    ('Other', 'Miscellaneous assets')
ON DUPLICATE KEY UPDATE description = VALUES(description);

INSERT INTO users (user_name, username, email, password_hash, role, is_active)
VALUES
    ('Admin One', 'admin1', 'admin1@worksphere.local', SHA2('admin1', 256), 'Admin', TRUE),
    ('Admin Two', 'admin2', 'admin2@worksphere.local', SHA2('admin2', 256), 'Admin', TRUE),
    ('Manager One', 'manager1', 'manager1@worksphere.local', SHA2('manager1', 256), 'IT Manager', TRUE),
    ('Manager Two', 'manager2', 'manager2@worksphere.local', SHA2('manager2', 256), 'IT Manager', TRUE),
    ('Manager Three', 'manager3', 'manager3@worksphere.local', SHA2('manager3', 256), 'IT Manager', TRUE),
    ('Viewer One', 'viewer1', 'viewer1@worksphere.local', SHA2('viewer1', 256), 'Viewer', TRUE),
    ('Viewer Two', 'viewer2', 'viewer2@worksphere.local', SHA2('viewer2', 256), 'Viewer', TRUE),
    ('Viewer Three', 'viewer3', 'viewer3@worksphere.local', SHA2('viewer3', 256), 'Viewer', TRUE),
    ('Test User', 'test1', 'test1@worksphere.local', SHA2('test1', 256), 'Viewer', TRUE)
ON DUPLICATE KEY UPDATE
    user_name = VALUES(user_name),
    password_hash = VALUES(password_hash),
    role = VALUES(role),
    is_active = VALUES(is_active);
