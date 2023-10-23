# pywikifetch

**pywikifetch** is a library to fetch and parse content from MediaWiki instances. It currently supports plain text and Markdown as output, and works on any MediaWiki instance (Wikipedia, wiki.gg, Fandom, etc.). API detection is automatic, so you can pass in something like `en.wikipedia.org` instead of configuring the full path to the [MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page) which varies by site.

```
usage: wikifetch [-h] [-s] [-v] [-r] [-m] [-V] base_url query

Fetch an article from a MediaWiki site

positional arguments:
  base_url        Wiki base URL, e.g. "en.wikipedia.org"
  query           Search query

options:
  -h, --help      show this help message and exit
  -s, --summary   Fetch only the first paragraph of a page
  -v, --verbose   Show verbose debug info
  -r, --raw       Print raw wikitext instead of formatting (overrides -s and -m)
  -m, --markdown  Show results in Markdown instead of plain text
  -V, --version   show program's version number and exit
```

## Samples

(Wikipedia samples are licensed under [CC-BY-SA 4.0](https://en.wikipedia.org/wiki/Wikipedia:Text_of_the_Creative_Commons_Attribution-ShareAlike_4.0_International_License))

### Plain text mode

```
$ wikifetch en.wikipedia.org 'Python (programming language)' -s
Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.

Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured (particularly procedural), object-oriented and functional programming. It is often described as a "batteries included" language due to its comprehensive standard library.

Guido van Rossum began working on Python in the late 1980s as a successor to the ABC programming language and first released it in 1991 as Python0.9.0. Python2.0 was released in 2000. Python3.0, released in 2008, was a major revision not completely backward-compatible with earlier versions. Python2.7.18, released in 2020, was the last release of Python2.

Python consistently ranks as one of the most popular programming languages.
https://en.wikipedia.org/wiki/Python_(programming_language)
```

### Markdown

`$ wikifetch en.wikipedia.org 'Python (programming language)' -s -m`

**Python** is a [high-level](https://en.wikipedia.org/w/index.php?title=High-level+programming+language), [general-purpose programming language](https://en.wikipedia.org/w/index.php?title=general-purpose+programming+language). Its design philosophy emphasizes [code readability](https://en.wikipedia.org/w/index.php?title=code+readability) with the use of [significant indentation](https://en.wikipedia.org/w/index.php?title=off-side+rule).

Python is [dynamically typed](https://en.wikipedia.org/w/index.php?title=type+system%23DYNAMIC) and [garbage-collected](https://en.wikipedia.org/w/index.php?title=garbage+collection+%28computer+science%29). It supports multiple [programming paradigm](https://en.wikipedia.org/w/index.php?title=programming+paradigm)s, including [structured](https://en.wikipedia.org/w/index.php?title=structured+programming) (particularly [procedural](https://en.wikipedia.org/w/index.php?title=procedural+programming)), [object-oriented](https://en.wikipedia.org/w/index.php?title=object-oriented+programming) and [functional programming](https://en.wikipedia.org/w/index.php?title=functional+programming). It is often described as a "batteries included" language due to its comprehensive [standard library](https://en.wikipedia.org/w/index.php?title=standard+library).

[Guido van Rossum](https://en.wikipedia.org/w/index.php?title=Guido+van+Rossum) began working on Python in the late 1980s as a successor to the [ABC programming language](https://en.wikipedia.org/w/index.php?title=ABC+%28programming+language%29) and first released it in 1991 as Python0.9.0. Python2.0 was released in 2000. Python3.0, released in 2008, was a major revision not completely [backward-compatible](https://en.wikipedia.org/w/index.php?title=backward+compatibility) with earlier versions. Python2.7.18, released in 2020, was the last release of Python2.

Python consistently ranks as one of the most popular programming languages.
https://en.wikipedia.org/wiki/Python_(programming_language)

