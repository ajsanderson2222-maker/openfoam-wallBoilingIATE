import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import re

CASE = '/home/ads-user/openfoam/openfoam-wallBoilingIATE'
R    = 0.0096   # pipe radius [m]
L    = 3.5      # pipe length [m]
NX, NY = 350, 40   # axial, radial cells

def parse_scalar(path):
    with open(path) as f: txt = f.read()
    m = re.search(r'internalField\s+nonuniform List<scalar>\s+(\d+)\s*\n\(', txt)
    if not m: return None
    n = int(m.group(1))
    vals = re.findall(r'([-+\d.eE]+)', txt[m.end():][:n*22])
    return np.array([float(v) for v in vals[:n]])

# ── cell centres (y varies fastest in OpenFOAM cell ordering for this mesh) ──
cx = parse_scalar(f'{CASE}/4/Ccx')   # axial
cy = parse_scalar(f'{CASE}/4/Ccy')   # radial

# Reshape: NX*NY, y-fastest → (NX, NY), then transpose → (NY, NX)
def reshape2d(arr): return arr.reshape(NX, NY).T   # → (NY=radial, NX=axial)

xc_1d = cx.reshape(NX, NY)[:, 0]   # NX axial positions
yc_1d = cy.reshape(NX, NY)[0, :]   # NY radial positions

def edges(c):
    d = np.diff(c)
    return np.concatenate([[c[0]-d[0]/2], c[:-1]+d/2, [c[-1]+d[-1]/2]])

xe = edges(xc_1d) * 1000   # mm
ye = edges(yc_1d) * 1000   # mm
XX, YY = np.meshgrid(xe, ye)

# ── fields ────────────────────────────────────────────────────────────────────
alpha2d = reshape2d(parse_scalar(f'{CASE}/4/alpha.gas'))
T2d     = reshape2d(parse_scalar(f'{CASE}/4/T.liquid') - 273.15)
d2d_raw = reshape2d(parse_scalar(f'{CASE}/4/d.gas') * 1000)
# Mask bubble diameter where there are essentially no bubbles — avoids
# spurious colour in the sub-cooled core and near the inlet.
d2d = np.ma.masked_where(alpha2d < 0.005, d2d_raw)

# pcolormesh with gouraud shading interpolates colours between cell centres
# for a smooth result; requires cell-centre coordinates (not edges).
XC, YC = np.meshgrid(xc_1d * 1000, yc_1d * 1000)

# ── 2D field contours ─────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 3.5))
fig.suptitle('wallBoilingIATE — axial–radial fields at t = 4 s', fontsize=13)

for ax, F, title, cmap in zip(axes,
        [alpha2d, T2d, d2d],
        ['Gas void fraction α_gas', 'Liquid temperature [°C]', 'Bubble diameter d_gas [mm]'],
        ['RdBu_r', 'hot', 'viridis']):
    im = ax.pcolormesh(XC, YC, F, cmap=cmap, shading='gouraud')
    ax.set_xlim(xe[0], xe[-1]); ax.set_ylim(ye[0], ye[-1])
    ax.axvline(3490.1, color='white', lw=1.2, ls='--', label='z = 3.49 m')
    ax.set_xlabel('Axial position [mm]')
    ax.set_ylabel('Radial [mm]')
    ax.set_title(title)
    plt.colorbar(im, ax=ax)

axes[0].legend(fontsize=8, loc='upper left')
plt.tight_layout()
plt.savefig(f'{CASE}/field_contours.png', dpi=150)
plt.close()
print('field_contours.png saved')

# ── mesh image ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 2.5))
for xi in xe:  ax.axvline(xi, color='steelblue', lw=0.15, alpha=0.7)
for yi in ye:  ax.axhline(yi, color='steelblue', lw=0.5)
ax.set_xlim(xe[0], xe[-1])
ax.set_ylim(ye[0], ye[-1])
ax.set_xlabel('Axial position [mm]')
ax.set_ylabel('Radial [mm]')
ax.set_title(f'Mesh — {NX}×{NY} = {NX*NY:,} cells  |  y-grading 0.5 (cells refined toward wall)')
ax.set_aspect('auto')
plt.tight_layout()
plt.savefig(f'{CASE}/mesh.png', dpi=150)
plt.close()
print('mesh.png saved')

# ── BC diagram ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 3.5))
Lmm, Rmm = L * 1000, R * 1000
ax.set_xlim(-200, Lmm + 200)
ax.set_ylim(-2.5, Rmm + 3.5)
ax.set_aspect('auto')
ax.axis('off')
ax.set_title('Boundary conditions — wallBoilingIATE', fontsize=12, pad=8)

# pipe outline
ax.add_patch(mpatches.Rectangle((0, 0), Lmm, Rmm, fill=True,
             facecolor='#e8f4f8', edgecolor='black', lw=2))

