#!/usr/bin/env python


import functools as ft
import argparse
import examples as ex
import sqlparse as sp
from sqlparse.tokens import Whitespace, Newline
from sqlparse.sql import Token, TokenList, Comment


def flatten(lss):
    ft.reduce(lambda x, y: x+y, list(lss))


def is_neligible(token):
    # print("===", token.value, token.ttype is Whitespace, token.ttype is Newline)
    return (token.ttype is Whitespace) or (token.ttype is Newline) or (token.ttype is None and isinstance(token, Comment))


def myprint(x, d):
    print(" " * 3 * d + str(x))


class TokenSeq:
    class Token:
        def __init__(self, token, depth, is_head):
            self._is_head = is_head
            self.value = token.value
            self.token = token
            self.depth = depth
            self.ttype = token.ttype

    def __init__(self, tokens):
        self._tokens = tokens

    def __str__(self):
        max_len = 0
        for t in self._tokens:
            max_len = max(max_len, len(t.value) + 3 * t.depth)
        ret = []
        for t in self._tokens:
            space_before = " " * t.depth * 3
            space_after = " " * (max_len - len(t.value) -
                                 len(space_before) + 10)
            ret.append(
                f"{space_before}{t.value}{space_after}{t.ttype}")
        return "\n".join(ret)


class TableExtractor:
    def extract(self, tokens, n):
        tokens = [t for t in tokens if not is_neligible(t)]
        is_head = True
        for t in tokens:
            if isinstance(t, TokenList):
                yield from self.extract(t, n+1)
            else:
                yield TokenSeq.Token(t, n, is_head)
                is_head = False


def main():
    with open("1.sql") as f:
        sql = "\n".join(f.readlines())

    tex = TableExtractor()
    for s in sp.parse(sql):
        seq = TokenSeq([t for t in tex.extract(s, 0)])
        print(seq)
        print("==========")


if __name__ == "__main__":
    main()
