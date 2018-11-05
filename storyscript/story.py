# -*- coding: utf-8 -*-
import io
import os
import re

from lark.exceptions import UnexpectedInput, UnexpectedToken

from .compiler import Compiler
from .exceptions import CompilerError, StoryError, StorySyntaxError
from .parser import Parser


class Story:
    """
    Represents a single story and exposes methods for reading, parsing and
    compiling it.
    """

    def __init__(self, story, path=None):
        self.story = story
        self.path = path

    @staticmethod
    def clean_source(source):
        """
        Cleans a story by removing comments.
        """
        expression = r'(?<=###)\s(.*|\\n)+(?=\s###)|#(.*)'
        return re.sub(expression, '', source)

    @classmethod
    def read(cls, path):
        """
        Reads a story
        """
        try:
            with io.open(path, 'r') as file:
                return cls.clean_source(file.read())
        except FileNotFoundError:
            abspath = os.path.abspath(path)
            print('File "{}" not found at {}'.format(path, abspath))
            exit()

    @classmethod
    def from_file(cls, path):
        """
        Creates a story from a file source
        """
        return Story(cls.read(path), path=path)

    @staticmethod
    def from_stream(stream):
        """
        Creates a story from a stream source
        """
        return Story(stream.read())

    def line(self, line):
        """
        Gets a single line from the source
        """
        return self.story.splitlines(keepends=False)[line]

    def slice(self, start, end):
        return self.story.splitlines(keepends=False)[start:end]

    def error(self, error, debug=False):
        """
        Handles errors by printing a nice message or raising the real error.
        """
        if debug:
            raise error
        # I don't really need the tree and I can extract line and column from
        # the error.
        StoryError(error, self.path, self.story).echo()
        # most likely echo can exit
        exit()

    def parse(self, ebnf=None, debug=False):
        """
        Parses the story, storing the tree
        """
        parser = Parser(ebnf=ebnf)
        try:
            self.tree = parser.parse(self.story, debug=debug)
        except UnexpectedToken as error:
            self.error(error, debug=debug)
        except UnexpectedInput as error:
            self.error(error, debug=debug)

    def modules(self):
        """
        Gets the modules of a story from its tree.
        """
        modules = []
        for module in self.tree.find_data('imports'):
            path = module.string.child(0).value[1:-1]
            if path.endswith('.story') is False:
                path = '{}.story'.format(path)
            modules.append(path)
        return modules

    def compile(self, debug=False):
        """
        Compiles the story and stores the result.
        """
        try:
            self.compiled = Compiler.compile(self.tree, debug=debug)
        except (CompilerError, StorySyntaxError) as error:
            self.error(error, debug=debug)

    def lex(self, ebnf=None):
        """
        Lexes a story
        """
        return Parser(ebnf=ebnf).lex(self.story)

    def process(self, ebnf=None, debug=False):
        """
        Parse and compile a story, returning the compiled JSON
        """
        self.parse(ebnf=ebnf, debug=debug)
        self.compile(debug=debug)
        return self.compiled
