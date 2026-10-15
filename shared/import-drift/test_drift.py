import csv
import io
from pathlib import Path
import tempfile
import unittest

import drift


class DriftTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'src'
        self.root.mkdir()

    def save(self, name, text):
        path = self.base / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_real_change_and_no_execution(self):
        source = self.root / 'main.py'
        source.write_text('raise RuntimeError("must never execute")\nimport os\n')
        before, _ = drift.snapshot(self.root)
        source.write_text('raise RuntimeError("must never execute")\nimport json\n')
        after, _ = drift.snapshot(self.root)
        result = drift.compare(self.save('a.csv', before), self.save('b.csv', after))
        self.assertEqual(result['summary']['changed'], 1)
        self.assertIn('external_imports', result['changed'][0]['fields'])

    def test_import_line_shifts_equal_and_local_links_present(self):
        (self.root / 'helper.py').write_text('')
        source = self.root / 'main.py'
        source.write_text('import helper\n')
        before, _ = drift.snapshot(self.root)
        source.write_text('\n\nimport helper\nimport helper\n')
        after, _ = drift.snapshot(self.root)
        self.assertEqual(before, after)
        rows = list(csv.DictReader(io.StringIO(after)))
        self.assertEqual(rows[1]['local_imports'], '["helper"]')

    def test_parse_error_retained(self):
        (self.root / 'broken.py').write_text('def (\n')
        text, report = drift.snapshot(self.root)
        self.assertEqual(report['summary']['issue_count'], 1)
        self.assertIn('parse_error', text)

    def test_duplicate_keys_ambiguous(self):
        (self.root / 'main.py').write_text('')
        text, _ = drift.snapshot(self.root)
        duplicated = text + text.splitlines(keepends=True)[1]
        result = drift.compare(self.save('a.csv', text), self.save('b.csv', duplicated))
        self.assertFalse(result['complete'])
        self.assertEqual(result['summary']['ambiguous_keys'], 1)

    def test_schema_and_outside_path_rejected(self):
        wrong = self.save('wrong.csv', 'module,x\na,b\n')
        with self.assertRaises(ValueError):
            drift.compare(wrong, wrong)
        with self.assertRaises(ValueError):
            drift.workspace_path(Path.cwd().parent / 'outside')

    def test_module_package_collision_fails_explicitly(self):
        (self.root / 'pkg').mkdir()
        (self.root / 'pkg.py').write_text('import os\n')
        (self.root / 'pkg' / '__init__.py').write_text('import json\n')
        with self.assertRaisesRegex(ValueError, 'module name collision'):
            drift.snapshot(self.root)


if __name__ == '__main__':
    unittest.main()
