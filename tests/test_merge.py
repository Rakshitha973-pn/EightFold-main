import unittest

from merger.merge_engine import merge_candidates
from models.candidate import ParsedCandidate


class MergePolicyTest(unittest.TestCase):
    def test_resume_wins_single_value_conflict(self):
        csv = ParsedCandidate(source_name="recruiter.csv", source_type="csv")
        csv.add_field("headline", "Developer", "csv", 0.90)
        resume = ParsedCandidate(source_name="resume.pdf", source_type="resume")
        resume.add_field("headline", "Backend Engineer", "regex", 0.80)
        canonical = merge_candidates([csv, resume])
        self.assertEqual(canonical.headline, "Backend Engineer")

    def test_list_values_are_deduped(self):
        csv = ParsedCandidate(source_name="recruiter.csv", source_type="csv")
        csv.add_field("skills", ["Python", "SQL"], "csv", 0.90)
        resume = ParsedCandidate(source_name="resume.pdf", source_type="resume")
        resume.add_field("skills", ["Python", "Pandas"], "regex", 0.80)
        canonical = merge_candidates([csv, resume])
        self.assertEqual([skill.name for skill in canonical.skills], ["Python", "Pandas", "SQL"])

    def test_candidate_id_is_stable_for_same_inputs(self):
        csv = ParsedCandidate(source_name="recruiter.csv", source_type="csv")
        csv.add_field("full_name", "Aarav Sharma", "csv", 0.90)
        csv.add_field("emails", ["aarav@example.com"], "csv", 0.90)
        first = merge_candidates([csv])
        second = merge_candidates([csv])
        self.assertEqual(first.candidate_id, second.candidate_id)


if __name__ == "__main__":
    unittest.main()
