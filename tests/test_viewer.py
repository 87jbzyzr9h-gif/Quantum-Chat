import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

import viewer


class ViewerTests(unittest.TestCase):
    def test_all_symbols_show_bell_marginals_and_actual_decoding(self):
        for bits in viewer.LABELS:
            trace = viewer.trace_pair(bits, 0, 19, 4)
            self.assertEqual(trace['first_measurement'], bits)
            self.assertEqual(trace['histogram'][bits], 4)
            for stage in trace['stages']:
                self.assertAlmostEqual(sum(stage['probabilities']), 1)
                if stage['title'] in ('DISTRIBUSI B / B DISTRIBUTION', 'ENCODING FASE / ENCODE PHASE', 'ENCODING FLIP / ENCODE FLIP'):
                    self.assertEqual(stage['ownership'], {'A': 'Bumi', 'B': 'Mars'})
                    self.assertAlmostEqual(stage['B']['p0'], 0.5)
                    self.assertAlmostEqual(stage['B']['p1'], 0.5)
            self.assertEqual(trace['stages'][6]['ownership'], {'A': 'Mars', 'B': 'Mars'})
            self.assertEqual(trace['stages'][-1]['probabilities'][int(bits, 2)], 1)

    def test_phase_is_visible_in_amplitudes_not_only_probabilities(self):
        plus = viewer.trace_pair('00', 0, 4, 1)['stages'][5]
        minus = viewer.trace_pair('10', 0, 4, 1)['stages'][5]
        self.assertEqual(plus['probabilities'], minus['probabilities'])
        self.assertNotEqual(plus['state_vector_notation'], minus['state_vector_notation'])

    def test_noise_uses_exact_ensemble_density_matrix(self):
        trace = viewer.trace_pair('11', 0.3, 22, 32)
        stage = trace['stages'][-2]
        self.assertIsNone(stage['state_vector_notation'])
        self.assertLess(stage['global_purity'], 1)
        np.testing.assert_allclose(stage['probabilities'], [0.1, 0.1, 0.1, 0.7], atol=1e-12)
        self.assertEqual(sum(trace['histogram'].values()), 32)
        self.assertEqual(trace, viewer.trace_pair('11', 0.3, 22, 32))

    def test_trace_message_full_frame_unicode_and_json(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)/'trace.json'
            result = subprocess.run([sys.executable, str(root/'viewer.py'), '--message', 'Halo 🌏',
                                     '--pairs', '1', '--shots', '2', '--json', str(destination)],
                                    cwd=root, text=True, capture_output=True, timeout=20, check=True)
            data = json.loads(destination.read_text())
        self.assertTrue(data['observer_only'])
        self.assertFalse(data['live_server_tap'])
        self.assertEqual(data['frame_verification_separate_run']['received_text'], 'Halo 🌏')
        self.assertEqual(len(data['traces']), 1)
        self.assertIn('OBSERVER MODE', result.stdout)

    def test_explicit_empty_payload_still_verifies_full_frame(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            viewer.main(['--message', '', '--shots', '1'])
        self.assertIn('Payload kosong', output.getvalue())
        self.assertIn('"accepted": true', output.getvalue())

    def test_step_and_invalid_options(self):
        from unittest.mock import patch
        with patch('builtins.input', return_value='') as prompt, contextlib.redirect_stdout(io.StringIO()):
            viewer.main(['--bits', '00', '--shots', '1', '--step'])
        self.assertEqual(prompt.call_count, 9)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            viewer.main(['--bits', '00', '--shots', '0'])


if __name__ == '__main__':
    unittest.main()