# heated wall (top)
ax.plot([0, Lmm], [Rmm, Rmm], 'r-', lw=4, label='Heated wall')
ax.text(Lmm/2, Rmm + 0.5, 'Heated wall  (noSlip, q″ = 570 kW/m², wallBoiling nucleation BC)',
        ha='center', va='bottom', fontsize=9, color='red')

# axis (bottom)
ax.plot([0, Lmm], [0, 0], 'k--', lw=1.5)
ax.text(Lmm/2, -0.7, 'Axis of symmetry  (wedge — 1°)',
        ha='center', va='top', fontsize=9, color='black')

# inlet
ax.annotate('', xy=(80, Rmm*0.55), xytext=(0, Rmm*0.55),
            arrowprops=dict(arrowstyle='->', color='navy', lw=2))
ax.text(-10, Rmm*0.55,
        'Inlet\nmappedInternal\nU_liq = 0.496 m/s\nT_liq = 80.8 °C\nα_gas ≈ 0',
        ha='right', va='center', fontsize=8.5, color='navy')

# outlet
ax.annotate('', xy=(Lmm, Rmm*0.55), xytext=(Lmm-80, Rmm*0.55),
            arrowprops=dict(arrowstyle='->', color='darkgreen', lw=2))
ax.text(Lmm + 10, Rmm*0.55,
        'Outlet\nzeroGradient U\nfixedValue p',
        ha='left', va='center', fontsize=8.5, color='darkgreen')

# measurement plane
ax.axvline(3490.1, color='orange', lw=1.5, ls='--')
ax.text(3490.1 - 30, Rmm*0.3, 'z=3.49m', fontsize=8, color='darkorange', rotation=90, va='center')

plt.tight_layout()
plt.savefig(f'{CASE}/bc_diagram.png', dpi=150)
plt.close()
print('bc_diagram.png saved')

# ── convergence ───────────────────────────────────────────────────────────────
log = open(f'{CASE}/log.foamRun').read()
res = {'p_rgh': [], 'h.liquid': [], 'k.liquid': []}
for line in log.split('\n'):
    for key in res:
        if f'Solving for {key},' in line:
            m = re.search(r'Final residual = ([\d.eE+\-]+)', line)
            if m: res[key].append(float(m.group(1)))

print({k: len(v) for k,v in res.items()})
fig, ax = plt.subplots(figsize=(9, 4))
labels = {'p_rgh': 'p_rgh', 'h.liquid': 'h.liquid (enthalpy)', 'k.liquid': 'k.liquid (TKE)'}
for key, label in labels.items():
    arr = res[key]
    if arr:
        xi = np.linspace(0, 4, len(arr))
        ax.semilogy(xi, arr, label=label, lw=0.8)

ax.set_xlabel('Simulation time [s]')
ax.set_ylabel('Final residual')
ax.set_title('Solver residuals — wallBoilingIATE')
ax.legend()
ax.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{CASE}/convergence.png', dpi=150)
plt.close()
print('convergence.png saved')

# ── validation profiles ───────────────────────────────────────────────────────
profile = np.loadtxt(f'{CASE}/postProcessing/graph/4/line.xy')
r_sim   = profile[:,0] / R
alpha_s = profile[:,1]
T_liq_s = profile[:,2] - 273.15
d_gas_s = profile[:,4] * 1000

vof_exp = np.loadtxt(f'{CASE}/validation/exptData/vof_deb1.txt')
T_exp   = np.loadtxt(f'{CASE}/validation/exptData/T_deb1.txt')
d_exp   = np.loadtxt(f'{CASE}/validation/exptData/d_deb1.txt')

fig, axes = plt.subplots(1, 3, figsize=(13, 5))
fig.suptitle('Wall boiling validation — Débora experiment (z = 3.49 m)', fontsize=13)

axes[0].plot(alpha_s, r_sim, 'b-', label='OpenFOAM')
axes[0].plot(vof_exp[:,1], vof_exp[:,0], 'ro', ms=4, label='Experiment (Débora)')
axes[0].set_xlabel('Gas void fraction α_gas')
axes[0].set_ylabel('r/R  (0 = centre, 1 = wall)')
axes[0].set_title('Void fraction'); axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(T_liq_s, r_sim, 'b-', label='OpenFOAM')
axes[1].plot(T_exp[:,1]-273.15, T_exp[:,0], 'ro', ms=4, label='Experiment (Débora)')
axes[1].set_xlabel('Liquid temperature [°C]')
axes[1].set_title('Liquid temperature'); axes[1].legend(); axes[1].grid(alpha=0.3)

axes[2].plot(d_gas_s, r_sim, 'b-', label='OpenFOAM')
axes[2].plot(d_exp[:,1]*1000, d_exp[:,0], 'ro', ms=4, label='Experiment (Débora)')
axes[2].set_xlabel('Bubble diameter [mm]')
axes[2].set_title('Bubble diameter'); axes[2].legend(loc='lower right'); axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f'{CASE}/validation_profiles.png', dpi=150)
plt.close()
print('validation_profiles.png saved')
