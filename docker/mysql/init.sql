CREATE DATABASE IF NOT EXISTS trivault CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS trivault_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON trivault.* TO 'trivault'@'%';
GRANT ALL PRIVILEGES ON trivault_test.* TO 'trivault'@'%';
FLUSH PRIVILEGES;
