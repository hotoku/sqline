select a,b,c from t1;

select t1.a,b,c from t1;

select a,b,c from t1 where a = 1;

select a,b,c from t1 where a = 1 group  by c;

select a,b,c from t1 where a = 1 group  by c order  by d;

select a,b,"c" from t1 where a = 1 group  by c order  by d;

select extract(hour from x) from t1 where a = 1 group  by c order  by d;
