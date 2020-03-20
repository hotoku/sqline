-- simpleなケース
select
  a,
  b,
  c
from
  `proj.ds.table`
where
  x=y and
  c=d
;

-- join するケース
select
  a,
  b,
  c
from
  `proj.ds.table` l left join
  `proj.ds.table2` r
where
  x=y and
  c=d
;

-- withを使うケース
with temp1 as (
select
  a
from
  `proj.ads.table`
)

select
  *
from
  (temp1 l cross join `proj.ds.table3`)
  using(x)
;

-- 副問い合わせがあるケース
select
  x
from (
  select x from `proj.ds.table4`
)
;


-- 副問い合わせがあるケース2
select
  x
from
  `proj.ds.table5` o
where
  exists (
    select a from `proj.ds.table6` i
    where i.x = o.x
  )
;

-- ,でjoinするケース
select
  *
from
  `proj.ds.table6`, `proj.ds.table7`
