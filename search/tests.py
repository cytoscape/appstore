"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import sys
from unittest.mock import MagicMock

# Mock external dependencies
sys.modules['xapian'] = MagicMock()

mock_conf = MagicMock()
mock_conf.XAPIAN_INDICES_DIR = "/tmp"
sys.modules['conf'] = MagicMock()
sys.modules['conf.xapian'] = mock_conf

from django.test import TestCase
from unittest.mock import patch, MagicMock
from search.views import _xapian_search


class DummyModelA:
    __name__ = "ModelA"
    search_key = "id"


class DummyModelB:
    __name__ = "ModelB"
    search_key = "id"


class SearchTestCase(TestCase):

    @patch("search.views.get_object_or_none")
    def test_search_returns_multiple_models(self, mock_get_obj):

        from search import views

        # Mock matches
        mock_match_1 = MagicMock()
        mock_match_1.document.get_data.return_value = "1"

        mock_match_2 = MagicMock()
        mock_match_2.document.get_data.return_value = "2"

        # Mock enquire behavior
        mock_enquire_1 = MagicMock()
        mock_enquire_1.get_mset.return_value = [mock_match_1]

        mock_enquire_2 = MagicMock()
        mock_enquire_2.get_mset.return_value = [mock_match_2]

        mock_qp = MagicMock()

        mock_db_1 = MagicMock()
        mock_db_1.get_doccount.return_value = 1

        mock_db_2 = MagicMock()
        mock_db_2.get_doccount.return_value = 1

        # Inject fake Xapian data
        views.Xapian_Enquires = {
            DummyModelA: (mock_db_1, mock_enquire_1, mock_qp),
            DummyModelB: (mock_db_2, mock_enquire_2, mock_qp),
        }

        # Mock object fetching
        mock_get_obj.side_effect = lambda model, **kwargs: {
            "model": model.__name__,
            "id": kwargs.get("id")
        }

        results = _xapian_search("test-query")

        # Assertions
        self.assertIn("DummyModelA", results)
        self.assertIn("DummyModelB", results)

        self.assertEqual(len(results["DummyModelA"]), 1)
        self.assertEqual(len(results["DummyModelB"]), 1)