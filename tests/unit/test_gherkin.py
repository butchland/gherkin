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
        ('identifier', ('Feature', 'My Feature')),
        ('text', 'Description of my feature in'),
        ('text', 'multiple lines'),
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
        ('identifier', ('Feature', 'Name')),
        ('comment', 'More comments'),
        ('text', 'Description'),
        ('comment', 'Desc'),
    ])


def test_lexer_two_features():
    # Given that I have an instance of a localized lexer
    lexer = Lexer('en')

    # When I scan two feature descriptions
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
        ('identifier', ('Feature', 'My Feature')),
        ('text', 'Description of my feature in'),
        ('text', 'multiple lines'),

        ('identifier', ('Feature', 'Another feature')),
        ('text', 'With another'),
        ('text', 'multiline'),
        ('text', 'description!'),
    ])


def test_lexer_feature_with_background():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan a feature with a background
    nodes = lexer.scan('''\
Feature: Random
  Description with
  two lines

  Background:
    Given a feature
      And a background
     Then I eat some cookies
''')

    # Then I see that the corresponding node list is correct
    nodes.should.equal([
        ('identifier', ('Feature', 'Random')),

        ('text', 'Description with'),
        ('text', 'two lines'),
        ('identifier', ('Background', '')),

        ('step', ('Given', 'a feature')),
        ('step', ('And', 'a background')),
        ('step', ('Then', 'I eat some cookies')),
    ])


def test_lexer_weird_syntax():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan the description of a feature with a scenario with a list of
    # weirdly indented steps
    nodes = lexer.scan('''\
Feature: Paladin
  Coder that cleans stuff up

  Scenario: Fight the evil
    Given that I have super powers
      And a nice costume
   When I see bad code
     Then I should rewrite it to look good

  Scenario: Eat cookies
    Given that I'm hungry
     When I open the cookie jar
     Then I should eat a delicious cookie
''')

    # Then I see that the corresponding node list is correct
    nodes.should.equal([
        ('identifier', ('Feature', 'Paladin')),
        ('text', 'Coder that cleans stuff up'),

        ('identifier', ('Scenario', 'Fight the evil')),

        ('step', ('Given', 'that I have super powers')),
        ('step', ('And', 'a nice costume')),
        ('step', ('When', 'I see bad code')),
        ('step', ('Then', 'I should rewrite it to look good')),

        ('identifier', ('Scenario', 'Eat cookies')),

        ('step', ('Given', 'that I\'m hungry')),
        ('step', ('When', 'I open the cookie jar')),
        ('step', ('Then', 'I should eat a delicious cookie')),
    ])


def test_lexer_examples():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan the description of a feature with a scenario outlines
    nodes = lexer.scan('''\
Feature: Name

  Scenario: Hacker list
    Given that I have a list of hackers:
      | name    | email             |
      | lincoln | lincoln@wlabs.com |
      | gabriel | gabriel@wlabs.com |
    When I create them as "super-ultra-users"
''')

    # Then I see that the correspond list of tokens is right
    nodes.should.equal([
        ('identifier', ('Feature', 'Name')),

        ('identifier', ('Scenario', 'Hacker list')),

        ('step', ('Given', 'that I have a list of hackers')),
        ('row', ('name', 'email')),
        ('row', ('lincoln', 'lincoln@wlabs.com')),
        ('row', ('gabriel', 'gabriel@wlabs.com')),
        ('step', ('When', 'I create them as "super-ultra-users"')),
    ])


def test_lexer_scenario_outlines():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan the description of a feature with a scenario outlines
    nodes = lexer.scan('''\
Feature: Name

  Scenario Outline: Hacker list
    Given I have the users:
      | name    | email             |
      | lincoln | lincoln@wlabs.com |
      | gabriel | gabriel@wlabs.com |
    When   I create them as "<role>"
    Then   they have permission to "edit <content type>"

  Examples:
    | role        | content type |
    | superuser   | posts        |
    | normal user | comments     |
''')

    # Then I see that the correspond list of tokens is right
    nodes.should.equal([
        ('identifier', ('Feature', 'Name')),

        ('identifier', ('Scenario Outline', 'Hacker list')),

        ('step', ('Given', 'I have the users')),
        ('row', ('name', 'email')),
        ('row', ('lincoln', 'lincoln@wlabs.com')),
        ('row', ('gabriel', 'gabriel@wlabs.com')),

        ('step', ('When', 'I create them as "<role>"')),
        ('step', ('Then', 'they have permission to "edit <content type>"')),
        ('identifier', ('Examples', '')),
        ('row', ('role', 'content type')),
        ('row', ('superuser', 'posts')),
        ('row', ('normal user', 'comments')),
    ])


def test_lexer_tags():
    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan the description of a feature with some tags
    nodes = lexer.scan('''\
@tag1 @tag|2
Feature: Name

  @tag.3 @tag-4
  Scenario: Hacker list
    Given that I have a list of hackers:
      | name    | email             |
      | lincoln | lincoln@wlabs.com |
      | gabriel | gabriel@wlabs.com |
    When I create them as "super-ultra-users"
''')

    # Then I see that the correspond list of tokens is right
    nodes.should.equal([
        ('tag', 'tag1'),
        ('tag', 'tag|2'),
        ('identifier', ('Feature', 'Name')),

        ('tag', 'tag.3'),
        ('tag', 'tag-4'),
        ('identifier', ('Scenario', 'Hacker list')),

        ('step', ('Given', 'that I have a list of hackers')),
        ('row', ('name', 'email')),
        ('row', ('lincoln', 'lincoln@wlabs.com')),
        ('row', ('gabriel', 'gabriel@wlabs.com')),
        ('step', ('When', 'I create them as "super-ultra-users"')),
    ])
