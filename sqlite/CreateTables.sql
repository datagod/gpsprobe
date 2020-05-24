-- SQLite 3
.print "--Create LogImport--"


drop table if exists LogImport;

create table LogImport
(
  DateTime     text,
  Lat          real,
  Lon          real,
  Signal       real,
  Channel      integer,
  PktType      integer,
  Device       string,
  MACAddress   string,
  FriendlyName string,
  Vendor       string,
  SSID         string
  );
  
  

.print "--Create GPSLog--"
drop table if exists GPSLog;

create table GPSLog
(
  DateTime     text,
  Lat          real,
  Lon          real,
  Signal       real,
  Channel      integer,
  PktType      integer,
  Device       string,
  MACAddress   string,
  FriendlyName string,
  Vendor       string,
  SSID         string
  );
  
  
create index i_GPSLog_DateTime     on GPSLog(Datetime);
create index i_GPSLog_FriendlyName on GPSLog(FriendlyName);
create index i_GPSLog_MACAddress   on GPSLog(MACAddress);






.print "--Create FriendlyName--"
drop table if exists FriendlyName;

create table FriendlyName
(
  ID           integer primary key,
  MACAddress   string,
  FriendlyName string

  );
  
create index i_FriendlyName_MACAddress on FriendlyName(MACAddress);
