"""Bilingual plot/table helpers; physics stays in notebook cells.
Helper gambar/tabel bilingual; perhitungan fisika tetap di sel notebook.
"""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
COLORS = ['#245c81', '#b15b31', '#477554', '#76538b']


def style():
    plt.rcParams.update({'figure.dpi': 110, 'savefig.dpi': 150, 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.hashsalt': 'quantum-chat-0.1.0'})


def save(fig, name):
    directory = ROOT/'docs/figures'
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory/f'{name}.png', bbox_inches='tight', facecolor='white')
    fig.savefig(directory/f'{name}.svg', bbox_inches='tight', facecolor='white', metadata={'Date': None})
    svg = directory/f'{name}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')


def bilingual_table(table):
    """Rename display labels only / Ganti label tampilan saja."""
    labels = {
        'shots': 'shot / shots', 'correct': 'benar / correct',
        'input': 'masukan / input', 'state': 'state / keadaan',
        'sender': 'pengirim / sender', 'receiver': 'penerima / receiver',
        'UTF-8 bytes': 'byte UTF-8 / UTF-8 bytes', 'frame bytes': 'byte frame / frame bytes',
        'status': 'status / status', 'A transfers': 'transfer A / A transfers',
        'B distributions': 'distribusi B / B distributions', 'ACK bits': 'bit ACK / ACK bits',
        'attempt': 'percobaan / attempt', 'accepted': 'diterima / accepted',
        'fresh': 'baru / fresh', 'ack_valid': 'ACK valid / valid ACK',
        'error': 'kesalahan / error', 'trials': 'uji / trials',
        'exact_received': 'diterima eksak / exact received',
        'confirmed': 'terkonfirmasi / confirmed', 'mean_attempts': 'rerata percobaan / mean attempts',
        'stage': 'tahap / stage', 'owner A': 'pemilik A / owner A',
        'owner B': 'pemilik B / owner B', 'purity global': 'kemurnian global / global purity',
        'symbol': 'simbol / symbol', 'ensemble_probability': 'peluang ensemble / ensemble probability',
        'actual_shots': 'shot aktual / actual shots', 'sample_fraction': 'fraksi sampel / sample fraction',
        'ideal': 'ideal / ideal', 'noisy': 'berisik / noisy',
    }
    result = table.rename(columns=labels, index=labels)
    if result.index.name == 'profile':
        result.index.name = 'profil / profile'
    return result


def architecture():
    fig, ax = plt.subplots(figsize=(18, 5.3))
    ax.set(xlim=(-.2, 12.6), ylim=(-1.65, 2.8))
    ax.axis('off')
    labels = [
        'Frame UTF-8\nHeader + checksum',
        'Pasangan Bell\nBell pairs\nH(A), CNOT(A,B)',
        'Encoding lokal\nLocal encoding\nZ → X on A',
        'Transfer A\nModel quantum\nQuantum model',
        'Decoding bersama\nJoint decoding\nCNOT, H, measure',
        'Penerima / Receiver\nValidasi + ACK\nValidate + ACK',
    ]
    for index, label in enumerate(labels):
        x = index * 2.1
        ax.add_patch(FancyBboxPatch((x, 0), 1.75, 1.4, boxstyle='round,pad=0.06',
                                   facecolor='#eef3f6', edgecolor=COLORS[0], linewidth=1.3))
        ax.text(x + .875, .7, label, ha='center', va='center', fontsize=10)
        if index < len(labels)-1:
            ax.add_patch(FancyArrowPatch((x + 1.81, .7), (x + 2.02, .7), arrowstyle='-|>', mutation_scale=12))
    ax.text(6.1, 2.25, 'Quantum Chat: alur data logis dalam simulator tepercaya\nLogical data path inside the trusted simulator', ha='center', fontsize=14, weight='bold')
    ax.annotate('', xy=(.85, -.4), xytext=(11.35, -.4), arrowprops={'arrowstyle': '->', 'color': COLORS[1]})
    ax.text(6.1, -.85, 'ACK / NACK klasik dalam model; pasangan baru setiap pengulangan\nModeled classical ACK / NACK; fresh pairs on every retry', ha='center', color=COLORS[1])
    ax.text(6.1, -1.45, 'Terminal ↔ backend memakai TCP localhost klasik, dihitung terpisah.\nActual terminal ↔ backend communication uses classical localhost TCP, counted separately.', ha='center', fontsize=10)
    return fig


def ownership():
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set(xlim=(-.5, 11), ylim=(-1, 3.3))
    ax.axis('off')
    for x, label in [(1, 'Pengirim / Sender\nBumi'), (8.9, 'Penerima / Receiver\nMars')]:
        ax.text(x, 2.5, label, ha='center', weight='bold', fontsize=13)
    ax.plot([.3, 9.7], [1.3, 1.3], color=COLORS[0], lw=2)
    ax.text(.1, 1.3, 'A', ha='right', va='center', color=COLORS[0])
    ax.text(1.3, 1.75, 'Encoding Z/X\nEncode Z/X', ha='center')
    ax.annotate('A harus tiba sebelum decoding bersama\nA must arrive before joint decoding', xy=(7.9, 1.3), xytext=(5.3, 2.0),
                ha='center', arrowprops={'arrowstyle': '->', 'color': COLORS[0]})
    ax.plot([.3, 9.7], [.15, .15], color=COLORS[1], lw=2)
    ax.text(.1, .15, 'B', ha='right', va='center', color=COLORS[1])
    ax.text(5, -.55, 'B didistribusikan lebih dahulu; transfernya dihitung terpisah\nB pre-distributed; its transfer is a separate resource', ha='center', fontsize=10)
    ax.add_patch(FancyBboxPatch((8, -.08), 2, 1.65, boxstyle='round,pad=.08', facecolor='white', edgecolor='#333333'))
    ax.text(9, .75, 'CNOT bersama / Joint\nH(A)\nUkur / Measure A,B', ha='center', va='center', fontsize=10)
    return fig
