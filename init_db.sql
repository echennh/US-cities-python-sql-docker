-- Schema & raw ingest
CREATE TABLE IF NOT EXISTS city_population (
    city        VARCHAR(100) NOT NULL,
    state       VARCHAR(100) NOT NULL,
    year        SMALLINT     NOT NULL,
    population  INT          NOT NULL,
    PRIMARY KEY (city, state, year)
);

-- Least-privilege user
CREATE USER 'ro'@'%' IDENTIFIED BY 'ropass';
GRANT SELECT ON geodata.city_population TO 'ro'@'%';
FLUSH PRIVILEGES;
