# -*- coding: utf-8; -*-

from functools import wraps
from . import languages
import re


(
    TOKEN_EOF,
    TOKEN_NEWLINE,
    TOKEN_TEXT,
    TOKEN_COMMENT,
    TOKEN_META_LABEL,
    TOKEN_META_VALUE,
    TOKEN_LABEL,
) = range(7)


def compiled_languages():
    compiled = {}
    for language, values in languages.LANGUAGES.items():
        compiled[language] = dict((kword, re.compile(regex))
            for (kword, regex) in values.items())
    return compiled


## This should happen just once in the module life time
LANGUAGES = compiled_languages()


class BaseParser(object):

    def __init__(self, stream):
        self.stream = stream
        self.start = 0
        self.position = 0
        self.width = 0

    def next_(self):
        if self.position >= len(self.stream):
            self.width = 0
            return None # EOF
        next_item = self.stream[self.position]
        self.width = 1
        self.position += self.width
        return next_item

    def ignore(self):
        self.start = self.position

    def backup(self):
        self.position -= self.width

    def accept(self, valid):
        if self.next_() in valid:
            return True
        self.backup()
        return False


class Lexer(BaseParser):

    def __init__(self, stream):
        super(Lexer, self).__init__(stream)
        self.tokens = []

    def emit(self, token):
        self.tokens.append((token, self.stream[self.start:self.position]))
        self.start = self.position

    def emit_s(self, token):
        if self.position > self.start:
            self.emit(token)

    def run(self):
        state = self.lex_text
        while state:
            state = state()
        return self.tokens

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
            elif cursor == '#':
                self.backup()
                self.emit_s(TOKEN_TEXT)
                self.next_()
                return self.lex_comment
            elif cursor == '\n':
                self.backup()
                self.emit_s(TOKEN_TEXT)
                self.next_()
                self.emit_s(TOKEN_NEWLINE)
                return self.lex_text
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
                self.emit_s(TOKEN_NEWLINE)
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
            elif cursor == '\n':
                self.backup()
                self.emit_s(TOKEN_META_VALUE)
                return self.lex_text
        self.emit_s(TOKEN_META_VALUE)
        return self.lex_text


class Parser(BaseParser):

    def __init__(self, stream):
        super(Parser, self).__init__(stream)
        self.output = []
        self.encoding = 'utf-8'
        self.language = 'en'
        self.languages = LANGUAGES

    def match_label(self, type_, label):
        return self.languages[self.language][type_].match(label)

    def parse_title(self):
        title = []
        while True:
            item = self.next_()
            if item is None:
                break  # EOF
            token, value = item
            if token == TOKEN_NEWLINE:
                break
            title.append(value)
        return Ast.Text(' '.join(title))

    def parse_description(self):
        description = []
        while True:
            item = self.next_()
            if item is None:
                break  # EOF
            token, value = item
            if token == TOKEN_NEWLINE:
                continue
            elif token == TOKEN_TEXT:
                description.append(value)
            else:
                self.backup()
                break
        return Ast.Text(' '.join(description))

    def parse_background(self):
        token, label = self.next_()
        if not self.match_label('background', label):
            self.backup()
            return None
        return Ast.Background(
            self.parse_title(),
            self.parse_description())

    def parse_steps(self):
        steps = []
        while True:
            item = self.next_()
            if item is None:
                break  # EOF
            token, value = item
            if token == TOKEN_TEXT:
                steps.append(Ast.Step(Ast.Text(value)))
            elif token == TOKEN_NEWLINE:
                self.ignore()
            else:
                self.backup()
                break
        return steps

    def parse_scenarios(self):
        scenarios = []
        while True:
            item = self.next_()
            if item is None:
                break  # EOF
            token, value = item
            if token == TOKEN_EOF:
                break
            if not self.match_label('scenario', value):
                raise SyntaxError(
                    ('`{}\' should not be declared here, '
                     'Scenario expected').format(value))
            scenarios.append(Ast.Scenario(
                title=self.parse_title(),
                steps=self.parse_steps()))
        return scenarios

    def parse_feature(self):
        while self.accept([(TOKEN_NEWLINE, '\n')]):
            self.ignore()
        token, label = self.next_()
        if not self.match_label('feature', label):
            raise SyntaxError(
                'Feature expected in the beginning of the file, '
                'found `{}\' though.'.format(label))
        return Ast.Feature(
            title=self.parse_title(),
            description=self.parse_description(),
            background=self.parse_background(),
            scenarios=self.parse_scenarios())

    def parse_metadata(self):
        item = self.next_()
        if item is None: return
        token, key = item
        assert token == TOKEN_META_LABEL

        item = self.next_()
        if item is None: return
        token, value = item
        if token != TOKEN_META_VALUE:
            raise SyntaxError(
                'No value found for the meta-field `{}\''.format(key))
        return Ast.Metadata(key, value)


class Ast:
    class Node(object):
        def __eq__(self, other):
            if other is not self and hasattr(other, '__dict__'):
                return other.__dict__ == self.__dict__
            return False

    class Metadata(Node):
        def __init__(self, key, value):
            self.key = key
            self.value = value

        def __repr__(self):
            return 'Metadata(key="{}", value="{}")'.format(self.key, self.value)

    class Text(Node):
        def __init__(self, text):
            self.text = text

        def __repr__(self):
            return 'Text("{}")'.format(self.text)

    class Background(Node):
        def __init__(self, title, description=None):
            self.title = title
            self.description = description

        def __repr__(self):
            return 'Background(title={}, description={})'.format(
                self.title, self.description)

    class Feature(Node):
        def __init__(self, title, description=None, background=None, scenarios=None):
            self.title = title
            self.description = description
            self.background = background
            self.scenarios = scenarios or []

        def __repr__(self):
            return 'Feature(title={}, description={}, background={}, scenarios={})'.format(
                self.title, self.description, self.background, self.scenarios)

    class Scenario(Node):
        def __init__(self, title, description=None, steps=None):
            self.title = title
            self.description = description
            self.steps = steps or []

        def __repr__(self):
            return 'Scenario(title={}, description={}, steps={})'.format(
                self.title, self.description, self.steps)

    class Step(Node):
        def __init__(self, title):
            self.title = title

        def __repr__(self):
            return 'Step(title={})'.format(self.title)











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


class OldLexer(object):

    def __init__(self, skip): pass

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
