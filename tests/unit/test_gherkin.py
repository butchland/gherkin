from __future__ import unicode_literals
from gherkin import Lexer


def test_read_metadata():
    "It should be possible to read metadata from feature files"

    # Given that I have an instance of a lexer
    lexer = Lexer('en')

    # When I scan a feature with lang and encoding
    nodes = lexer.scan('''# language: en
# encoding: utf-8

Feature: My lame feature
     My lame description
''')

    # Then I see that the corresponding node list is correct
    nodes.should.equal([
        ('metadata', ('language', 'en')),
        ('metadata', ('encoding', 'utf-8')),
        ('identifier', ('Feature', 'My lame feature')),
        ('text', 'My lame description'),
    ])


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


def test_feature_with_comments():
    "It should be possible to add comments to features and text"

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


def test_feature_with_background():
    "It should be possible to declare a background for a feature"

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


def test_random_spaces_in_syntax():
    "It should be possible to use any syntax when declaring steps"

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


def test_tables():
    "It should be possible to declare tables in steps"

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


def test_scenario_outlines():
    "It should be possible to declare a complete scenario outline"

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


def test_tags():
    "It should be possible to read tags"

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


def test_multiline_strings():
    "It should be possible to declare multiline strings in steps"

    # Given that I have a tasty instance of a delicious localized lexer
    lexer = Lexer('en')

    # When I scan the description of a feature with some multiline strings
    nodes = lexer.scan('''\
Feature: Create new files

  As a user
  I need to create files

  Background:
    Given an empty directory
    When I create the file "blah" with:
      """
      This is the content of my file
      there are multiple lines here, can
      ya see? :)
      """
''')

    # Then I see that the correspond list of tokens is right
    nodes.should.equal([
        ('identifier', ('Feature', 'Create new files')),
        ('text', 'As a user'),
        ('text', 'I need to create files'),
        ('identifier', ('Background', '')),
        ('step', ('Given', 'an empty directory')),
        ('step', ('When', 'I create the file "blah" with')),
        ('text', ('This is the content of my file\n'
                  'there are multiple lines here, can\n'
                  'ya see? :)')),
    ])
