# -*- coding: utf-8; -*-

from __future__ import unicode_literals
from functools import wraps
import re


(
    TOKEN_EOF,
    TOKEN_TEXT,
    TOKEN_HASH,
    TOKEN_COMMENT,
    TOKEN_META_LABEL,
    TOKEN_META_VALUE,
    TOKEN_LABEL,
) = range(7)


class matcher(object):
    """Decorator for creating new matchers for the lexer analyzer.

    This decorator compiles an RE out of the pattern (and flags) received and
    wrap the actual scan operation with a function that executes the compiled
    RE, calling the actual function if the matching is successful.
    """
    def __init__(self, pattern, flags=0):
        # Yay, this line will get called only once per pattern since the
        # matcher (and thus the assigner functions) are called when python is
        # still reading the decorated methods from the `Lexer` class.
        self.regex = re.compile(pattern, flags=flags)

    def __call__(self, func):

        # Saving the local attribute inside of the closure's namespace so we
        # can use it inside of the decorator
        regex = self.regex

        @wraps(func)
        def decorator(self, chunk):
            # The actuall matcher won't get called unless the pattern can be
            # matched agains the piece of text received from the lexer.
            found = regex.findall(chunk)
            if found:
                return func(self, found[0])

        return decorator


class Lexer(object):

    def __init__(self, stream):

        # settings
        self.language = 'en'
        self.encoding = 'utf-8'

        # control the cursor
        self.stream = stream
        self.start = 0
        self.position = 0
        self.width = 0
        self.tokens = []

    def next_(self):
        if self.position >= len(self.stream):
            self.width = 0
            return None # EOF
        next_char = self.stream[self.position]
        self.width = len(next_char)
        self.position += self.width
        return next_char

    def emit(self, token):
        self.tokens.append((token, self.stream[self.start:self.position]))
        self.start = self.position

    def emit_s(self, token):
        if self.position > self.start:
            self.emit(token)

    def ignore(self):
        self.start = self.position

    def backup(self):
        self.position -= self.width

    def accept(self, valid):
        if self.next_() in valid:
            return True
        self.backup()
        return False

    ## Breaking the lexer down
    def lex_hash(self):
        self.position += 1
        self.emit(TOKEN_HASH)
        return self.lex_comment

    def lex_text(self):
        while self.accept([' ']):
            self.ignore()
        while True:
            cursor = self.next_()
            if cursor is None: # EOF
                break

            elif cursor == ':':
                self.backup()
                self.emit_s(TOKEN_LABEL)
                self.next_()
                self.ignore()
                return self.lex_text

            elif cursor == '\n':
                self.backup()
                self.emit_s(TOKEN_TEXT)
                self.next_()
                self.ignore()
                return self.lex_text

            elif cursor == '#':
                self.backup()
                self.emit_s(TOKEN_TEXT)
                self.next_()
                self.emit(TOKEN_HASH)
                return self.lex_comment

        self.emit_s(TOKEN_TEXT)
        self.emit(TOKEN_EOF)
        return None

    def lex_comment(self):
        while self.accept([' ']):
            self.ignore()
        while True:
            cursor = self.next_()
            if cursor is None: # EOF
                break
            elif cursor == '\n':
                self.ignore()
                return self.lex_text
            elif cursor == ':':
                self.backup()
                self.emit(TOKEN_META_LABEL)
                self.next_()
                self.ignore()
                return self.lex_comment_metadata_value

        self.emit_s(TOKEN_COMMENT)
        return self.lex_text

    def lex_comment_metadata_value(self):
        while self.accept([' ']):
            self.ignore()
        while True:
            cursor = self.next_()
            if cursor is None: # EOF
                break
            if cursor in (' ', '\n'):
                self.backup()
                self.emit_s(TOKEN_META_VALUE)
                return self.lex_comment

        self.emit_s(TOKEN_META_VALUE)
        return self.lex_comment

    def scan(self, data):
        i = 0
        tokens = []

        while i < len(data):
            chunk = data[i:]

            # Expressions to find out wtf is that chunk
            handlers = [
                self.scan_conf,
                self.scan_comment,
                self.scan_step,
                self.scan_examples,
                self.scan_identifier,
                self.scan_tags,
                self.scan_multiline_strings,
                self.scan_text,
                self.cookie_monster,
            ]

            for handler in handlers:
                found = handler(chunk)

                if found:
                    kind, token, size = found

                    # The `scan_indent` handler might not return tokens, but we
                    # still need to skip the newline character found inside of
                    # the same indent level
                    if kind:
                        tokens.append((kind, token))

                    i += size
                    break

        return tokens

    @matcher(r'\A(\n+)')
    def cookie_monster(self, found):
        return ('', found, len(found))

    @matcher(r'\A(\s*\#\s*)(language|encoding)(:\s*)([^\n]+)')
    def scan_conf(self, found):
        return ('metadata', (found[1], found[3]), sum(map(len, found)))

    @matcher(r'\A(\s*\#\s*)([^\n]+)')
    def scan_comment(self, found):
        return ('comment', found[1], sum(map(len, found)))

    @matcher(r'\A(\s*)@([^\s]+)')
    def scan_tags(self, found):
        return ('tag', found[1], sum(map(len, found))+1)

    @matcher(r'\A(\:?\s+\|)([^\n]+)(\|\n)', re.M)
    def scan_examples(self, found):
        return ('row',
                tuple(f.strip() for f in found[1].split('|')),
                sum(map(len, found)))

    @matcher(r'\A([^\:\n]+)(\: *)([^\n\#]*)')
    def scan_identifier(self, found):
        identifier, _, label = found
        return ('identifier',
                (identifier.strip(), label.strip()),
                sum(map(len, found)))

    @matcher(r'\A(\s*)(Given|When|Then|And|But)( *)([^\n\#\:]+)')
    def scan_step(self, found):
        _, name, _, text = found
        return ('step', (name, text), sum(map(len, found)))

    @matcher(r'\A(\:?\s*""")([^"""]+)')
    def scan_multiline_strings(self, found):
        lines = (f.strip() for f in found[1].splitlines() if f.strip())
        return ('text', '\n'.join(lines), sum(map(len, found))+3)

    @matcher(r'\A([^\n\#]+)')
    def scan_text(self, found):
        # Corner case? When there's a comment in the same line we have text we
        # need to strip the text
        return ('text', found.strip(), len(found))
