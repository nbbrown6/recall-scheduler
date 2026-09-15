import unittest

from recall_scheduler.stats import summarize, quality_passed


class SummarizeTests(unittest.TestCase):
    def test_empty_sequence(self):
        stats = summarize([])
        self.assertEqual(stats.total, 0)
        self.assertEqual(stats.passed, 0)
        self.assertEqual(stats.retention_rate, 0.0)
        self.assertEqual(stats.current_streak, 0)
        self.assertEqual(stats.longest_streak, 0)

    def test_all_passes(self):
        stats = summarize([True, True, True])
        self.assertEqual(stats.total, 3)
        self.assertEqual(stats.passed, 3)
        self.assertEqual(stats.retention_rate, 1.0)
        self.assertEqual(stats.current_streak, 3)
        self.assertEqual(stats.longest_streak, 3)

    def test_all_fails(self):
        stats = summarize([False, False])
        self.assertEqual(stats.retention_rate, 0.0)
        self.assertEqual(stats.current_streak, 0)
        self.assertEqual(stats.longest_streak, 0)

    def test_current_streak_ends_at_last_fail(self):
        stats = summarize([True, True, False, True])
        self.assertEqual(stats.total, 4)
        self.assertEqual(stats.passed, 3)
        self.assertEqual(stats.retention_rate, 0.75)
        self.assertEqual(stats.current_streak, 1)
        self.assertEqual(stats.longest_streak, 2)

    def test_longest_streak_not_at_end(self):
        stats = summarize([True, True, True, False, True])
        self.assertEqual(stats.current_streak, 1)
        self.assertEqual(stats.longest_streak, 3)

    def test_accepts_any_iterable(self):
        stats = summarize(x % 2 == 0 for x in range(4))
        self.assertEqual(stats.total, 4)
        self.assertEqual(stats.passed, 2)


class QualityPassedTests(unittest.TestCase):
    def test_default_threshold(self):
        self.assertFalse(quality_passed(0))
        self.assertFalse(quality_passed(2))
        self.assertTrue(quality_passed(3))
        self.assertTrue(quality_passed(5))

    def test_custom_threshold(self):
        self.assertFalse(quality_passed(3, threshold=4))
        self.assertTrue(quality_passed(4, threshold=4))


if __name__ == "__main__":
    unittest.main()
