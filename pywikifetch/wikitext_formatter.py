#!/usr/bin/env python3
import argparse
import functools
import io
import itertools
import logging
import re
import sys
import urllib.parse

import mwparserfromhell

logger = logging.getLogger('wikifetch.formatter')

class BaseFormatter():
    def __init__(self, parent):
        self.parent = parent
        self.list_level = 0

    # FIXME: this can probably move to the parent class
    def get_page_url(self, page):
        return urllib.parse.urljoin(self.parent.baseurl, 'index.php?' + urllib.parse.urlencode({
            'title': page
        }))

    def format_node(self, node):
        """Format a Wikitext node"""
        raise NotImplementedError

    def format_list(self):
        """Display the markup for a list once all consecutive list tokens have been parsed

        The current list level is stored in self.list_level"""
        raise NotImplementedError

    def pre_format_node(self, node):
        """Function called before each node is formatted"""
        is_list_tag = isinstance(node, mwparserfromhell.nodes.tag.Tag) and str(node.tag) == 'li'
        if self.list_level and not is_list_tag:
            logging.debug('Ending list at level %s', self.list_level)
            yield from self.format_list()
            self.list_level = 0

    def format(self, wikitext: str, summary: bool = False) -> str:
        """Entrypoint to the formatter"""
        markup = mwparserfromhell.parse(wikitext)
        strbuf = io.StringIO()

        for node in markup.nodes:
            logger.debug('format: %s %r', type(node), node)
            if summary and isinstance(node, mwparserfromhell.nodes.heading.Heading):
                break
            for output in itertools.chain(self.pre_format_node(node), self.format_node(node)):
                assert isinstance(output, str), f'expected str, got {type(output)} for node {node}'
                strbuf.write(output)
        s = strbuf.getvalue()
        # Limit consecutive newlines to 2 in a row, as we can end up with a lot of
        # unused space otherwise from deleting unsupported & invisible items
        s = re.sub(r'\s+?\n\s+?\n\s+', r'\n\n', s)
        return s.strip()

class PlainTextFormatter(BaseFormatter):
    """Formats Wikitext as plain text"""

    @functools.singledispatchmethod
    def format_node(self, node):
        """Stub for unhandled Wikitext node types"""
        logger.info("Skipping unknown node of type %s: %r", type(node), node)
        return
        yield

    @format_node.register
    def format_wikicode(self, node: mwparserfromhell.wikicode.Wikicode):
        for child_node in node.nodes:
            yield from self.format_node(child_node)

    @format_node.register
    def format_text(self, node: mwparserfromhell.nodes.text.Text):
        yield str(node)

    def increment_list_counter(self, node: mwparserfromhell.nodes.text.Text):
        # Lists are parsed into a sequence of consecutive 'li' tags
        # To properly track the list level we need to count how many of these we see in a row.
        # Of course, this is stateful, but oh well...
        if str(node.tag) == 'li':
            self.list_level += 1

    # Strip currently unsupported features
    _html_tags_remove = {
        'gallery',
        'ref',
    }
    @format_node.register
    def format_tag(self, node: mwparserfromhell.nodes.tag.Tag):
        self.increment_list_counter(node)
        if str(node.tag) in self._html_tags_remove:
            return
        yield from self.format_node(node.contents)

    @format_node.register
    def format_wikilink(self, node: mwparserfromhell.nodes.wikilink.Wikilink):
        target = str(node.title)
        if target.startswith(('File:', 'Category:')):
            # Ignore image / file embeds for plain text mode
            # Categories are invisible in the page content
            return
        # Return the displayed text for the link, or the title of the target page if none is set
        link_text = node.text or node.title
        yield from self.format_node(link_text)

    @format_node.register
    def format_external_link(self, node: mwparserfromhell.nodes.external_link.ExternalLink):
        link_text = node.title or node.url
        yield from self.format_node(link_text)

    ### Markdown-esque formatters
    @format_node.register
    def format_heading(self, node: mwparserfromhell.nodes.heading.Heading):
        heading_hashtags = '#' * node.level
        yield heading_hashtags + ' '
        # Strip spaces around the heading text. Technically this isn't necessary, but makes the output cleaner
        heading_text = ''.join(self.format_node(node.title))
        yield heading_text.strip()

    def format_list(self):
        yield '  ' * (self.list_level-1) + '*'

class MarkdownFormatter(PlainTextFormatter):
    """Formats Wikitext as Markdown"""

    # This registers a new singledispatchmethod for just the subclass, with unhandled calls passed into the superclass'
    # method. This works around singledispatchmethod not natively supporting subclasses:
    # https://github.com/python/cpython/issues/80638
    @functools.singledispatchmethod
    def format_node(self, node):
        return super().format_node(node)

    _tag_to_markdown = {
        'b': '**',
        # "_" is also accepted for italics, EXCEPT inside words. So using * is more general
        'i': '*',
        'strike': '~~',
    }
    _end_tag_to_markdown = _tag_to_markdown
    _html_tags_map = {}
    @format_node.register
    def format_tag(self, node: mwparserfromhell.nodes.tag.Tag):
        if str(node.tag) in self._html_tags_remove:
            return
        self.increment_list_counter(node)
        tag_output = None
        if markdown_tag := self._tag_to_markdown.get(str(node.tag)):
            yield markdown_tag
        elif not node.wiki_markup:  # keep HTML tags as is (for the most part)
            tag_output = str(node.tag)
            tag_output = self._html_tags_map.get(tag_output, tag_output)
            yield f'<{tag_output}>'
        yield from self.format_node(node.contents)
        if markdown_tag := self._end_tag_to_markdown.get(str(node.tag)):
            yield markdown_tag
        elif not node.wiki_markup and not node.self_closing:
            yield f'</{tag_output}>'

    @format_node.register
    def format_wikilink(self, node: mwparserfromhell.nodes.wikilink.Wikilink):
        target = str(node.title)
        is_image = 'File:' in target
        if target.startswith('Category:'):
            # Categories are invisible in the page content
            return

        # Return the displayed text for the link, or the title of the target page if none is set
        link_text = node.text or node.title
        formatted_link_text = self.format_node(link_text)
        if not self.parent.baseurl:
            if not is_image:
                # No baseurl provided, drop the link
                yield from formatted_link_text
            return

        if is_image:
            # TODO: support alt text
            # TODO: allow adjusting desired image preview size
            # ![](https://example.com/blah.png hover text)
            image_page_title = target.replace('File:', 'Special:Filepath/')
            url = self.get_page_url(image_page_title)
            yield f'![]({url})'
            return

        url = self.get_page_url(node.title)
        # [link](text)
        yield '['
        yield from formatted_link_text
        yield f']({url})'

    @format_node.register
    def format_external_link(self, node: mwparserfromhell.nodes.external_link.ExternalLink):
        link_text = node.title or node.url
        yield from self.format_node(link_text)

def main():
    parser = argparse.ArgumentParser(
        description="Render Wikitext as plain text or Markdown")
    parser.add_argument('-s', '--summary', action='store_true', help='Fetch only the first paragraph of a page')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    formatter = PlainTextFormatter(None)
    result = formatter.format(sys.stdin.read(), summary=args.summary)
    print(result)

if __name__ == '__main__':
    main()
