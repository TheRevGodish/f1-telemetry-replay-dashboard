CREATE TABLE IF NOT EXISTS car_data (
    session_key    INTEGER     NOT NULL,
    driver_number  INTEGER     NOT NULL,
    date           TIMESTAMPTZ NOT NULL,   -- timestamp OpenF1 (ISO 8601 + timezone)
    speed          INTEGER,
    throttle       INTEGER,
    brake          INTEGER,
    rpm            INTEGER,
    n_gear         INTEGER,
    drs            INTEGER,
    PRIMARY KEY (session_key, driver_number, date)
);

CREATE TABLE IF NOT EXISTS location (
    session_key    INTEGER     NOT NULL,
    driver_number  INTEGER     NOT NULL,
    date           TIMESTAMPTZ NOT NULL,
    x              INTEGER,
    y              INTEGER,
    z              INTEGER,
    PRIMARY KEY (session_key, driver_number, date)
);