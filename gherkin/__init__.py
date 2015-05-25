# -*- coding: utf-8; -*-

from . import languages
import re


(
    TOKEN_EOF,                  # 0
    TOKEN_NEWLINE,              # 1
    TOKEN_TEXT,                 # 2
    TOKEN_COMMENT,              # 3
    TOKEN_META_LABEL,           # 4
    TOKEN_META_VALUE,           # 5
    TOKEN_LABEL,                # 6
    TOKEN_TABLE_COLUMN,         # 7
    TOKEN_QUOTES,               # 8
    TOKEN_TAG,                  # 9
) = range(10)


def compiled_languages():
    compiled = {}
    for language, values in languages.LANGUAGES.items():
        compiled[language] = dict(
            (keyword, re.compile(regex))
            for (keyword, regex) in values.items())
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

    def backup(self, steps=1):
        self.position -= self.width * steps

    def peek(self):
        value = self.next_()
        self.backup()
        return value

    def accept(self, valid):
        if self.next_() in valid:
            return True
        self.backup()
        return False


class Lexer(BaseParser):

    def __init__(self, stream):
        super(Lexer, self).__init__(stream)
        self.tokens = []

    def emit(self, token, strip=False):
        value = self.stream[self.start:self.position]
        if strip: value = value.strip()
        self.tokens.append((token, value))
        self.start = self.position

    def emit_s(self, token, strip=False):
        if self.position > self.start:
            self.emit(token, strip)

    def run(self):
        state = self.lex_text
        while state:
            state = state()
        return self.tokens

    def eat_whitespaces(self):
        while self.accept([' ', '\t']):
            self.ignore()

    def match_quotes(self, cursor):
        stream_at_cursor = self.stream[self.position:]
        return cursor in ('"', "'") and (
            stream_at_cursor.startswith('""') or
            stream_at_cursor.startswith("''"))

    def lex_field(self):
        self.eat_whitespaces()
        while True:
            cursor = self.next_()
            if cursor is None: # EOF
                break
            elif cursor == '\n':
                self.backup()
                return self.lex_text
            elif cursor == '|':
                self.backup()
                self.emit_s(TOKEN_TABLE_COLUMN, strip=True)
                return self.lex_text
        return self.lex_text

    def lex_comment(self):
        self.eat_whitespaces()
        while True:
            cursor = self.next_()
            if cursor is None: # EOF
                break
            elif cursor == '\n':
                self.backup()
                break
            elif cursor == ':':
                self.backup()
                self.emit(TOKEN_META_LABEL)
                self.next_()
                self.ignore()
                return self.lex_comment_metadata_value
        self.emit_s(TOKEN_COMMENT)
        return self.lex_text

    def lex_comment_metadata_value(self):
        self.eat_whitespaces()
        while True:
            cursor = self.next_()
            if cursor is None or cursor == '\n':
                self.backup()
                self.emit_s(TOKEN_META_VALUE)
                return self.lex_text

    def lex_quotes(self):
        while True:
            cursor = self.next_()
            if self.match_quotes(cursor):
                # Consume all the text inside of the quotes
                self.backup()
                self.emit_s(TOKEN_TEXT)

                # Consume the closing quotes
                for _ in range(3): self.accept(['"', "'"])
                self.emit_s(TOKEN_QUOTES)
                break
        return self.lex_text

    def lex_tag(self):
        while True:
            cursor = self.next_()
            if cursor is None: # EOF
                break
            elif cursor in (' ', '\n'):
                self.backup()
                break
        self.emit_s(TOKEN_TAG)
        return self.lex_text

    def lex_text(self):
        self.eat_whitespaces()
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
            elif cursor == '|':
                self.ignore()
                return self.lex_field
            elif cursor == '@':
                self.ignore()
                return self.lex_tag
            elif cursor == '\n':
                self.backup()
                self.emit_s(TOKEN_TEXT)
                self.next_()
                self.emit_s(TOKEN_NEWLINE)
                return self.lex_text
            elif self.match_quotes(cursor):
                for _ in range(2): self.accept(['"', "'"])
                self.emit_s(TOKEN_QUOTES)
                return self.lex_quotes

        self.emit_s(TOKEN_TEXT)
        self.emit(TOKEN_EOF)
        return None


