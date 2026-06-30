import unittest

from normalizers.skills import normalize_skills


class SkillNormalizationTest(unittest.TestCase):
    def test_skill_synonyms_are_canonicalized_and_deduped(self):
        self.assertEqual(
            normalize_skills(["cpp", "C plus plus", "js", "Java Script"]),
            ["C++", "JavaScript"],
        )


if __name__ == "__main__":
    unittest.main()
