CREATE DATABASE IF NOT EXISTS relecov_docker;
CREATE DATABASE IF NOT EXISTS iskylims_docker;

GRANT ALL PRIVILEGES ON relecov_docker.* TO 'django'@'%';
GRANT ALL PRIVILEGES ON iskylims_docker.* TO 'django'@'%';
FLUSH PRIVILEGES;
