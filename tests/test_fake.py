import unittest

import pytest
from fake_useragent import VERSION, FakeUserAgent, UserAgent, settings


class TestFake(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _probe(self, ua):
        ua.edge
        ua.google
        ua.chrome
        ua.googlechrome
        ua.google_chrome
        ua["google chrome"]
        ua.firefox
        ua.ff
        ua.safari
        ua.random
        ua["random"]

    def test_fake_init(self):
        ua = UserAgent()

        self.assertTrue(ua.chrome)
        self.assertIsInstance(ua.chrome, str)
        self.assertTrue(ua.edge)
        self.assertIsInstance(ua.edge, str)
        self.assertTrue(ua["internet explorer"])
        self.assertIsInstance(ua["internet explorer"], str)
        self.assertTrue(ua.firefox)
        self.assertIsInstance(ua.firefox, str)
        self.assertTrue(ua.safari)
        self.assertIsInstance(ua.safari, str)
        self.assertTrue(ua.random)
        self.assertIsInstance(ua.random, str)

    def test_fake_user_agent_browsers(self):
        ua = UserAgent()

        self._probe(ua)

    def test_fake_data_browser_type(self):
        ua = UserAgent()
        assert isinstance(ua.data_browsers, list)

    def test_fake_fallback(self):
        fallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

        ua = UserAgent()
        self.assertEqual(ua.non_existing, fallback)
        self.assertEqual(ua["non_existing"], fallback)

    def test_fake_fallback_str_types(self):
        with pytest.raises(AssertionError):
            UserAgent(fallback=True)

    def test_fake_browser_str_or_list_types(self):
        with pytest.raises(AssertionError):
            UserAgent(browsers=52)

    def test_fake_os_str_or_list_types(self):
        with pytest.raises(AssertionError):
            UserAgent(os=23.4)

    def test_fake_percentage_float_types(self):
        with pytest.raises(AssertionError):
            UserAgent(min_percentage="")

    def test_fake_safe_attrs_iterable_str_types(self):
        with pytest.raises(AssertionError):
            UserAgent(safe_attrs={})

        with pytest.raises(AssertionError):
            UserAgent(safe_attrs=[66])

    def test_fake_safe_attrs(self):
        ua = UserAgent(safe_attrs=("__injections__",))

        with pytest.raises(AttributeError):
            ua.__injections__

    def test_fake_version(self):
        assert VERSION == settings.__version__

    def test_fake_aliases(self):
        assert FakeUserAgent is UserAgent
