CREATE UNIQUE INDEX attribute_code_idx ON public.attribute (code);

CREATE UNIQUE INDEX infotexte_infotextnummer_idx ON public.infotexte (infotextnummer);

CREATE INDEX stops_trip_id_idx ON public.stops (trip_id);

CREATE INDEX stops_liniennummer_idx ON public.stops (liniennummer);

CREATE INDEX stops_hstnummer_idx ON public.stops (hstnummer);

CREATE INDEX stops_richtungsid_idx ON public.stops (richtungsid);

CREATE INDEX trip_attribute_trip_id_idx ON public.trip_attribute (trip_id);

CREATE INDEX trip_attribute_sequenznummer_idx ON public.trip_attribute (sequenznummer);

CREATE INDEX trip_infotexte_trip_id_idx ON public.trip_infotexte (trip_id);

CREATE INDEX trip_infotexte_sequenznummer_idx ON public.trip_infotexte (sequenznummer);

CREATE INDEX trips_trip_id_idx ON public.trips (trip_id);

CREATE INDEX trips_datum_idx ON public.trips (datum);

CREATE INDEX trips_fahrtnummer_idx ON public.trips (fahrtnummer);

CREATE INDEX trips_verwaltung_idx ON public.trips (verwaltung);

CREATE INDEX zugart_kategorien_code_idx ON public.zugart_kategorien (code);

CREATE INDEX zugart_kategorien_sprache_idx ON public.zugart_kategorien (sprache);

CREATE INDEX zugart_kategorien_kategorie_idx ON public.zugart_kategorien (kategorie);

CREATE INDEX zugart_klassen_code_idx ON public.zugart_klassen (code);

CREATE INDEX zugart_klassen_sprache_idx ON public.zugart_klassen (sprache);

CREATE INDEX zugart_klassen_klasse_idx ON public.zugart_klassen (klasse);

CREATE INDEX zugart_optionen_code_idx ON public.zugart_optionen (code);

CREATE INDEX zugart_optionen_sprache_idx ON public.zugart_optionen (sprache);

CREATE INDEX zugart_optionen_option_idx ON public.zugart_optionen (option);

CREATE INDEX zugarten_code_idx ON public.zugarten (code);

CREATE INDEX zugarten_produktklasse_idx ON public.zugarten (produktklasse);

CREATE INDEX zugarten_kategorienummer_idx ON public.zugarten (kategorienummer);