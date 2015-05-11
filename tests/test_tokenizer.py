__author__ = 'tla'

import json
import unittest
import wordtokenize
from parse import from_sc


class Test (unittest.TestCase):

    testdoc = None

    def setUp(self):
        with open('tests/data/M1731.json', encoding='utf-8') as fh:
            jdata = json.load(fh)
        self.testdoc = from_sc(jdata)


    def test_simple(self):
        """Test a plain & simple file without special markup beyond line breaks."""
        pass

    def test_glyphs(self):
        """Test the correct detection and rendering of glyphs. The characters in
        the resulting token should be the characters that are the content of the
        g tag. """
        pass

    def test_substitution(self):
        """Test that the correct words are picked out of a subst tag."""
        tokens = wordtokenize.from_etree(self.testdoc)
        # Find the token that has our substitution
        found = False
        for t in tokens:
            if t['lit'] != 'դե<add xmlns="http://www.tei-c.org/ns/1.0">ռ</add>ևս':
                continue
            self.assertEqual(t['t'], 'դեռևս')
            found = True
        self.assertTrue(found, "Did not find the testing token")


    def test_substitution_layer(self):
        """Test that the first_layer option works correctly."""
        tokens = wordtokenize.from_etree(self.testdoc, first_layer=True)
        # Find the token that has our substitution
        found = False
        for t in tokens:
            if t['lit'] != 'դե<del xmlns="http://www.tei-c.org/ns/1.0">ղ</del>ևս':
                continue
            self.assertEqual(t['t'], 'դեղևս')
            found = True
        self.assertTrue(found, "Did not find the testing token")

    def test_del_word_boundary(self):
        """Test that a strategically placed del doesn't cause erroneous joining of words.
        TODO add testing data"""
        pass

    def test_gap(self):
        """Test that gaps are handled correctly. At the moment this means that no token
        should be generated for a gap."""
        pass

    def test_milestone_element(self):
        """Test that milestone elements (not <milestone>, but e.g. <lb/> or <cb/>)
         are passed through correctly in the token 'lit' field."""
        pass

    def test_milestone_option(self):
        """Test that passing a milestone option gives back only the text from the
        relevant <milestone/> element to the next one."""
        pass

    def test_arbitrary_element(self):
        """Test that arbitrary tags (e.g. <abbr>) are passed into 'lit' correctly."""
        pass

    def test_file_input(self):
        """Make sure we get a result when passing a file path."""
        pass

    def test_fh_input(self):
        """Make sure we get a result when passing an open filehandle object."""
        pass

    def test_string_input(self):
        """Make sure we get a result when passing a string containing XML."""
        pass

    def test_object_input(self):
        """Make sure we get a result when passing an lxml.etree object."""
        pass

    def testLegacyTokenization(self):
        """Test with legacy TEI files from 2009, to make sure the tokenizer
        works with them."""
        testfile = 'tests/data/matenadaran_1896.xml'
        with open('tests/data/matenadaran_1896_reference.txt', encoding='utf-8') as rfh:
            rtext = rfh.read()
        reference = rtext.rstrip().split(' ')
        tokens = wordtokenize.from_file(testfile)
        for i, t in enumerate(tokens):
            self.assertEqual(t['t'], reference[i], "Mismatch at index %d: %s - %s" % (i, t, reference[i]))