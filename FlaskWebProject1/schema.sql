drop table if exists photo;
create table photo (
  id integer primary key autoincrement,
  name string not null,
  store_date DATE not null
);