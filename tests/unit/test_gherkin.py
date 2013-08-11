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
