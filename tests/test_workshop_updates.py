"""Las respuestas y miniaturas antiguas no pueden modificar la búsqueda actual."""
import types
import unittest
from unittest.mock import Mock, patch
from wpelib.workshop_window import WorkshopBrowserWindow as Browser


class SearchUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.window = types.SimpleNamespace(_search_generation=2, current_page=1,
                    page_cache={}, prefetching={2}, cards={}, status_label=Mock())

    def test_old_search_cannot_replace_results_or_cache(self):
        Browser._populate_results(self.window, 99, [{'publishedfileid': '1'}], 1, 1)
        self.assertEqual(self.window.page_cache, {})

    def test_old_prefetch_cannot_contaminate_cache(self):
        Browser._store_prefetched(self.window, 2, 99, [], 1)
        self.assertEqual(self.window.page_cache, {})
        self.assertEqual(self.window.prefetching, {2})

    def test_old_error_cannot_replace_current_status(self):
        Browser._search_error(self.window, 1, 1, 'old error')
        self.window.status_label.set_text.assert_not_called()
        Browser._search_error(self.window, 2, 1, 'current error')
        self.window.status_label.set_text.assert_called_once_with('current error')

    def test_thumbnail_worker_stops_after_new_search(self):
        with patch('wpelib.workshop_window.download_workshop_thumb') as download:
            Browser._thumbs_thread(self.window, [{'publishedfileid': '1', 'preview_url': 'https://example.test'}], 1, 1)
            download.assert_not_called()

    def test_old_thumbnail_cannot_replace_new_card(self):
        card = Mock()
        self.window.cards['1'] = card
        Browser._set_thumb(self.window, '1', '/no/such/image', 1, 1)
        card.set_pixbuf.assert_not_called()

    def test_cancel_invalidates_pending_updates(self):
        Browser._cancel_searches(self.window)
        self.assertEqual(self.window._search_generation, 3)
