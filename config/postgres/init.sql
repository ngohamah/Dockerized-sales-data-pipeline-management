-- Executed once, automatically, on the Postgres container's first boot
-- (mounted into /docker-entrypoint-initdb.d/). Creates the two logical
-- databases used by this platform on a single Postgres instance:
--   airflow  -> Airflow's own metadata database
--   app_data -> cleaned pipeline output, queried by Metabase
CREATE DATABASE airflow;
CREATE DATABASE app_data;
