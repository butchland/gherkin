import re
from functools import wraps


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

    def __init__(self, lang):
        pass

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
        s, found, s2 = found
        vals = map(str.strip, found.split('|'))
        return ('row', tuple(vals), sum(map(len, [s, found, s2])))

    @matcher(r'\A([^\:\n]+)(\: *)([^\n\#]*)')
    def scan_identifier(self, found):
        identifier, _, label = found
        return ('identifier',
                (identifier.strip(), label.strip()),
                sum(map(len, found)))

    @matcher(r'\A(\s*)(Given|When|Then|And|But)( *)([^\n\#\:]+)')
    def scan_step(self, found):
        s1, name, s2, text = found
        return ('step', (name, text), sum(map(len, [s1, s2, name, text])))

    @matcher(r'\A([^\n\#]+)')
    def scan_text(self, found):
        # Corner case? When there's a comment in the same line we have text we
        # need to strip the text
        return ('text', found.strip(), len(found))
