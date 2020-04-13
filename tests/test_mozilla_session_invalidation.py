import unittest

import mozilla_session_invalidation


class Mozilla_session_invalidationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = mozilla_session_invalidation.app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertIn('Welcome to Mozilla Session Invalidation', rv.data.decode())


if __name__ == '__main__':
    unittest.main()
