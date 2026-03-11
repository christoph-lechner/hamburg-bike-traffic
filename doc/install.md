```
cl@clsrv:/$ sudo useradd -m -c "user for bike proj" -s /bin/bash bikeproj
cl@clsrv:/$ sudo useradd -m -c "user for bike proj" -s /bin/bash bikedata
```

```
cl@clsrv:/$ sudo mkdir /srv/bikedata/
cl@clsrv:/$ sudo chown bikedata:bikedata /srv/bikedata/
cl@clsrv:/$ sudo chmod 750 /srv/bikedata/
cl@clsrv:/$ sudo ls -ld /srv/bikedata/
drwxr-x--- 2 bikedata bikedata 4096 Mar 11 19:30 /srv/bikedata/
```

## Preparation of PostgreSQL DB
This section assumes that you already have a running postgreSQL installation and that your admin user is `postgres`.

### User Accounts and Permissions
```
cl@clpc:~/work/fahrrad$ pgcli -h <host_of_postgresql_server> -p <port_of_postgresql_server> -u postgres -d postgres
Password for postgres: 
Using local time zone Europe/Berlin (server uses Etc/UTC)
Use `set time zone <TZ>` to override, or set `use_local_timezone = False` in the config
Server: PostgreSQL 18.0 (Debian 18.0-1.pgdg13+3)
Version: 4.4.0
Home: http://pgcli.com
postgres> CREATE USER bikeproj WITH PASSWORD 'your_password';
CREATE ROLE
Time: 0.011s
postgres> CREATE DATABASE bikedb OWNER bikeproj;
CREATE DATABASE
Time: 0.105s
postgres> CREATE USER bikeproj_ro WITH PASSWORD 'your_ro_password';
CREATE ROLE
Time: 0.009s
postgres> GRANT CONNECT ON DATABASE bikedb TO bikeproj_ro;
GRANT
Time: 0.003s
postgres> \c bikedb
You are now connected to database "bikedb" as user "postgres"
Time: 0.018s
bikedb> GRANT USAGE ON SCHEMA public TO bikeproj_ro;
GRANT
Time: 0.008s
bikedb> GRANT SELECT ON ALL TABLES IN SCHEMA public TO bikeproj_ro;
GRANT
Time: 0.001s
```

Above commands granted SELECT permission to `bikeproj_ro` on all tables that are already existing in database `bikedb`.
What is still missing is adjusting the permissions for tables that will be created in the future. As `bikeproj` will be creating all the tables in the database `bikedb`, the following command must be executed as user `bikeproj` (not as superuser 'postgres'):
```
cl@clpc:~/work/fahrrad$ pgcli -h <host_of_postgresql_server> -p <port_of_postgresql_server> -u bikeproj -d bikedb
Password for bikeproj: 
Using local time zone Europe/Berlin (server uses Etc/UTC)
Use `set time zone <TZ>` to override, or set `use_local_timezone = False` in the config
Server: PostgreSQL 18.0 (Debian 18.0-1.pgdg13+3)
Version: 4.4.0
Home: http://pgcli.com
bikedb> ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO bikeproj_ro;
You're about to run a destructive command.
Do you want to proceed? [y/N]: y
Your call!
ALTER DEFAULT PRIVILEGES
Time: 0.006s
bikedb>
```

### Database Schema
```
bikedb> \i schema.sql
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE TABLE
Time: 0.051s
bikedb>
```


