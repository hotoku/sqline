#!/usr/bin/env python


import functools as ft
import argparse
import examples as ex
import sqlparse as sp
from sqlparse.tokens import Whitespace, Newline, Keyword, Name, Punctuation
from sqlparse.sql import TokenList, Comment


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


def word(val, ttype):
    def ret(tokens):
        token = tokens[0]
        if token.ttype is ttype and token.value.upper() == val.upper():
            return 1
        else:
            raise UnexpectedToken(val.upper(), token.value, tokens)
    return ret


def where(tokens):
    ret = word("where", Keyword)(tokens)
    nx = tokens[ret]
    while nx.ttype is not Keyword and not nx.value == ";" and ret < len(tokens):
        ret += 1
        nx = tokens[ret]
    return ret


def groupby(tokens):
    t = tokens[0]
    if not (t.ttype is Keyword and t.value.upper().replace(" ", "") == "GROUPBY"):
        raise UnexpectedToken("group by", t.value, tokens)
    ret = 1
    ret += column_list(tokens[ret:])
    return ret


def orderby(tokens):
    t = tokens[0]
    if not (t.ttype is Keyword and t.value.upper().replace(" ", "") == "ORDERBY"):
        raise UnexpectedToken("order by", t.value, tokens)
    ret = 1
    ret += column_list(tokens[ret:])
    return ret


def query(tokens):
    pos = 0
    pos += word("select", Keyword.DML)(tokens[pos:])
    pos += anything_but_from(tokens[pos:])
    pos += word("from", Keyword)(tokens[pos:])
    pos += table_name(tokens[pos:])
    nx = tokens[pos]
    if nx.ttype is Keyword and nx.value.upper() == "WHERE":
        pos += where(tokens[pos:])
    nx = tokens[pos]
    if nx.ttype is Keyword and nx.value.upper().replace(" ", "") == "GROUPBY":
        pos += groupby(tokens[pos:])
    nx = tokens[pos]
    if nx.ttype is Keyword and nx.value.upper().replace(" ", "") == "ORDERBY":
        pos += orderby(tokens[pos:])
    return pos


def statement(tokens):
    pos = query(tokens)
    if pos < len(tokens):
        pos += semicolon(tokens[pos:])
    if pos == len(tokens):
        return True
    else:
        raise NotComsumedTokenRemains(
            "parse finished but not consumed terms remain")


def main():
    with open("2.sql") as f:
        sql = "\n".join(f.readlines())

    statements = sp.parse(sql)
    for st in statements:
        if str(st).strip() == "":
            continue
        print(st)
        tokens = [t for t in extract(st)]
        try:
            ret = statement(tokens)
            print("parse succeeded")
        except ParseError as e:
            print(e)


if __name__ == "__main__":
    main()
