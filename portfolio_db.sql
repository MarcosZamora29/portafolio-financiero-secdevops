-- =====================================================
-- BASE DE DATOS: PORTAFOLIO FINANCIERO
-- =====================================================

CREATE DATABASE IF NOT EXISTS portafolio_financiero
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE portafolio_financiero;

-- ---------------------------------------------------
-- TABLA: usuarios
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    rol VARCHAR(20) NOT NULL DEFAULT 'user',
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'user',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- ---------------------------------------------------
-- TABLA: activos  (catálogo de instrumentos)
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS activos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    tipo ENUM('accion','etf','cripto','bono','divisa','materia_prima') NOT NULL,
    sector VARCHAR(100),
    moneda VARCHAR(10) DEFAULT 'USD',
    descripcion TEXT
) ENGINE=InnoDB;

-- ---------------------------------------------------
-- TABLA: portafolios
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS portafolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    moneda_base VARCHAR(10) DEFAULT 'USD',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------
-- TABLA: transacciones
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS transacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    portafolio_id INT NOT NULL,
    activo_id INT NOT NULL,
    tipo ENUM('compra','venta','dividendo','split') NOT NULL,
    cantidad DECIMAL(18,6) NOT NULL,
    precio_unitario DECIMAL(18,6) NOT NULL,
    comision DECIMAL(18,6) DEFAULT 0,
    fecha DATETIME NOT NULL,
    notas TEXT,
    FOREIGN KEY (portafolio_id) REFERENCES portafolios(id) ON DELETE CASCADE,
    FOREIGN KEY (activo_id) REFERENCES activos(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------
-- TABLA: precios_historicos
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS precios_historicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activo_id INT NOT NULL,
    fecha DATE NOT NULL,
    precio_cierre DECIMAL(18,6) NOT NULL,
    volumen BIGINT,
    UNIQUE KEY uq_activo_fecha (activo_id, fecha),
    FOREIGN KEY (activo_id) REFERENCES activos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------
-- TABLA: alertas
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    activo_id INT NOT NULL,
    tipo ENUM('precio_mayor','precio_menor','variacion_porcentaje') NOT NULL,
    valor_referencia DECIMAL(18,6) NOT NULL,
    activa TINYINT(1) DEFAULT 1,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (activo_id) REFERENCES activos(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------
-- DATOS DE EJEMPLO
-- ---------------------------------------------------

-- Usuario demo (password: demo1234 — hash bcrypt)
INSERT INTO usuarios (nombre, email, password_hash) VALUES
('Usuario Demo', 'demo@portafolio.com',
 '$2b$12$KIXg3VyQ8z0rQ2v1Hk5yFOGQh5OPEyblAJvqkJSnXO7xLwkUj1vQu');

-- Activos de ejemplo
INSERT INTO activos (ticker, nombre, tipo, sector, moneda) VALUES
('AAPL',  'Apple Inc.',              'accion',       'Tecnología',      'USD'),
('MSFT',  'Microsoft Corporation',   'accion',       'Tecnología',      'USD'),
('GOOGL', 'Alphabet Inc.',           'accion',       'Tecnología',      'USD'),
('AMZN',  'Amazon.com Inc.',         'accion',       'Comercio',        'USD'),
('TSLA',  'Tesla Inc.',              'accion',       'Automotriz',      'USD'),
('SPY',   'SPDR S&P 500 ETF',        'etf',          'Diversificado',   'USD'),
('BTC',   'Bitcoin',                 'cripto',       'Cripto',          'USD'),
('ETH',   'Ethereum',                'cripto',       'Cripto',          'USD'),
('GLD',   'SPDR Gold Shares',        'materia_prima','Metales',         'USD'),
('TLT',   'iShares 20+ Year Treasury','bono',        'Renta Fija',      'USD');

-- Portafolio de ejemplo
INSERT INTO portafolios (usuario_id, nombre, descripcion, moneda_base) VALUES
(1, 'Mi Portafolio Principal', 'Portafolio diversificado de largo plazo', 'USD');

-- Transacciones de ejemplo
INSERT INTO transacciones (portafolio_id, activo_id, tipo, cantidad, precio_unitario, comision, fecha) VALUES
(1, 1, 'compra', 10,  150.00, 1.00, '2024-01-15 10:00:00'),
(1, 2, 'compra', 5,   310.00, 1.00, '2024-01-20 11:30:00'),
(1, 3, 'compra', 3,   140.00, 1.00, '2024-02-01 09:00:00'),
(1, 7, 'compra', 0.5, 42000.00, 5.00, '2024-03-10 14:00:00'),
(1, 6, 'compra', 20,  470.00, 2.00, '2024-04-05 10:00:00'),
(1, 1, 'venta',  2,   185.00, 1.00, '2024-06-01 15:00:00');

-- Precios históricos de ejemplo
INSERT INTO precios_historicos (activo_id, fecha, precio_cierre) VALUES
(1, '2024-12-01', 195.00),(1, '2024-12-15', 198.50),(1, '2025-01-01', 202.00),
(2, '2024-12-01', 415.00),(2, '2024-12-15', 420.00),(2, '2025-01-01', 425.00),
(7, '2024-12-01', 95000.00),(7, '2024-12-15', 98000.00),(7, '2025-01-01', 102000.00);
