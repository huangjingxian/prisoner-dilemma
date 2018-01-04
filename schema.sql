drop table if exists scores;
create table scores (
  id integer primary key autoincrement,
  idx integer not null,	--session number
  oppo_type text not null,
  room_num integer not null,
  name1 integer not null,
  oper1 integer not null,
  delta1 integer not null,
  tot1 integer not null,
  name2 integer not null,
  oper2 integer not null,
  delta2 integer not null,
  tot2 integer not null,
  ifNo1 integer not null
);