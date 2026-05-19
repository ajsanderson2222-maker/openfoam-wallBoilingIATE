import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re, os

CASE = os.path.dirname(os.path.abspath(__file__))
R    = 0.0096

def load_profile(path):
    """Return (r/R, alpha, T_liq_C, d_mm) from a line.xy profile file."""
    p = np.loadtxt(path)
    r    = p[:,0] / R
    alpha = p[:,1]
    T_liq = p[:,2] - 273.15
    d_mm  = p[:,4] * 1000
    return r, alpha, T_liq, d_mm

# ── experimental data ──────────────────────────────────────────────────────────
vof_exp = np.loadtxt(f'{CASE}/validation/exptData/vof_deb1.txt')
T_exp   = np.loadtxt(f'{CASE}/validation/exptData/T_deb1.txt')
d_exp   = np.loadtxt(f'{CASE}/validation/exptData/d_deb1.txt')

# ── simulation profiles ────────────────────────────────────────────────────────
studies = {
    'Baseline':                    f'{CASE}/studies/baseline/profile.xy',
    'Study 1 — small d_dep':       f'{CASE}/studies/study1/profile.xy',
    'Study 2 — low C_td':          f'{CASE}/studies/study2/profile.xy',
    'Study 3 — small d_dep+C_td':  f'{CASE}/studies/study3/profile.xy',
    'Study 4 — low C_rc':          f'{CASE}/studies/study4/profile.xy',
    'Study 5 — low We_cr':         f'{CASE}/studies/study5/profile.xy',
    'Study 6 — low C_rc+We_cr':    f'{CASE}/studies/study6/profile.xy',
}

colors = ['steelblue', 'darkorange', 'green', 'purple', 'crimson', 'teal', 'saddlebrown']
styles = ['-', '--', '-.', ':', '-', '--', '-.']

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('Parametric study — Débora validation  (z = 3.49 m)', fontsize=13)

for ax, (exp_x, exp_y, xlabel, title) in zip(axes, [
        (vof_exp[:,1], vof_exp[:,0], 'Gas void fraction α_gas', 'Void fraction'),
        (T_exp[:,1]-273.15, T_exp[:,0], 'Liquid temperature [°C]', 'Liquid temperature'),
        (d_exp[:,1]*1000, d_exp[:,0], 'Bubble diameter [mm]', 'Bubble diameter'),
    ]):
    ax.plot(exp_x, exp_y, 'ro', ms=5, zorder=5, label='Experiment (Débora)')
    ax.set_xlabel(xlabel); ax.set_title(title)
    ax.set_ylabel('r/R  (0 = centre, 1 = wall)')
    ax.grid(alpha=0.3)

for (label, path), color, ls in zip(studies.items(), colors, styles):
    if not os.path.exists(path):
        print(f'Missing: {path}')
        continue
    r, alpha, T_liq, d_mm = load_profile(path)
    axes[0].plot(alpha, r, color=color, ls=ls, lw=1.6, label=label)
    axes[1].plot(T_liq,  r, color=color, ls=ls, lw=1.6, label=label)
    axes[2].plot(d_mm,   r, color=color, ls=ls, lw=1.6, label=label)

for ax in axes:
    ax.legend(fontsize=7.5, loc='upper left')

plt.tight_layout()
plt.savefig(f'{CASE}/study_comparison.png', dpi=150)
plt.close()
print('study_comparison.png saved')
