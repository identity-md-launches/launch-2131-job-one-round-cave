"""Behavioral checks for the query diagnosis companion."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("query_diagnose", Path(__file__).with_name("diagnose.py"))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class DiagnoseTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / "test" / "scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "docs"
        self.root.mkdir()
        (self.root / "a.md").write_text("ZTO token details.\n", encoding="utf-8")
        (self.root / "b.md").write_text("IMD pool reference.\n", encoding="utf-8")
        self.index = tool.search.build_index(self.root)

    def test_strict_and_relaxed_citations_are_live_verified(self):
        result = tool.diagnose(self.index, self.root, "IMD pool absent")
        self.assertEqual(result["strict_hit_count"], 0)
        by_term = {item["omitted_term"]: item for item in result["relaxations"]}
        self.assertEqual(by_term["absent"]["hits"][0]["citation"], "b.md:1-1")
        self.assertTrue(by_term["absent"]["hits"][0]["source_verified"])
        self.assertEqual(by_term["pool"]["hits"], [])

    def test_existing_strict_hits_remain_present(self):
        result = tool.diagnose(self.index, self.root, "ZTO token")
        self.assertEqual(result["strict_hits"][0]["citation"], "a.md:1-1")
        self.assertTrue(result["strict_hits"][0]["source_verified"])

    def test_rejects_empty_large_query_and_bad_limit(self):
        for query in ("!!!", " ".join(f"t{i}" for i in range(13))):
            with self.subTest(query=query), self.assertRaises(tool.search.SearchError):
                tool.diagnose(self.index, self.root, query)
        with self.assertRaisesRegex(tool.search.SearchError, "limit"):
            tool.diagnose(self.index, self.root, "ZTO", limit=11)

    def test_demo_uses_real_inherited_sources(self):
        result = tool.demo()
        self.assertEqual(result["strict_hit_count"], 0)
        finality = next(item for item in result["relaxations"]
                        if item["omitted_term"] == "finality")
        self.assertGreater(finality["hit_count"], 0)
        self.assertTrue(all(hit["source_verified"] for hit in finality["hits"]))


if __name__ == "__main__":
    unittest.main()