class Parser(BaseParser):

    def __init__(self, stream):
        super(Parser, self).__init__(stream)
        self.output = []
        self.encoding = 'utf-8'
        self.language = 'en'
        self.languages = LANGUAGES

    def match_label(self, type_, label):
        return self.languages[self.language][type_].match(label)

    def eat_newlines(self):
        while self.accept([(TOKEN_NEWLINE, '\n')]):
            self.ignore()

    def next_(self):
        "Same as BaseParser.next_() but returns (None, None) instead of None on EOF"
        output = super(Parser, self).next_()
        return (None, None) if output is None else output

    def parse_title(self):
        "Parses the stream until token != TOKEN_TEXT than returns Text()"
        title = []
        while True:
            token, value = self.next_()
            if token != TOKEN_TEXT: break
            title.append(value)
        return Ast.Text(' '.join(title))

    def parse_description(self):
        description = []
        while True:
            token, value = self.next_()
            if token == TOKEN_NEWLINE:
                continue
            elif token == TOKEN_TEXT:
                description.append(value)
            else:
                self.backup()
                break
        return Ast.Text(' '.join(description))

    def parse_background(self):
        _, label = self.next_()
        if not self.match_label('background', label):
            self.backup()
            return None
        return Ast.Background(
            self.parse_title(),
            self.parse_steps())

    def parse_step_text(self):
        self.next_(); self.ignore()  # Skip enter QUOTES
        token, step_text = self.next_()
        assert token == TOKEN_TEXT
        token, _ = self.next_()      # Skip exit QUOTES
        assert token == TOKEN_QUOTES
        self.ignore()
        return Ast.Text(step_text)

    def parse_steps(self):
        steps = []
        while True:
            token, value = self.next_()
            if token == TOKEN_LABEL and self.match_label('examples', value):
                # Special case, label `Examples' is not a step. Let's
                # backup here and let parse_scenarios() deal with that
                self.backup()
                return steps

            self.eat_newlines()
            next_token = self.peek()[0]

            if token == TOKEN_NEWLINE:
                self.ignore()
            elif (token in (TOKEN_LABEL, TOKEN_TEXT) and
                  next_token == TOKEN_TABLE_COLUMN):
                steps.append(Ast.Step(
                    title=Ast.Text(value),
                    table=self.parse_table()))
            elif (token in (TOKEN_LABEL, TOKEN_TEXT) and
                  next_token == TOKEN_QUOTES):
                steps.append(Ast.Step(
                    title=Ast.Text(value),
                    text=self.parse_step_text()))
            elif token == TOKEN_TEXT:
                steps.append(Ast.Step(title=Ast.Text(value)))
            else:
                self.backup()
                break
        return steps

    def parse_table(self):
        table = []
        row = []
        while True:
            token, value = self.next_()
            if token == TOKEN_TABLE_COLUMN:
                row.append(value)
            elif token == TOKEN_NEWLINE:
                table.append(row)
                row = []
            else:
                self.backup()
                break
        return Ast.Table(fields=table)

    def parse_examples(self):
        self.eat_newlines()
        token, value = self.next_()
        if token == TOKEN_LABEL and self.match_label('examples', value):
            self.eat_newlines()
            return Ast.Examples(table=self.parse_table())
        self.backup()

    def parse_scenarios(self):
        scenarios = []
        while True:
            self.eat_newlines()
            scenario = Ast.Scenario()
            scenario.tags = self.parse_tags()

            token, value = self.next_()
            if token in (None, TOKEN_EOF):
                break  # EOF
            elif not self.match_label('scenario', value):
                raise SyntaxError(
                    ('`{}\' should not be declared here, '
                     'Scenario expected').format(value))

            scenario.title = self.parse_title()
            scenario.steps = self.parse_steps()
            scenario.examples = self.parse_examples()
            scenarios.append(scenario)
        return scenarios

    def parse_tags(self):
        tags = []
        while True:
            token, value = self.next_()
            if token == TOKEN_TAG:
                tags.append(value)
            elif token == TOKEN_NEWLINE:
                self.ignore()
            else:
                self.backup()
                break
        return tags

    def parse_feature(self):
        feature = Ast.Feature()
        feature.tags = self.parse_tags()

        _, label = self.next_()
        if not self.match_label('feature', label):
            raise SyntaxError(
                'Feature expected in the beginning of the file, '
                'found `{}\' though.'.format(label))

        feature.title = self.parse_title()
        feature.description = self.parse_description()
        feature.background = self.parse_background()
        feature.scenarios = self.parse_scenarios()
        return feature

    def parse_metadata(self):
        token, key = self.next_()
        if token in (None, TOKEN_EOF): return
        assert token == TOKEN_META_LABEL

        token, value = self.next_()
        if token in (None, TOKEN_EOF):
            return
        elif token != TOKEN_META_VALUE:
            raise SyntaxError(
                'No value found for the meta-field `{}\''.format(key))
        return Ast.Metadata(key, value)


class Ast(object):
    class Node(object):
        def __eq__(self, other):
            return getattr(other, '__dict__', None) == self.__dict__

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
        def __init__(self, title=None, steps=None):
            self.title = title
            self.steps = steps or []

        def __repr__(self):
            return 'Background(title={}, steps={})'.format(
                self.title, self.steps)

    class Feature(Node):
        def __init__(self, title=None, tags=None, description=None, background=None, scenarios=None):
            self.title = title
            self.tags = tags or []
            self.description = description
            self.background = background
            self.scenarios = scenarios or []

        def __repr__(self):
            return 'Feature(title={}, tags={}, description={}, background={}, scenarios={})'.format(
                self.title, self.tags, self.description, self.background, self.scenarios)

    class Scenario(Node):
        def __init__(self, title=None, tags=None, description=None, steps=None, examples=None):
            self.title = title
            self.tags = tags or []
            self.description = description
            self.steps = steps or []
            self.examples = examples

        def __repr__(self):
            return 'Scenario(title={}, description={}, steps={}, examples={})'.format(
                self.title, self.description, self.steps, self.examples)

    class Step(Node):
        def __init__(self, title, table=None, text=None):
            self.title = title
            self.table = table
            self.text = text

        def __repr__(self):
            return 'Step(title={}, table={}, text={})'.format(
                self.title, self.table, self.text)

    class Table(Node):
        def __init__(self, fields):
            self.fields = fields

        def __repr__(self):
            return 'Table(fields={})'.format(self.fields)

    class Examples(Node):
        def __init__(self, table=None):
            self.table = table

        def __repr__(self):
            return 'Examples(table={})'.format(self.table)
