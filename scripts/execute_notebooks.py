"""Eksekusi notebook dari kernel bersih dan validasi keluarannya. / Execute notebooks from clean kernels and validate their completed outputs."""
import argparse
import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main():
    parser = argparse.ArgumentParser(add_help=False, description=__doc__)
    parser.add_argument('-h', '--help', action='help', help='Tampilkan bantuan lalu keluar / Show this help and exit')
    parser.add_argument('--output', type=Path, default=Path('work/executed-notebooks'), help='Direktori notebook hasil eksekusi / Executed notebooks directory')
    parser.add_argument('--in-place', action='store_true', help='Perbarui keluaran ilmiah dalam repository / Refresh checked-in scientific outputs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = root/'notebooks' if args.in_place else args.output.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted((root/'notebooks').glob('*.ipynb')):
        notebook = nbformat.read(path, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                cell.outputs = []
                cell.execution_count = None
        print('Menjalankan / Executing', path.name, flush=True)
        client = NotebookClient(notebook, timeout=180, kernel_name='python3',
                                resources={'metadata': {'path': str(root)}})
        client.execute()
        # Wall-clock cell timings do not belong in reproducible source output.
        for cell in notebook.cells:
            cell.metadata.pop('execution', None)
        nbformat.validate(notebook)
        codes = [c for c in notebook.cells if c.cell_type == 'code']
        assert all(c.execution_count is not None for c in codes)
        assert not any(o.output_type == 'error' for c in codes for o in c.outputs)
        target = destination/path.name
        nbformat.write(notebook, target)
        records.append({'notebook': path.name, 'code_cells': len(codes),
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'errors': 0})
    if not records:
        raise SystemExit('Notebook tidak ditemukan / No notebooks found')
    summary = {'notebooks': records, 'all_executed': True}
    report_path = root/'work/notebook-execution.json'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
