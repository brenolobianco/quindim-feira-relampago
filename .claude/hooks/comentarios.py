import re
import sys
import tokenize

PERMITIDO = re.compile(r"#!|#\s*(noqa|type:\s*ignore)\b")

with tokenize.open(sys.argv[1]) as arquivo:
    for token in tokenize.generate_tokens(arquivo.readline):
        if token.type == tokenize.COMMENT and not PERMITIDO.match(token.string):
            print(f"linha {token.start[0]}: {token.string}")
