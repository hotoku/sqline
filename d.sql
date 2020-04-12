#standardSQL

create or replace table `p.d.d` as
with temp1 as (
  select * from `p.d.a`
)
select * from temp1
