# -*- coding: utf-8; -*-

import gherkin
from gherkin import Lexer, Parser, Ast


def test_lex_test_eof():
    "lex_text() Should be able to find EOF"

    # Given a lexer that takes '' as the input string
    lexer = gherkin.Lexer('')

    # When we try to lex any text from ''
    new_state = lexer.lex_text()

    # Then we see we've got to EOF and that new state is nil
    lexer.tokens.should.equal([(gherkin.TOKEN_EOF, '')])
    new_state.should.be.none


def test_lex_text():
    "lex_text() Should be able to find text before EOF"

    # Given a lexer that takes some text as input string
    lexer = gherkin.Lexer('some text')

    # When we lex it
    new_state = lexer.lex_text()

    # Then we see we found both the text and the EOF token
    lexer.tokens.should.equal([
        (gherkin.TOKEN_TEXT, 'some text'),
        (gherkin.TOKEN_EOF, '')
    ])

    # And the new state is nil
    new_state.should.be.none


def test_lex_hash_with_text():
    "lex_text() Should stop lexing at # (we found a comment!)"

    # Given a lexer with some text and some comment
    lexer = gherkin.Lexer(' some text # random comment')

    # When the input is lexed through the text lexer
    new_state = lexer.lex_text()

    # Then we see the following token on the output list
    lexer.tokens.should.equal([
        (gherkin.TOKEN_TEXT, 'some text '),
    ])

    # And that the next state will lex comments
    new_state.should.equal(lexer.lex_comment)


def test_lex_comment():
    "lex_comment() Should stop lexing at \\n"

    # Given a lexer loaded with some comments
    lexer = gherkin.Lexer('   random comment')

    # When We lex the input text
    new_state = lexer.lex_comment()

    # Then we see the comment above was captured
    lexer.tokens.should.equal([
        (gherkin.TOKEN_COMMENT, 'random comment'),
    ])

    # And that new state is lex_text()
    new_state.should.equal(lexer.lex_text)


def test_lex_comment_meta_label():
    "lex_comment() Should stop lexing at : (we found a label)"

    # Given a lexer loaded with a comment that contains a label
    lexer = gherkin.Lexer('     metadata: test')

    # When we lex the comment
    new_state = lexer.lex_comment()

    # Then we see that a label was found
    lexer.tokens.should.equal([
        (gherkin.TOKEN_META_LABEL, 'metadata'),
    ])

    # And that new state is going to read the value of the variable we
    # just found
    new_state.should.equal(lexer.lex_comment_metadata_value)


def test_lex_comment_metadata_value():
    "lex_comment_metadata_value() Should stop lexing at \n"

    # Given a lexer loaded with the value of a label and a new line
    # with more text
    lexer = gherkin.Lexer(' test value\nblah')

    # When we lex the input string
    new_state = lexer.lex_comment_metadata_value()

    # Then we see that only the value present is the one before the
    # \n, everything else will be lexed by lex_text
    lexer.tokens.should.equal([
        (gherkin.TOKEN_META_VALUE, 'test value'),
    ])

    # And we also see that the next
    new_state.should.equal(lexer.lex_text)

def test_lex_comment_no_newline():

    # Given a lexer loaded with a comment without the newline marker
    lexer = gherkin.Lexer(' test comment')

    # When we lex the input string
    new_state = lexer.lex_comment_metadata_value()

    # Then we see the whole line was captured
    lexer.tokens.should.equal([
        (gherkin.TOKEN_META_VALUE, 'test comment'),
    ])

    # And we also see that the next
    new_state.should.equal(lexer.lex_text)


def test_lex_comment_until_newline():
    "Lexer.lex_comment() Should parse comments until the newline character"

    # Given a lexer loaded with comments containing a metadata field
    lexer = gherkin.Lexer('# one line\n# another line')

    # When I run the lexer
    tokens = lexer.run()

    # Then we see both lines were captured
    lexer.tokens.should.equal([
        (gherkin.TOKEN_COMMENT, 'one line'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_COMMENT, 'another line'),
        (gherkin.TOKEN_EOF, ''),
    ])


