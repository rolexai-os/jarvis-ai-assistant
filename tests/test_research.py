import unittest
from jarvis.research import _ResultParser


class ResearchParserTests(unittest.TestCase):
    def test_parses_result_title_and_url(self):
        parser = _ResultParser()
        parser.feed('<div class="result"><a class="result__a" href="https://example.com/page">Example result</a><a class="result__snippet">A short useful snippet.</a></div>')
        self.assertEqual(len(parser.results), 1)
        self.assertEqual(parser.results[0]["title"], "Example result")
        self.assertEqual(parser.results[0]["url"], "https://example.com/page")
        self.assertEqual(parser.results[0]["snippet"], "A short useful snippet.")

    def test_resolves_duckduckgo_redirect_link(self):
        parser = _ResultParser()
        parser.feed('<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Farticle">Article</a>')
        self.assertEqual(parser.results[0]["url"], "https://example.org/article")


if __name__ == "__main__":
    unittest.main()
