import re


class Lexer(object):
    def __init__(self, lang):
        pass

    def scan(self, data):
        i = 0
        tokens = []

        while i < len(data):
            chunk = data[i:]

            # Expressions to find out wtf is that chunk
            handlers = [
                self.scan_comment,
                self.scan_step,
                self.scan_examples,
                self.scan_identifier,
                self.scan_tags,
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

    def _exec(self, pattern, chunk, flags=0):
        found = re.compile(pattern, flags=flags).findall(chunk)
        return found and found[0]

    def cookie_monster(self, chunk):
        found = self._exec(r'\A(\n+)', chunk)
        return ('', found, len(found))

    def scan_comment(self, chunk):
        found = self._exec(r'\A(\s*\#\s*)([^\n]+)', chunk)
        return found and ('comment', found[1], sum(map(len, found)))

    def scan_tags(self, chunk):
        found = self._exec(r'\A(\s*)@([^\s]+)', chunk)
        return found and ('tag', found[1], sum(map(len, found))+1)

    def scan_examples(self, chunk):
        found = self._exec(r'\A(\:?\s+\|)([^\n]+)(\|\n)', chunk, re.M)
        if found:
            s, found, s2 = found
            vals = map(str.strip, found.split('|'))
            return ('row', tuple(vals), sum(map(len, [s, found, s2])))

    def scan_identifier(self, chunk):
        found = self._exec(r'\A([^\:\n]+)(\: *)([^\n\#]*)', chunk)
        if found:
            identifier, _, label = found
            return ('identifier',
                    (identifier.strip(), label.strip()),
                    sum(map(len, found)))

    def scan_step(self, chunk):
        found = self._exec(r'\A(\s*)(Given|When|Then|And|But)( *)([^\n\#\:]+)', chunk)
        if found:
            s1, name, s2, text = found
            return ('step', (name, text), sum(map(len, [s1, s2, name, text])))

    def scan_text(self, chunk):
        found = self._exec(r'\A([^\n\#]+)', chunk)
        # Corner case? When there's a comment in the same line we have text we
        # need to strip the text
        return found and ('text', found.strip(), len(found))