def test_lex_comment_full():
    "Lexer.run() Should be able to process metadata in comments"

    # Given a lexer loaded with comments containing a metadata field
    lexer = gherkin.Lexer('some text # metadata-field: blah-value\ntext')

    # When I run the lexer
    tokens = lexer.run()

    # Then I see the tokens collected match some text, a field, more
    # text and EOF
    tokens.should.equal([
        (gherkin.TOKEN_TEXT, 'some text '),
        (gherkin.TOKEN_META_LABEL, 'metadata-field'),
        (gherkin.TOKEN_META_VALUE, 'blah-value'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'text'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_lex_text_with_label():
    "Lexer.run() Should be able to parse a label with some text"

    # Given a lexer loaded with a feature
    lexer = gherkin.Lexer(
        'Feature: A cool feature\n  some more text\n  even more text')

    # When we run the lexer
    tokens = lexer.run()

    # Then we see the token list matches the label, text, text EOF
    # sequence
    tokens.should.equal([
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'A cool feature'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'some more text'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'even more text'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_lex_text_with_labels():
    "Lexer.run() Should be able to tokenize a feature with a scenario"

    # Given a lexer with a more complete feature+scenario
    lexer = gherkin.Lexer('''

Feature: Some descriptive text
  In order to parse a Gherkin file
  As a parser
  I want to be able to parse scenarios

  Even more text

  Scenario: The user wants to describe a feature
''')

    # When we run the lexer
    tokens = lexer.run()

    # Then we see it was broken down into the right list of tokens
    tokens.should.equal([
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'Some descriptive text'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'In order to parse a Gherkin file'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'As a parser'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'I want to be able to parse scenarios'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Even more text'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_TEXT, 'The user wants to describe a feature'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_lex_text_with_steps():
    "Lexer.run() Should be able to tokenize steps"

    # Given a lexer loaded with feature+background+scenario+steps
    lexer = gherkin.Lexer('''\
Feature: Feature title
  feature description
  Background: Some background
    about the problem
  Scenario: Scenario title
    Given first step
     When second step
     Then third step
''')

    # When we run the lexer
    tokens = lexer.run()

    # Then we see that everything, including the steps was properly
    # tokenized
    tokens.should.equal([
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'Feature title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'feature description'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Background'),
        (gherkin.TOKEN_TEXT, 'Some background'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'about the problem'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_TEXT, 'Scenario title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Given first step'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'When second step'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Then third step'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_lex_load_languages():
    "Lexer.run() Should be able to parse different languages"

    # Given the following lexer instance loaded with another language
    lexer = gherkin.Lexer('''# language: pt-br

    Funcionalidade: Interpretador para gherkin
      Para escrever testes de aceitação
      Como um programador
      Preciso de uma ferramenta de BDD
    Contexto:
      Dado que a variavel "X" contém o número 2
    Cenário: Lanche
      Dada uma maçã
      Quando mordida
      Então a fome passa
    ''')

    # When we run the lexer
    tokens = lexer.run()

    # Then the following list of tokens is generated
    tokens.should.equal([
        (gherkin.TOKEN_META_LABEL, 'language'),
        (gherkin.TOKEN_META_VALUE, 'pt-br'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Funcionalidade'),
        (gherkin.TOKEN_TEXT, 'Interpretador para gherkin'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Para escrever testes de aceitação'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Como um programador'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Preciso de uma ferramenta de BDD'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Contexto'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Dado que a variavel "X" contém o número 2'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Cenário'),
        (gherkin.TOKEN_TEXT, 'Lanche'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Dada uma maçã'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Quando mordida'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Então a fome passa'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_lex_tables():
    "Lexer.run() Should be able to lex tables"

    # Given the following lexer loaded with an examples label followed
    # by a table that ends before '\n'
    lexer = gherkin.Lexer('''\
  Examples:
    | column1 | column2 | ''')

    # When we run the lexer
    tokens = lexer.run()

    # Then we see the scenario outline case was properly parsed
    tokens.should.equal([
        (gherkin.TOKEN_LABEL, 'Examples'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'column1'),
        (gherkin.TOKEN_TABLE_COLUMN, 'column2'),
        (gherkin.TOKEN_EOF, ''),
    ])


def test_lex_tables_full():
    "Lexer.run() Should be able to lex scenario outlines"

    lexer = gherkin.Lexer('''\
  Feature: gherkin has steps with examples
  Scenario Outline: Add two numbers
    Given I have <input_1> and <input_2> the calculator
    When I press Sum!
    Then the result should be <output> on the screen
  Examples:
    | input_1 | input_2 | output |
    | 20      | 30      | 50     |
    | 0       | 40      | 40     |
''')

    # When we run the lexer
    tokens = lexer.run()

    # Then we see the scenario outline case was properly parsed
    tokens.should.equal([
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'gherkin has steps with examples'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario Outline'),
        (gherkin.TOKEN_TEXT, 'Add two numbers'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Given I have <input_1> and <input_2> the calculator'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'When I press Sum!'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Then the result should be <output> on the screen'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Examples'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'input_1'),
        (gherkin.TOKEN_TABLE_COLUMN, 'input_2'),
        (gherkin.TOKEN_TABLE_COLUMN, 'output'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, '20'),
        (gherkin.TOKEN_TABLE_COLUMN, '30'),
        (gherkin.TOKEN_TABLE_COLUMN, '50'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, '0'),
        (gherkin.TOKEN_TABLE_COLUMN, '40'),
        (gherkin.TOKEN_TABLE_COLUMN, '40'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_lex_tables_within_steps():
    "Lexer.run() Should be able to lex example tables from steps"

    # Given a lexer loaded with steps that contain example tables
    lexer = gherkin.Lexer('''\
	Feature: Check models existence
		Background:
	   Given I have a garden in the database:
	      | @name  | area | raining |
	      | Secret Garden | 45   | false   |
	    And I have gardens in the database:
	      | name            | area | raining |
	      | Octopus' Garden | 120  | true    |
    ''')

    # When we run the lexer
    tokens = lexer.run()

    # Then we see that steps that contain : will be identified as
    # labels
    tokens.should.equal([
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'Check models existence'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Background'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Given I have a garden in the database'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, '@name'),
        (gherkin.TOKEN_TABLE_COLUMN, 'area'),
        (gherkin.TOKEN_TABLE_COLUMN, 'raining'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Secret Garden'),
        (gherkin.TOKEN_TABLE_COLUMN, '45'),
        (gherkin.TOKEN_TABLE_COLUMN, 'false'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'And I have gardens in the database'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'name'),
        (gherkin.TOKEN_TABLE_COLUMN, 'area'),
        (gherkin.TOKEN_TABLE_COLUMN, 'raining'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Octopus\' Garden'),
        (gherkin.TOKEN_TABLE_COLUMN, '120'),
        (gherkin.TOKEN_TABLE_COLUMN, 'true'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, '')
    ])


def test_parse_metadata_empty():

    Parser([(gherkin.TOKEN_EOF, '')]).parse_metadata().should.be.none

    Parser([None]).parse_metadata().should.be.none


def test_parse_metadata_incomplete():

    parser = Parser([
        (gherkin.TOKEN_META_LABEL, 'language'),
        (gherkin.TOKEN_EOF, ''),
    ])

    parser.parse_metadata().should.be.none


def test_parse_metadata_syntax_error():

    parser = Parser([
        (gherkin.TOKEN_META_LABEL, 'language'),
        (gherkin.TOKEN_TEXT, 'pt-br'),
    ])

    parser.parse_metadata.when.called.should.throw(
        SyntaxError, 'No value found for the meta-field `language\'')


def test_parse_metadata():

    parser = Parser([
        (gherkin.TOKEN_META_LABEL, 'language'),
        (gherkin.TOKEN_META_VALUE, 'pt-br'),
    ])

    metadata = parser.parse_metadata()

    metadata.should.equal(Ast.Metadata('language', 'pt-br'))


def test_parse_empty_title():

    parser = Parser([
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'more text after title'),
    ])

    feature = parser.parse_title()

    feature.should.equal(Ast.Text(''))


def test_parse_title():

    parser = Parser([
        (gherkin.TOKEN_TEXT, 'Scenario title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
    ])

    feature = parser.parse_title()

    feature.should.equal(Ast.Text('Scenario title'))


def test_parse_table():

    parser = Parser([
        (gherkin.TOKEN_TABLE_COLUMN, 'name'),
        (gherkin.TOKEN_TABLE_COLUMN, 'email'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Lincoln'),
        (gherkin.TOKEN_TABLE_COLUMN, 'lincoln@clarete.li'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Gabriel'),
        (gherkin.TOKEN_TABLE_COLUMN, 'gabriel@nacaolivre.org'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_EOF, ''),
    ])

    feature = parser.parse_table()

    feature.should.equal(Ast.Table(fields=[
        ['name', 'email'],
        ['Lincoln', 'lincoln@clarete.li'],
        ['Gabriel', 'gabriel@nacaolivre.org'],
    ]))


def test_parse_background():

    parser = Parser([
        (gherkin.TOKEN_LABEL, 'Background'),
        (gherkin.TOKEN_TEXT, 'title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Given two users in the database'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'name'),
        (gherkin.TOKEN_TABLE_COLUMN, 'email'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Lincoln'),
        (gherkin.TOKEN_TABLE_COLUMN, 'lincoln@clarete.li'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Gabriel'),
        (gherkin.TOKEN_TABLE_COLUMN, 'gabriel@nacaolivre.org'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
    ])

    feature = parser.parse_background()

    feature.should.equal(Ast.Background(
        title=Ast.Text('title'),
        steps=[
            Ast.Step(
                title=Ast.Text('Given two users in the database'),
                table=Ast.Table([
                    ['name', 'email'],
                    ['Lincoln', 'lincoln@clarete.li'],
                    ['Gabriel', 'gabriel@nacaolivre.org'],
                ]))
        ]))


def teste_parse_scenarios():

    parser = Parser([
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_TEXT, 'Scenario title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Given first step'),
    ])

    feature = parser.parse_scenarios()

    feature.should.equal([Ast.Scenario(
        title=Ast.Text('Scenario title'),
        steps=[Ast.Step(Ast.Text('Given first step'))],
    )])


def test_parse_not_starting_with_feature():

    parser = gherkin.Parser(gherkin.Lexer('''
Scenario: Scenario title
  Given first step
   When second step
   Then third step
    ''').run())

    parser.parse_feature.when.called.should.throw(
        SyntaxError,
        "Feature expected in the beginning of the file, "
        "found `Scenario' though.")


def test_parse_feature_two_backgrounds():

    parser = gherkin.Parser(gherkin.Lexer('''
Feature: Feature title
  feature description
  Background: Some background
    about the problem
  Background: Some other background
    will raise an exception
  Scenario: Scenario title
    Given first step
     When second step
     Then third step
    ''').run())

    parser.parse_feature.when.called.should.throw(
        SyntaxError, "`Background' should not be declared here, Scenario expected")


def test_parse_feature_background_wrong_place():

    parser = gherkin.Parser(gherkin.Lexer('''
Feature: Feature title
  feature description
  Scenario: Scenario title
    Given first step
     When second step
     Then third step
  Background: Some background
    about the problem
    ''').run())

    parser.parse_feature.when.called.should.throw(
        SyntaxError, "`Background' should not be declared here, Scenario expected")


def test_parse_feature():

    parser = Parser([
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'Feature title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'feature description'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Background'),
        (gherkin.TOKEN_TEXT, 'Some background'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'about the problem'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_TEXT, 'Scenario title'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Given first step'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_TEXT, 'Another scenario'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Given this step'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'When we take another step'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, ''),
    ])

    feature = parser.parse_feature()

    feature.should.equal(Ast.Feature(
        title=Ast.Text('Feature title'),
        description=Ast.Text('feature description'),
        background=Ast.Background(
            title=Ast.Text('Some background'),
            steps=[Ast.Step(Ast.Text('about the problem'))]),
        scenarios=[
            Ast.Scenario(title=Ast.Text('Scenario title'),
                         steps=[Ast.Step(Ast.Text('Given first step'))]),
            Ast.Scenario(title=Ast.Text('Another scenario'),
                         steps=[Ast.Step(Ast.Text('Given this step')),
                                Ast.Step(Ast.Text('When we take another step'))]),
        ],
    ))


def test_parse_tables_within_steps():
    "Lexer.run() Should be able to lex example tables from steps"

    # Given a parser loaded with steps that contain example tables
    '''\
	Feature: Check models existence
		Background:
	   Given I have a garden in the database:
	      | @name  | area | raining |
	      | Secret Garden | 45   | false   |
	    And I have gardens in the database:
	      | name            | area | raining |
	      | Octopus' Garden | 120  | true    |
         Scenario: Plant a tree
           Given the <name> of a garden
           When I plant a tree
            And wait for <num_days> days
           Then I see it growing
         # Examples:
         #   | name | num_days |
         #   | Secret | 2 |
         #   | Octopus | 5 |
    '''
    parser = Parser([
        (gherkin.TOKEN_LABEL, 'Feature'),
        (gherkin.TOKEN_TEXT, 'Check models existence'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Background'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Given I have a garden in the database'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, '@name'),
        (gherkin.TOKEN_TABLE_COLUMN, 'area'),
        (gherkin.TOKEN_TABLE_COLUMN, 'raining'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'Secret Garden'),
        (gherkin.TOKEN_TABLE_COLUMN, '45'),
        (gherkin.TOKEN_TABLE_COLUMN, 'false'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'And I have gardens in the database'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, 'name'),
        (gherkin.TOKEN_TABLE_COLUMN, 'area'),
        (gherkin.TOKEN_TABLE_COLUMN, 'raining'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TABLE_COLUMN, "Octopus' Garden"),
        (gherkin.TOKEN_TABLE_COLUMN, '120'),
        (gherkin.TOKEN_TABLE_COLUMN, 'true'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_LABEL, 'Scenario'),
        (gherkin.TOKEN_TEXT, 'Plant a tree'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Given the <name> of a garden'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'When I plant a tree'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'And wait for <num_days> days'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_TEXT, 'Then I see it growing'),
        (gherkin.TOKEN_NEWLINE, '\n'),
        (gherkin.TOKEN_EOF, '')
    ])

    feature = parser.parse_feature()

    feature.should.equal(Ast.Feature(
        title=Ast.Text('Check models existence'),
        description=Ast.Text(""),
        background=Ast.Background(
            title=Ast.Text(""),
            steps=[
                Ast.Step(Ast.Text('Given I have a garden in the database'),
                         Ast.Table([['@name', 'area', 'raining'],
                                    ['Secret Garden', '45', 'false']])),
                Ast.Step(Ast.Text('And I have gardens in the database'),
                         Ast.Table([['name', 'area', 'raining'],
                                    ['Octopus\' Garden', '120', 'true']])),
            ]
        ),
        scenarios=[
            Ast.Scenario(title=Ast.Text('Plant a tree'),
                         steps=[Ast.Step(Ast.Text('Given the <name> of a garden')),
                                Ast.Step(Ast.Text('When I plant a tree')),
                                Ast.Step(Ast.Text('And wait for <num_days> days')),
                                Ast.Step(Ast.Text('Then I see it growing'))],
                     )
        ],
    ))


def test_ast_node_equal():

    # Given two different AST nodes
    n1 = Ast.Node()
    n2 = Ast.Node()

    # And different attributes to each node
    n1.name = 'Lincoln'
    n2.color = 'green'

    # When I compare them
    equal = n1 == n2

    # Then I see they're different
    equal.should.be.false
