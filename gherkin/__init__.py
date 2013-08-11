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
                self.scan_identifier,
                self.scan_indent,
                self.scan_text,
                self.scan_newline,
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

    def _exec(self, pattern, chunk):
        found = re.compile(pattern).findall(chunk)
        return found and found[0]

    def scan_identifier(self, chunk):
        found = self._exec(r'\A([^\:\n]+)\:(\s*)', chunk)
        return found and ('identifier', found[0], sum(map(len, found)) + 1)

    def scan_text(self, chunk):
        found = self._exec(r'\A([^\n]+)', chunk)
        return found and ('text', found, len(found))

    def scan_newline(self, chunk):
        found = self._exec(r'\n$', chunk)
        return found and ('', '', len(found))

    def scan_indent(self, chunk):
        found = self._exec(r'\A\n(\s+)', chunk)

        if found:
            # Alright, we're inside of an indentation, let's see if it's bigger
            # or smaller than the current one
            new_indent = found
            new_indent_size = len(found)

            # Handling same level indentation
            if new_indent_size == self.current_indent_size:
                return ('', '', new_indent_size + 1)

            # Handling deindentation
            elif new_indent_size < self.current_indent_size:
                while len(found) < self.current_indent_size:
                    self.current_indent_size -= len(self.indent_stack.pop())
                return ('dedent', found, len(found))

            # Handling new indentation level
            self.indent_stack.append(new_indent)
            self.current_indent_size += new_indent_size

            # This `+ 1` is present in the next line cause the '\n' is not part
            # of the re group
            return ('indent', self.current_indent_size, len(new_indent) + 1)
