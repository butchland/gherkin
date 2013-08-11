import re


class Lexer(object):
    def __init__(self, lang):
        self.current_indent_size = 0
        self.indent_stack = []

    def scan(self, data):
        i = 0
        tokens = []

        while i < len(data):
            chunk = data[i:]

            # Expressions to find out wtf is that chunk
            handlers = [
                self.scan_dedent,
                self.scan_indent,
                self.scan_comment,
                self.scan_identifier,
                self.scan_step,
                self.scan_text,
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

        # Closing open indentations
        while self.current_indent_size > 0:
            self.current_indent_size -= len(self.indent_stack.pop())
            tokens.append(('dedent', '\n'))

        return tokens

    def _exec(self, pattern, chunk, flags=0):
        found = re.compile(pattern, flags=flags).findall(chunk)
        return found and found[0]

    def scan_comment(self, chunk):
        found = self._exec(r'\A(\s*\#\s*([^\n]+))', chunk)
        if found:
            actual, filtered = found
            return ('comment', filtered, len(actual))

    def scan_identifier(self, chunk):
        found = self._exec(r'\A([^\:\n]+)(\: *)', chunk)
        return found and ('identifier', found[0], sum(map(len, found)))

    def scan_step(self, chunk):
        found = self._exec(r'\A(Given|When|Then|And) *([^\n\#]+)', chunk)
        if found:
            name, text = found
            return ('step', (name, text), sum(map(len, found))+1)

    def scan_text(self, chunk):
        found = self._exec(r'\A([^\n\#]+)', chunk)
        # Corner case? When there's a comment in the same line we have text we
        # need to strip the text
        return found and ('text', found.strip(), len(found))

    def scan_dedent(self, chunk):
        found = self._exec(r'\A(\n)[^ \#\n]', chunk)
        if found and self.current_indent_size > 0:
            self.current_indent_size -= len(self.indent_stack.pop())
            return ('dedent', found, len(found))

    def scan_indent(self, chunk):
        # Don't use `\s` here, since it contains `\n` on it
        found = self._exec(r'\A(\n)( *)', chunk)

        if found:
            # Alright, we're inside of an indentation, let's see if it's bigger
            # or smaller than the current one;

            new_line, new_indent = found
            new_indent_size = len(new_indent)
            chars_to_eat = new_indent_size + 1  # \n

            # Handling new lines
            if not new_indent_size:
                return ('', '', chars_to_eat)

            # Handling same level indentation
            elif new_indent_size == self.current_indent_size:
                return ('', '', chars_to_eat)

            # Handling new indentation level
            self.indent_stack.append(
                ' ' * (new_indent_size - self.current_indent_size))
            self.current_indent_size = new_indent_size

            return ('indent', self.current_indent_size, chars_to_eat)
