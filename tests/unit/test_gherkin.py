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


def test_lexer_feature_with_comments():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan a feature description with comments
    nodes = lexer.scan('''\
# Some nice comments
# Some more nice comments

Feature: Name     # More comments
  Description     # Desc
''')

    # Then I see that the corresponding node list is correct
    nodes.should.equal([
        ('comment', "Some nice comments"),
        ('comment', "Some more nice comments"),
        ('identifier', 'Feature'),
        ('text', 'Name'),
        ('comment', 'More comments'),
        ('indent', 2),
        ('text', 'Description'),
        ('comment', 'Desc'),
        ('dedent', '\n'),
    ])


def test_lexer_two_features():
    # Given that I have an instance of a localized lexer
    lexer = Lexer('en')

    # When I scan a feature description
    nodes = lexer.scan('''\
Feature: My Feature
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


def test_lexer_feature_with_background():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan a feature description with a background
    nodes = lexer.scan('''\
Feature: Random
  Description with
  two lines

  Background:
    Given a feature
    And a background
    And some cookies
''')

    # Then I see that the corresponding node list is correct
    nodes.should.equal([
        ('identifier', 'Feature'),
        ('text', 'Random'),
        ('indent', 2),
        ('text', 'Description with'),
        ('text', 'two lines'),
        ('identifier', 'Background'),
        ('indent', 4),
        ('step', ('Given', 'a feature')),
        ('step', ('And', 'a background')),
        ('step', ('And', 'some cookies')),
        ('dedent', '\n'),
        ('dedent', '\n'),
    ])
