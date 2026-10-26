-- PostgreSQL-only optional geospatial extension; apply with psql after DB bootstrap.
-- Requires an authorized database administrator and PostGIS installation.
CREATE EXTENSION IF NOT EXISTS postgis;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS geom geometry(Point,4326);
CREATE INDEX IF NOT EXISTS ix_reports_geom ON reports USING GIST(geom);
-- When writing locations in a later implementation, update geom using ST_SetSRID(ST_MakePoint(longitude, latitude),4326).
