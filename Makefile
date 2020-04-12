.PHONY: all

all: done.b.sql done.c.sql done.a.sql done.d.sql done.e.sql

done.b.sql: 
	cat b.sql | bq query
	touch $@

done.c.sql: done.a.sql done.b.sql
	cat c.sql | bq query
	touch $@

done.a.sql: 
	cat a.sql | bq query
	touch $@

done.d.sql: done.a.sql
	cat d.sql | bq query
	touch $@

done.e.sql: done.d.sql
	cat e.sql | bq query
	touch $@
