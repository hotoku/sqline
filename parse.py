#!/usr/bin/env python


import functools as ft
import argparse
import examples as ex
import sqlparse as sp
from sqlparse.tokens import Whitespace, Newline, Keyword, Name, Punctuation, DDL
from sqlparse.sql import TokenList, Comment
from glob import glob
from io import StringIO
import logging
import re


def flatten(lss):
    return ft.reduce(lambda x, y: x+y, list(lss))


def is_neligible(token):
    return (token.ttype is Whitespace) or \
        (token.ttype is Newline) or \
        (token.ttype is None and isinstance(token, Comment)) or \
        (token.ttype is Name and token.value == "#standardSQL")


def extract(tokens):
    tokens = [t for t in tokens if not is_neligible(t)]
    for t in tokens:
        if isinstance(t, TokenList):
            yield from extract(t)
        else:
            yield t


class ParseError(Exception):
    pass


class UnexpectedToken(ParseError):
    def __init__(self, exp, got, tokens):
        super(UnexpectedToken, self).__init__(
            f"expected {exp} but got {got}:\n{' '.join([t.value for t in tokens])}")


def term(val, ttype):
    def ret(tokens):
        token = tokens[0]
        if token.ttype is ttype and token.value.upper() == val.upper():
            return 1
        else:
            raise UnexpectedToken(val.upper(), token.value, tokens)
    return ret


create_term = term("CREATE", DDL)
table_term = term("TABLE", Keyword)
as_term = term("AS", Keyword)


def create_or_replace_term(tokens):
    token = tokens[0]
    if token.ttype is DDL and re.match(r"CREATE +OR +REPLACE", token.value.upper()):
        return 1
    else:
        raise UnexpectedToken("CREATE OR REPLACE", token.value, tokens)


def table_name(tokens, ls):
    token = tokens[0]
    if token.ttype is Name:
        ls.append(token.value.replace("`", ""))
        return 1
    else:
        raise UnexpectedToken("TABLE NAME", token.value, tokens)


def create_sentence(tokens, targets, sources):
    pos = 0
    if tokens[pos].value.upper() == "CREATE":
        pos += create_term(tokens)
    else:
        pos += create_or_replace_term(tokens)
    pos += table_term(tokens[pos:])
    pos += table_name(tokens[pos:], targets)
    pos += as_term(tokens[pos:])
    gather_sources(tokens[pos:], sources)
    return targets, sources


def gather_sources(tokens, sources):
    for t in tokens:
        m = re.match("`(.+)`", t.value)
        if m:
            sources.append(m[1])


def analyze_statement(st):
    tokens = [t for t in extract(st)]
    sources, targets = [], []
    if len(tokens) == 0:
        return sources, targets
    if re.match("CREATE.*", tokens[0].value.upper()):
        create_sentence(tokens, targets, sources)
    else:
        gather_sources(tokens, sources)
    return targets, sources


def parse(sql):
    targets = []
    sources = []
    statements = sp.parse(sql)
    for s in statements:
        t, s = analyze_statement(s)
        targets += t
        sources += s
    return targets, sources


class Dependency:
    def __init__(self, t, s, f):
        self.targets = t
        self.sources = s
        self.file = f

    def filter(self, targets):
        s = [s for s in self.sources if s in targets]
        return Dependency(self.targets, s, self.file)

    def rule(self, s2f):
        return """{target}: {sources}
\tcat {file} | bq query
\ttouch $@
""".format(target="done." + self.file,
           sources=" ".join(set(["done." + s2f[s] for s in self.sources])),
           file=self.file)


def create_makefile(ds):
    targets = flatten([d.targets for d in ds])
    if len(targets) != len(set(targets)):
        raise RuntimeError(
            f"some targets are defined in multiple files: {targets}")
    ds2 = [d.filter(targets) for d in ds]
    sources = flatten([d.sources for d in ds])

    def search(s):
        for d in ds2:
            if s in d.targets:
                return d.file
    s2f = {
        s: search(s)
        for s in sources
    }

    with open("Makefile", "w") as f:
        f.write(""".PHONY: all

all: {}

""".format(" ".join(["done." + d.file for d in ds2])))
        f.write("\n".join([
            d.rule(s2f) for d in ds2
        ]))


def main(args):
    fnames = glob("*.sql")
    dependencies = []
    for fname in fnames:
        with open(fname) as f:
            sql = "\n".join(f.readlines())
        t, s = parse(sql)
        dependencies.append(Dependency(t, s, fname))
    create_makefile(dependencies)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    logging.basicConfig(
        filename="parse.log",
        level=logging.DEBUG,
        format="[%(levelname)s]%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    main(args)
