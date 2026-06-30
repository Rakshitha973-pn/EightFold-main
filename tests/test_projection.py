import unittest

from models.candidate import CanonicalCandidate, SkillEntry
from projection.projector import project_candidate


class ProjectionTest(unittest.TestCase):
    def test_projection_renames_and_hides_provenance(self):
        candidate = CanonicalCandidate(candidate_id="123", full_name="Aarav Sharma", overall_confidence=0.9)
        output = project_candidate(candidate, {
            "fields": ["id", "name", "provenance"],
            "map_fields": {"id": "candidate_id", "name": "full_name"},
            "rename_fields": {"id": "candidateId", "name": "fullName"},
            "include_provenance": False,
            "missing_value_strategy": "null",
        })
        self.assertEqual(output, {"candidateId": "123", "fullName": "Aarav Sharma"})

    def test_projection_supports_assignment_style_paths(self):
        candidate = CanonicalCandidate(
            candidate_id="123",
            full_name="Aarav Sharma",
            emails=["aarav@example.com"],
            phones=["+16502530000"],
            skills=[SkillEntry(name="JavaScript", confidence=0.8, sources=["resume.pdf"])],
            overall_confidence=0.9,
        )
        output = project_candidate(candidate, {
            "fields": [
                {"path": "primary_email", "from": "emails[0]", "type": "string", "required": True},
                {"path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical"},
            ],
            "include_provenance": False,
        })
        self.assertEqual(output["primary_email"], "aarav@example.com")
        self.assertEqual(output["skills"], ["JavaScript"])


if __name__ == "__main__":
    unittest.main()
