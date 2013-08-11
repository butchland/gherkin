from gherkin import Lexer


def test_lexer_single_feature():
    "The lexer should be able to emit tokens for the Feature identifier"

    # Given an instance of a localized lexes
    lexer = Lexer('en')

    # When I scan a feature description
    nodes = lexer.scan('''Feature: My Feature
  Description of my feature in
  multiple lines
''')

    # Then I see the corresponding node list is correct
    nodes.should.equal([
        ('identifier', 'Feature'),
        ('text', 'My Feature'),
        ('indent', 2),
        ('text', 'Description of my feature in'),
        ('text', 'multiple lines'),
        ('dedent', '\n'),
    ])


def test_lexer_two_features():
    # Given that I have an instance of a localized lexer
    lexer = Lexer('en')

    # When I scan a feature description
    nodes = lexer.scan('''Feature: My Feature
  Description of my feature in
  multiple lines



Feature: Another feature
  With another
  multiline
  description!
''')

    # Then I see that the corresponding node list is correct
    nodes.should.equal([
        ('identifier', 'Feature'),
        ('text', 'My Feature'),
        ('indent', 2),
        ('text', 'Description of my feature in'),
        ('text', 'multiple lines'),
        ('dedent', '\n'),
        ('identifier', 'Feature'),
        ('text', 'Another feature'),
        ('indent', 2),
        ('text', 'With another'),
        ('text', 'multiline'),
        ('text', 'description!'),
        ('dedent', '\n'),
    ])
