"""Offline behavioral checks, creating transient fixtures beside this file."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import reconcile as tool


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def compare(self, before, after, keys=('id',), ignore=()):
        self.b = self.base / 'before.csv'
        self.a = self.base / 'after.csv'
        self.b.write_bytes(before.encode('utf-8'))
        self.a.write_bytes(after.encode('utf-8'))
        return tool.reconcile(self.b, self.a, keys, ignore)

    def test_reordering_rows_and_columns_is_equal(self):
        r = self.compare('id,value\nb,2\na,1\n', 'value,id\n1,a\n2,b\n')
        self.assertTrue(r['equal'])
        self.assertEqual(r['summary']['unchanged_on_common_columns'], 2)

    def test_add_remove_change_and_exact_strings(self):
        r = self.compare('id,value\na,01\nb,x\nc,same\n', 'id,value\na,1\nc,same\nd,new\n')
        self.assertEqual(r['summary'], {'before_records': 3, 'after_records': 3, 'added': 1,
            'removed': 1, 'changed': 1, 'unchanged_on_common_columns': 1, 'ambiguous_keys': 0})
        self.assertEqual(r['changed'][0]['fields']['value'], {'before': '01', 'after': '1'})
        self.assertEqual(r['added'][0]['key'], {'id': 'd'})
        self.assertEqual(r['removed'][0]['key'], {'id': 'b'})

    def test_duplicate_key_never_silently_overwrites_or_pairs(self):
        r = self.compare('id,value\na,1\na,2\nb,3\n', 'id,value\na,1\nb,3\n')
        self.assertFalse(r['complete'])
        self.assertFalse(r['equal'])
        self.assertEqual([x['record'] for x in r['ambiguous'][0]['before']], [2, 3])
        self.assertEqual(r['changed'], [])
        self.assertEqual(r['summary']['unchanged_on_common_columns'], 1)

    def test_duplicates_on_candidate_only_still_ambiguous(self):
        r = self.compare('id\n', 'id\na\na\n')
        self.assertEqual(r['summary']['ambiguous_keys'], 1)
        self.assertEqual(r['added'], [])

    def test_composite_keys_do_not_concatenate_collisions(self):
        r = self.compare('x,y,v\nab,c,1\na,bc,2\n', 'x,y,v\na,bc,3\nab,c,1\n', ('x', 'y'))
        self.assertEqual(r['changed'][0]['key'], {'x': 'a', 'y': 'bc'})
        self.assertEqual(r['summary']['ambiguous_keys'], 0)

    def test_multiline_quoted_unicode_and_bom(self):
        r = self.compare('\ufeffid,note\nα,"one, two\nthree"\n', 'id,note\nα,"one, two\nthree"\n')
        self.assertTrue(r['equal'])

    def test_schema_changes_are_not_claimed_equal(self):
        r = self.compare('id,old\na,x\n', 'id,new\na,y\n')
        self.assertFalse(r['equal'])
        self.assertEqual(r['schema'], {'added_columns': ['new'], 'removed_columns': ['old']})
        self.assertEqual(r['changed'], [])

    def test_ignored_columns(self):
        r = self.compare('id,time\na,old\n', 'id,time\na,new\n', ignore=('time',))
        self.assertTrue(r['equal'])
        r = self.compare('id,time\n', 'id\na\n', ignore=('time',))
        self.assertEqual(r['added'][0]['values'], {'id': 'a'})

    def test_empty_tables_with_headers(self):
        self.assertTrue(self.compare('id,v\n', 'id,v\n')['equal'])

    def test_blank_key_is_literal_and_duplicates_are_ambiguous(self):
        r = self.compare('id,v\n,x\n', 'id,v\n,y\n')
        self.assertEqual(r['changed'][0]['key'], {'id': ''})

    def test_invalid_inputs(self):
        for text in ['', 'id,id\na,b\n', 'id,\na,b\n', 'v\nx\n',
                     'id,v\na\n', 'id\na,b\n', 'id,v\na,"unclosed\n', 'id\n\n']:
            with self.subTest(text=text), self.assertRaises(tool.InputError):
                self.compare(text, 'id,v\na,b\n')

    def test_invalid_options(self):
        for keys, ignore in [(('id', 'id'), ()), (('id',), ('id',)), (('id',), ('typo',))]:
            with self.subTest(keys=keys, ignore=ignore), self.assertRaises(tool.InputError):
                self.compare('id,v\na,b\n', 'id,v\na,b\n', keys, ignore)

    def test_row_and_byte_bounds(self):
        original_bytes, original_rows = tool.MAX_BYTES, tool.MAX_ROWS
        try:
            tool.MAX_BYTES = 8
            with self.assertRaises(tool.InputError):
                self.compare('id\nlongvalue\n', 'id\n')
            tool.MAX_BYTES = original_bytes
            tool.MAX_ROWS = 1
            with self.assertRaises(tool.InputError):
                self.compare('id\na\nb\n', 'id\n')
        finally:
            tool.MAX_BYTES, tool.MAX_ROWS = original_bytes, original_rows

    def test_non_utf8_is_rejected(self):
        p = self.base / 'invalid.csv'
        p.write_bytes(b'id\n\xff\n')
        with self.assertRaises(tool.InputError):
            tool.load_table(p, ('id',))

    def test_outside_path_rejected_before_open(self):
        with self.assertRaises(tool.InputError):
            tool.load_table(Path.cwd().parent / 'outside.csv', ('id',))

    def test_cli_exit_codes_and_parseable_output(self):
        for candidate, expected in [('id,v\na,1\n', 0), ('id,v\na,2\n', 1), ('id,v\na\n', 2)]:
            self.compare('id,v\na,1\n', 'id,v\na,1\n')
            self.a.write_text(candidate)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                result = tool.main([str(self.b), str(self.a), '--key', 'id'])
            self.assertEqual(result, expected)
            payload = json.loads(err.getvalue() if expected == 2 else out.getvalue())
            self.assertIn('error' if expected == 2 else 'equal', payload)


if __name__ == '__main__':
    unittest.main()
