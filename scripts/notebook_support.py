"""Plot helpers only; physical calculations remain visible in notebook cells."""
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


def architecture():
    fig, ax = plt.subplots(figsize=(15, 3.3))
    ax.set(xlim=(-0.2, 12.6), ylim=(-1.1, 1.8))
    ax.axis('off')
    labels = ['UTF-8 frame\nheader + checksum', 'Bell pairs\nH(A), CNOT(A,B)',
              'Local encoding\nZ then X on A', 'A transfer\nquantum model',
              'Joint decoding\nCNOT, H, measure', 'Receiver\nvalidate + ACK']
    for index, label in enumerate(labels):
        x = index * 2.1
        ax.add_patch(FancyBboxPatch((x, 0), 1.75, 0.95, boxstyle='round,pad=0.06',
                                   facecolor='#eef3f6', edgecolor=COLORS[0], linewidth=1.3))
        ax.text(x + .875, .475, label, ha='center', va='center', fontsize=10)
        if index < len(labels)-1:
            ax.add_patch(FancyArrowPatch((x + 1.81, .475), (x + 2.02, .475), arrowstyle='-|>', mutation_scale=12))
    ax.text(5.9, 1.5, 'Quantum Chat: logical data path inside the trusted simulator', ha='center', fontsize=14, weight='bold')
    ax.annotate('', xy=(.85, -.4), xytext=(11.35, -.4), arrowprops={'arrowstyle': '->', 'color': COLORS[1]})
    ax.text(6.1, -.72, 'Modeled classical ACK / NACK; fresh pairs on every retry', ha='center', color=COLORS[1])
    ax.text(6.1, -1.03, 'Actual terminal ↔ backend communication uses classical localhost TCP, counted separately.', ha='center', fontsize=10)
    return fig


def ownership():
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.set(xlim=(-.5, 10.8), ylim=(-.6, 2.6))
    ax.axis('off')
    for x, label in [(1, 'Sender / Bumi'), (8.7, 'Receiver / Mars')]:
        ax.text(x, 2.2, label, ha='center', weight='bold', fontsize=13)
    ax.plot([.3, 9.7], [1.3, 1.3], color=COLORS[0], lw=2)
    ax.text(.1, 1.3, 'A', ha='right', va='center', color=COLORS[0])
    ax.text(1.3, 1.65, 'Encode Z/X', ha='center')
    ax.annotate('A must arrive before joint decoding', xy=(7.9, 1.3), xytext=(5, 1.8),
                ha='center', arrowprops={'arrowstyle': '->', 'color': COLORS[0]})
    ax.plot([.3, 9.7], [.15, .15], color=COLORS[1], lw=2)
    ax.text(.1, .15, 'B', ha='right', va='center', color=COLORS[1])
    ax.text(4.6, -.22, 'B pre-distributed; its transfer is a separate resource', ha='center', fontsize=10)
    ax.add_patch(FancyBboxPatch((8, -.08), 2, 1.65, boxstyle='round,pad=.08', facecolor='white', edgecolor='#333333'))
    ax.text(9, .75, 'Joint CNOT\nH(A)\nMeasure A,B', ha='center', va='center')
    return fig
