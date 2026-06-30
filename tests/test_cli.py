import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from main import run_pipeline


class CliPipelineTest(unittest.TestCase):
    def test_cli_pipeline_writes_output(self):
        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "candidate.json"
            output = run_pipeline(
                Path("sample_inputs/recruiter.csv"),
                Path("sample_inputs/resume.pdf"),
                Path("config/default.json"),
                output_path,
            )
            self.assertTrue(output_path.exists())
            self.assertEqual(output["full_name"], "Aarav Sharma")
            self.assertIn("JavaScript", [skill["name"] for skill in output["skills"]])
            self.assertIsInstance(output["location"], dict)
            self.assertIn("linkedin", output["links"])


if __name__ == "__main__":
    unittest.main()
