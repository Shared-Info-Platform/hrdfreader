CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    trip_id varchar(32),
    datum varchar(10),
    fahrtnummer varchar(8),
    verwaltung varchar(8),
    variante varchar(8),
    lw_variante integer,
    attr_variante integer,
    info_variante integer
);

CREATE TABLE stops (
    id SERIAL PRIMARY KEY,
    trip_id varchar(32),
    lw_variante integer,
    sequenznummer integer,
    verkehrsmittel varchar(3),
    liniennummer varchar(8),
    hstnummer varchar(8),
    hstname varchar(50),
    ankunftszeit varchar(5),
    abfahrtszeit varchar(5),
    aussteigeverbot varchar(5),
    einsteigeverbot varchar(5),
    richtungsid char,
    richtung varchar(50),
    fahrtnummer varchar(8),
    verwaltung varchar(8),
    x varchar(2)
);

CREATE TABLE zugarten (
    id SERIAL PRIMARY KEY,
    code varchar(3),
    produktklasse varchar(2),
    tarifgruppe char,
    ausgabesteuerung char,
    gattungsbezeichnung varchar(8),
    zuschlag char,
    flag char,
    gattungsbildernamen varchar(4),
    kategorienummer varchar(3)
);

CREATE TABLE zugart_kategorien (
    id SERIAL PRIMARY KEY,
    code varchar(3),
    sprache varchar(20),
    kategorie text
);

CREATE TABLE zugart_optionen (
    id SERIAL PRIMARY KEY,
    code varchar(3),
    sprache varchar(20),
    option text
);

CREATE TABLE zugart_klassen (
    id SERIAL PRIMARY KEY,
    code varchar(3),
    sprache varchar(20),
    klasse text
);

CREATE TABLE trip_attribute (
    id SERIAL PRIMARY KEY,
    trip_id varchar(32),
    attr_variante integer,
    sequenznummer integer,
    attributscode varchar(2)
);

CREATE TABLE trip_infotexte (
    id SERIAL PRIMARY KEY,
    trip_id varchar(32),
    info_variante integer,
    sequenznummer integer,
    infotextcode varchar(2),
    infotextnummer varchar(7)
);

CREATE TABLE attribute (
    id SERIAL PRIMARY KEY,
    code varchar(2),
    hstzugehoerigkeit char,
    ausgabeprio integer,
    feinsortierung integer,
    attributsklartext text
);

CREATE TABLE infotexte (
    id SERIAL PRIMARY KEY,
    infotextnummer varchar(7),
    infotext text
);