-- Tabel lokasi untuk menyimpan koordinat dan alamat detail
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude NUMERIC(10,6) NOT NULL,
    longitude NUMERIC(10,6) NOT NULL,
    detail_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk pencarian berdasarkan koordinat
CREATE INDEX idx_locations_coordinates ON locations(latitude, longitude);

-- Index untuk pencarian berdasarkan nama
CREATE INDEX idx_locations_name ON locations(name);
