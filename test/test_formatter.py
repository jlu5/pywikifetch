#!/usr/bin/env python3
import unittest

from pywikifetch.wikitext_formatter import MarkdownFormatter, PlainTextFormatter

class PlainTextFormatterTest(unittest.TestCase):
    def setUp(self):
        self._formatter = PlainTextFormatter()

    def test_simple(self):
        inp = expected = 'Hello world'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_bold(self):
        inp = "'''Hello world'''"
        expected = 'Hello world'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_italic(self):
        inp = "''Hello world''"
        expected = 'Hello world'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_bold_italics_in_one_word(self):
        inp = "''Ab'''''cd'''<b>''efg''</b>"
        expected = 'Abcdefg'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_strikethrough(self):
        inp = """<strike>delete this!</strike>"""
        expected = 'delete this!'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_wikilink(self):
        inp = "[[Apple]]"
        expected = 'Apple'
        self.assertEqual(expected, self._formatter.format(inp))

        inp = "[[Apple|Orange]]"
        expected = 'Orange'
        self.assertEqual(expected, self._formatter.format(inp))

        # Auto-pluralization
        inp = "[[Apple]]s"
        expected = 'Apples'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_ignore_images(self):
        inp = "[[File:My file.svg|thumb|left|Caption 12345]]"
        expected = ''
        self.assertEqual(expected, self._formatter.format(inp))

    def test_external_link(self):
        inp = "[https://example.com]"
        expected = 'https://example.com'
        self.assertEqual(expected, self._formatter.format(inp))

        inp = "[https://example.com example link]"
        expected = 'example link'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_full_article(self):
        inp = """\
This is a Wikitext snippet with '''bold''', ''italicized'', and '''''bold + italicized''''' text. It also includes links to [[another wiki page]] and an [https://en.wikipedia.org/w external URL].

This is the second paragraph.

==Heading==

This text after a heading will be ignored in summary mode.

=== Subsection ===

Hello world
"""
        expected = """\
This is a Wikitext snippet with bold, italicized, and bold + italicized text. It also includes links to another wiki page and an external URL.

This is the second paragraph.

## Heading

This text after a heading will be ignored in summary mode.

### Subsection

Hello world"""
        self.assertEqual(expected, self._formatter.format(inp))
        expected = """\
This is a Wikitext snippet with bold, italicized, and bold + italicized text. It also includes links to another wiki page and an external URL.

This is the second paragraph."""
        self.assertEqual(expected, self._formatter.format(inp, summary=True))

    def test_strip_newlines(self):
        """Test that > 2 newlines left by unsupported items are collapsed to 2"""
        # From https://en.wikipedia.org/wiki/Pear
        inp = """\
== References ==
{{Reflist|30em}}

== External links ==
[[Category:Flora of Asia]]
[[Category:Flora of Europe]]
[[Category:Flora of North Africa]]
[[Category:Fruits originating in Africa]]
<!--[[Category:Fruits originating in Europe]]-->
[[Category:Fruit trees]]
"""
        expected = """\
## References


## External links"""
        self.assertEqual(expected, self._formatter.format(inp))

class MarkdownFormatterTest(unittest.TestCase):
    def setUp(self):
        self._formatter = MarkdownFormatter(baseurl='https://en.wikipedia.org/w/api.php')

    def test_simple(self):
        inp = expected = 'Hello world'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_bold(self):
        inp = "'''Hello world'''"
        expected = '**Hello world**'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_italic(self):
        inp = "''Hello world''"
        expected = '*Hello world*'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_bold_italics_in_one_word(self):
        inp = "''Ab'''''cd'''<b>''efg''</b>"
        expected = '*Ab***cd*****efg***'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_strikethrough(self):
        inp = """<strike>delete this!</strike>"""
        expected = '~~delete this!~~'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_html_tags(self):
        inp = "Some of this ''content'' is <small>smaller</small> or <u>underlined</u>."
        expected = 'Some of this *content* is <small>smaller</small> or <u>underlined</u>.'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_wikilink(self):
        inp = "[[Apple]]"
        expected = '[Apple](https://en.wikipedia.org/w/index.php?title=Apple)'
        self.assertEqual(expected, self._formatter.format(inp))

        inp = "[[Apple|Orange]]"
        expected = '[Orange](https://en.wikipedia.org/w/index.php?title=Apple)'
        self.assertEqual(expected, self._formatter.format(inp))

        inp = "[[Page with space]]"
        expected = '[Page with space](https://en.wikipedia.org/w/index.php?title=Page+with+space)'
        self.assertEqual(expected, self._formatter.format(inp))

        # Auto-pluralization
        # FIXME: this is not the desired result, but it's tricky with a streaming approach...
        inp = "[[Apple]]s"
        expected = '[Apple](https://en.wikipedia.org/w/index.php?title=Apple)s'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_images(self):
        inp = "[[File:JPG Test.jpg|thumb|left|Caption 12345]]"
        expected = '![](https://en.wikipedia.org/w/index.php?title=Special%3AFilepath%2FJPG+Test.jpg)'
        self.assertEqual(expected, self._formatter.format(inp))

    def test_external_link(self):
        inp = "[https://example.com]"
        expected = 'https://example.com'
        self.assertEqual(expected, self._formatter.format(inp))

        inp = "[https://example.com example link]"
        expected = 'example link'
        self.assertEqual(expected, self._formatter.format(inp))

    # TODO add full article test

if __name__ == '__main__':
    unittest.main()
