#standardSQL

create or     replace table `p.d.c` as
select * from `p.d.a` l left join `p.d.b`
