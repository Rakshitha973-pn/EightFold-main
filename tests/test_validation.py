import unittest

from pydantic import ValidationError

from models.candidate import CanonicalCandidate
from validator.schema_validator import validate_canonical, validate_projected


class ValidationTest(unittest.TestCase):
    def test_validate_canonical_returns_candidate(self):
        candidate = CanonicalCandidate(candidate_id="123")
        self.assertEqual(validate_canonical(candidate).candidate_id, "123")

    def test_validate_projected_accepts_dict(self):
        self.assertEqual(validate_projected({"candidate_id": "123"}), {"candidate_id": "123"})

    def test_validate_projected_rejects_bad_default_shape(self):
        with self.assertRaises(ValidationError):
            validate_projected({
                "candidate_id": "123",
                "full_name": "Aarav Sharma",
                "emails": [],
                "phones": [],
                "location": "San Francisco, CA",
                "links": {},
                "headline": None,
                "years_experience": None,
                "skills": [],
                "experience": [],
                "education": [],
                "provenance": [],
                "overall_confidence": 0.5,
            })


if __name__ == "__main__":
    unittest.main()
