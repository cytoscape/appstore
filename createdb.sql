CREATE USER 'appstoreuser'@'localhost' IDENTIFIED BY '@@PASSWORD@@';
CREATE USER 'appstoreuser'@'127.0.0.1' IDENTIFIED BY '@@PASSWORD@@';
GRANT ALL PRIVILEGES ON AppStore.* to 'appstoreuser'@'localhost';
GRANT ALL PRIVILEGES ON AppStore.* to 'appstoreuser'@'127.0.0.1';
GRANT ALL PRIVILEGES ON test_AppStore.* to 'appstoreuser'@'localhost';
GRANT ALL PRIVILEGES ON test_AppStore.* to 'appstoreuser'@'127.0.0.1';

FLUSH PRIVILEGES;
