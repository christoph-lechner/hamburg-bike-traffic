# Installation Instructions
C. Lechner, 2026-03-11

## System Accounts
We create two system accounts. User `bikedata` is the owner of all JSON dumps written by the data ingestion script. These JSON files allow to recreate the database at a later time should the need arise (for instance because additional fields are required).
```
cl@clsrv:/$ sudo useradd -m -c "user for bike proj" -s /bin/bash bikeproj
cl@clsrv:/$ sudo useradd -m -c "user for bike proj" -s /bin/bash bikedata
```

After creating the system accounts, we create the data directory and adjust the permissions:
```
cl@clsrv:/$ sudo mkdir /srv/bikedata/
cl@clsrv:/$ sudo chown bikedata:bikedata /srv/bikedata/
cl@clsrv:/$ sudo chmod 750 /srv/bikedata/
cl@clsrv:/$ sudo ls -ld /srv/bikedata/
drwxr-x--- 2 bikedata bikedata 4096 Mar 11 19:30 /srv/bikedata/
```

## Preparation of PostgreSQL DB
This section assumes that you already have a running postgreSQL installation and that the admin user is `postgres`.

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

## Preparation of Software
The goal is to deploy a copy of the software for regular API requests and loading of obtained data into the DB, i.e. "production use".

### Python "virtual environment".
It is good practice to set up a virtual environment for the Python scripts. This "decouples" the installed packages from other software installed on the same machine.
To create the Python virtual environment, I used: (Note: This assumes that the Python package providing `venv` is already installed. If needed, this is provided by a package of your Linux distribution, for instance python3-venv on Debian-based distributions.)
```
cl@clsrv:/$ sudo -i
[sudo] password for cl: 
root@clsrv:~# su - bikedata
bikedata@clsrv:~$ mkdir prod_bikeloader
bikedata@clsrv:~$ cd prod_bikeloader/
bikedata@clsrv:~/prod_bikeloader$ python3 -m venv venv_prod
bikedata@clsrv:~/prod_bikeloader$ source /home/bikedata/prod_bikeloader/venv_prod/bin/activate
(venv_prod) bikedata@clsrv:~/prod_bikeloader$
```

### Preparation of Software
```
(venv_prod) bikedata@clsrv:~/prod_bikeloader$ git clone https://github.com/christoph-lechner/hamburg-bike-traffic.git
[..]
```

```
(venv_prod) bikedata@clsrv:~/prod_bikeloader$ cd hamburg-bike-traffic/
(venv_prod) bikedata@clsrv:~/prod_bikeloader/hamburg-bike-traffic$ pip3 install -r requirements_loaders.txt 
```

### Configuration
In `loader_radverkehr.py`, the value assigned to variable `datadir` needs to reflect the directory set up earlier for data storage. (In future versions, it is planned that this will be configured using a dedicated configuration file.)

The database connection parameters have to be entered in `db_conn.py`.
The corresponding password goes into the file `~/.pgpass` (be sure to set the permissions to 0600, otherwise the file will be ignored).

To verify that the DB connection can be established, a test script can be executed:
```
(venv_prod) bikedata@clsrv:~/prod_bikeloader/hamburg-bike-traffic$ ./check_db_conn.py 
Connecting to DB ...
Success: Connection to DB established
*** Connection Test successful ***
```

### Manual Test of Loader
Before setting up scheduled execution of the ingestion script, we execute it once from the command line to ensure that everything is working. (In particular, should there be any issues with the scheduled execution of the process, the comparison with manual execution from the command line allows to isolate any issues.)
```
(venv_prod) bikedata@clsrv:~/prod_bikeloader/hamburg-bike-traffic$ ./loader_radverkehr.py --ndays=1
```

If there were no error messages, you can have a look into the database to verify that data indeed arrived there:
```
bikedb> SELECT MAX(t_start) FROM bikeproj_zaehlstellen;
+------------------------+
| max                    |
|------------------------|
| 2026-03-11 22:30:00+01 |
+------------------------+
SELECT 1
Time: 0.004s
bikedb>
```
While preparing this text, the youngest timestamp in the data just obtained was about 1 hour old.


## Installation of Scheduled Data Downloads
### Final Test
For this test, we disable the Python virtual environment and go back to the home directory:
```
(venv_prod) bikedata@clsrv:~/prod_bikeloader/hamburg-bike-traffic$ deactivate
bikedata@clsrv:~/prod_bikeloader/hamburg-bike-traffic$ cd
bikedata@clsrv:~$
```

Then we launch the script that will later be executed as cronjob. If this executes correctly, we can be confident that everything is set up correctly for the regular data import. As in the crontab, we run the script with absolute path:
```
bikedata@clsrv:~$ /home/bikedata/prod_bikeloader/hamburg-bike-traffic/run_cron.sh 
[..]
```

### Configuration of Cron Job
Our goal is to run the script once per day in the early morning hours.
To achieve this, we need to configure a so-called cronjob.
We run the command: 
```
bikedata@clsrv:~$ crontab -e
```
The line to be added at the very bottom of the file is:
```
0 4 * * * /usr/bin/flock -n /tmp/bike-transfer-cron.lockfile /home/bikedata/prod_bikeloader/hamburg-bike-traffic/run_cron.sh
```
In the editor, save the file and exit. On the terminal you should now see
```
crontab: installing new crontab
bikedata@clsrv:~$ 
```
The new `crontab` was installed (you can check by running `crontab -l`).

### Check that Cron Job was active
On the next day, inspect the log files and/or the database to verify that the cronjob was indeed completing the task.

### Future Directions
If you are running an installation of Apache Airflow, you might consider setting up a DAG for this process.
