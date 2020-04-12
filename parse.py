#!/usr/bin/env python


import functools as ft
import argparse
import examples as ex
import sqlparse as sp
from sqlparse.tokens import Whitespace, Newline, Keyword, Name, Punctuation
from sqlparse.sql import TokenList, Comment
from glob import glob


def flatten(lss):
    ft.reduce(lambda x, y: x+y, list(lss))


def is_neligible(token):
    # print("===", token.value, token.ttype is Whitespace, token.ttype is Newline)
    return (token.ttype is Whitespace) or (token.ttype is Newline) or (token.ttype is None and isinstance(token, Comment))


def myprint(x, d):
    print(" " * 3 * d + str(x))


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


class NotComsumedTokenRemains(ParseError):
    pass


def select(tokens):
    token = tokens[0]
    if token.ttype is Keyword.DML and token.value.upper() == "SELECT":
        return 1
    else:
        raise UnexpectedToken("SELECT", token.value, tokens)


def name(tokens):
    token = tokens[0]
    if token.ttype is not Name:
        raise UnexpectedToken("<Name>", token.value, tokens)
    return 1


def column_select(tokens):
    ret = name(tokens)
    nx = tokens[ret]
    if nx.ttype is Punctuation and nx.value == ".":
        ret += 1
        ret += name(tokens[ret:])
    return ret


def column_list(tokens):
    ret = column_select(tokens)
    nx = tokens[ret]
    if nx.ttype is Punctuation and nx.value == ",":
        ret += 1
        ret += column_list(tokens[ret:])
    return ret


def anything_but_from(tokens):
    ret = 0
    nx = tokens[ret]
    while not (nx.ttype is Keyword and nx.value.upper() == "FROM"):
        ret += 1
        nx = tokens[ret]
    return ret


def from_(tokens):
    token = tokens[0]
    if token.ttype is Keyword and token.value.upper() == "FROM":
        return 1
    else:
        raise UnexpectedToken("FROM", token.value, tokens)


def table_name(tokens):
    return name(tokens)


def semicolon(tokens):
    token = tokens[0]
    if token.ttype is Punctuation and token.value == ";":
        return 1
    else:
        raise UnexpectedToken(";", token.value, tokens)


def term(val, ttype):
    def ret(tokens):
        token = tokens[0]
        if token.ttype is ttype and token.value.upper() == val.upper():
            return 1
        else:
            raise UnexpectedToken(val.upper(), token.value, tokens)
    return ret


create_term = term("CREATE", Keyword)
or_term = term("OR", Keyword)
replace_term = term("REPLACE", Keyword)
table_term = term("TABLE", Keyword)
as_term = term("AS", Keyword)
open_paren = term("(", Punctuation)
close_paren = term(")", Punctuation)
select_term = term("SELECT", Keyword)


def table_name(tokens, ls):
    token = tokens[0]
    if token.ttype is Name:
        ls.append(token.value().replace("`", ""))
        return 1
    else:
        raise UnexpectedToken("TABLE NAME", token.value, tokens)


def create_sentence(tokens, targets, sources):
    pos = 0
    pos += create_term(tokens)
    if tokens[pos].value.upper() == "OR":
        pos += or_term(tokens[pos:])
        pos += replace_term(tokens[pos:])
    pos += table_term(tokens[pos:], targets)
    pos += as_term(tokens[pos:])
    gather_sources(tokens, sources)
    return targets, sources


def gather_sources(tokens, sources):
    for t in tokens:
        m = re.match("`(.+)`", t.value())
        if m:
            sources.append(m[1])


def analyze_statement(st):
    tokens = [t for t in extarct(st)]
    sources, targets = [], []
    if tokens[0].value.upper() == "CREATE":
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


def main(args):
    fnames = glob("*.sql")
    targets = []
    sources = []
    for fname in fnames:
        with open(fname) as f:
            sql = "\n".join(f.readlines())
        t, s = parse(sql)
        targets += t
        sources += s
    create_makefile(targets, sources)


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
