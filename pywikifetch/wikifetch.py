import argparse
import asyncio
import logging
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from .version import __version__
from .wikitext_formatter import MarkdownFormatter, PlainTextFormatter

logger = logging.getLogger('wikifetch')

__all__ = [
    'WikifetchError',
    'MediaWikiAPIError',
    'NoSearchResultsError',
    'Wiki',
]

class WikifetchError(Exception):
    """Base class for exceptions raised by wikifetch"""

class MediaWikiAPIError(WikifetchError):
    """Represents a MediaWiki API error"""
    # TODO: turn error details into actual fields

class NoSearchResultsError(WikifetchError):
    pass

class Wiki():
    """
    Instantiates a MediaWiki fetcher for the given base URL.
    """
    _DEFAULT_HEADERS = {
        'User-Agent': f'Mozilla/5.0 (compatible) pywikifetch/{__version__}'
    }

    def __init__(self, baseurl, headers=None, bs4_parser='html.parser', formatter_class=PlainTextFormatter):
        self._input_baseurl = baseurl
        self.baseurl = None
        self.http_headers = headers or self._DEFAULT_HEADERS
        self.bs4_parser = bs4_parser
        self.formatter_class = formatter_class

        self._session = None
        self.formatter = None

    def _get_bs4(self, *args, **kwargs):
        return BeautifulSoup(*args, features=self.bs4_parser, **kwargs)

    async def _guess_api_url(self, home_url):
        async with self._session.get(home_url) as resp:
            homepage = await resp.text()
            soup = self._get_bs4(homepage)
            for link in soup.find_all('link'):
                # Find the first <link> tag that points to an api.php
                href = link.attrs['href']
                url_parts = urllib.parse.urlparse(href)
                if 'api.php' in url_parts.path.lower():
                    # Remove the API query from this URL
                    new_url_parts = url_parts._replace(query='')
                    new_href = urllib.parse.urlunparse(new_url_parts)
                    new_baseurl = urllib.parse.urljoin(home_url, new_href)
                    logger.info('_guess_api_url: setting baseurl %r -> %r', home_url, new_href)
                    return new_baseurl
            raise MediaWikiAPIError(
                f"Could not find MediaWiki API endpoint from base URL {self.baseurl!r} - "
                "try passing in the full path to the wiki's api.php")

    async def _init(self):
        """
        On first run, try to find the api.php location for a wiki and update self.baseurl accordingly
        """
        baseurl = self._input_baseurl
        url_parts = urllib.parse.urlparse(baseurl)
        if not url_parts.scheme:
            baseurl = 'https://' + baseurl
        if 'api.php' not in url_parts.path.lower():
            # No api.php passed into baseurl: fetch the homepage and try to find it there
            baseurl = await self._guess_api_url(baseurl)

        self.baseurl = baseurl
        self.formatter = self.formatter_class(self)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(raise_for_status=True)
        if not self.baseurl:
            await self._init()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self._session.close()
        self._session = None

    async def _mw_api_call(self, params):
        """Performs an async GET call to the MediaWiki API."""
        url = f"{self.baseurl}?{params}"

        async with self._session.get(url) as resp:
            api_data = await resp.json()

        if isinstance(api_data, dict):
            if error := api_data.get('error'):
                error_code = error['code']
                error_info = error['info']
                raise MediaWikiAPIError(f"MediaWiki API Error: {error_code} - {error_info} - {url}")
        return api_data

    async def fetch(self, title, summary=False, raw=False):
        """Return the plain-text formatted content of a page.

        If summary is True, only return the first paragraph instead of the whole page."""
        params = urllib.parse.urlencode({
            'action': 'parse',
            'page': title,
            'prop': 'wikitext|headhtml',
            'formatversion': 2,
            'format': 'json',
            'redirects': True
        })
        api_data = await self._mw_api_call(params)

        page_title = api_data['parse']['title']
        content = api_data['parse']['wikitext']
        html_head = api_data['parse']['headhtml']

        if raw:
            text = content
        else:
            text = self.formatter.format(content, summary=summary)

        soup = self._get_bs4(html_head)
        if canonical_link := soup.find('link', rel='canonical'):
            # Wikipedia
            url = canonical_link.attrs['href']
        elif og_url := soup.find('meta', property='og:url'):
            # wiki.gg, Fandom
            url = og_url.attrs['content']
        else:
            # Use generic MediaWiki link as fallback (this doesn't look as nice)
            url = self.formatter.get_page_url(page_title)

        return (text, url)

    async def search(self, searchquery):
        """Return page titles from a MediaWiki search."""
        params = urllib.parse.urlencode({
            'action': 'opensearch',
            'search': searchquery,
            'format': 'json',
        })
        api_data = await self._mw_api_call(params)

        search_result_titles = api_data[1]
        if not search_result_titles:
            raise NoSearchResultsError(f"No search results for {searchquery!r}")
        return search_result_titles

async def _main():
    parser = argparse.ArgumentParser( description="Fetch an article from a MediaWiki site")
    parser.add_argument('base_url', help='Wiki base URL, e.g. "en.wikipedia.org"')
    parser.add_argument('query', help='Search query')
    parser.add_argument('-s', '--summary', action='store_true', help='Fetch only the first paragraph of a page')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose debug info')
    parser.add_argument('-r', '--raw', action='store_true', help='Print raw wikitext instead of formatting '
                        '(overrides -s and -m)')
    parser.add_argument('-m', '--markdown', action='store_true', help='Show results in Markdown instead of plain text')
    parser.add_argument('-V', '--version', action='version', version=f'pywikifetch {__version__}')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    formatter_class = MarkdownFormatter if args.markdown else PlainTextFormatter
    async with Wiki(args.base_url, formatter_class=formatter_class) as wiki:
        search_results = await wiki.search(args.query)
        logger.info("Search results: %s", ', '.join(search_results))
        text, url = await wiki.fetch(search_results[0], summary=args.summary, raw=args.raw)
        print(text)
        print(url)

def main():
    asyncio.run(_main())

if __name__ == '__main__':
    main()
