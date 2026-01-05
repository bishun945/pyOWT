import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Ellipse
import matplotlib.patheffects as PathEffects
import os
from pyowt.OWT import OWT

def draw_ellipse(ax, mean_x, mean_y, cov, color, label, n_std=1.0, text_pos=None):
    v, w = np.linalg.eigh(cov)
    order = v.argsort()[::-1]
    v = v[order]
    w = w[:, order]
    angle = np.degrees(np.arctan2(*w[:, 0][::-1]))
    width, height = 2 * n_std * np.sqrt(v)
    
    ellipse = Ellipse(
        xy=(mean_x, mean_y),
        width=width,
        height=height,
        angle=angle,
        edgecolor="#000000",
        facecolor="none",
        label=label,
        zorder=6,
    )
    ax.add_patch(ellipse)

    tx, ty = text_pos if text_pos is not None else (mean_x, mean_y)

    txt = ax.text(
        tx,
        ty,
        label,
        fontsize=12,
        color=color,
        # bbox=dict(facecolor="white", alpha=0.3, edgecolor="none"),
        # fontweight='bold',
        ha="center",
        va="center",
        zorder=7,
    )

    txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='white')])

def plot_illustration(owt, spec_csv_path=None, output_path='plot.png'):
    if spec_csv_path is None:
        spec_csv_path = f"pyowt/data/{owt.version}/OWT_mean_spec.csv"
    
    if not os.path.exists(spec_csv_path):
        print(f"Warning: Spectral library file not found at {spec_csv_path}")
        return

    spec_lib = pd.read_csv(spec_csv_path)
    
    means = owt.classInfo.mean_OWT
    covs = owt.classInfo.covm_OWT
    colors = owt.classInfo.typeColHex
    labels = owt.classInfo.typeName
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    
    ax = axs[0, 0]
    for i, lbl in enumerate(labels):
        subset = spec_lib[spec_lib["type"] == str(lbl)]
        col = colors[i]
        ax.plot(subset["wavelen"], subset["m_Rrs"], color=col, linewidth=2)
    
    ax.set_xlabel("Wavelength [nm]", fontsize=12)
    ax.set_ylabel(r"$R_{rs}$ [sr$^{-1}$]", fontsize=12)
    ax.set_title("(a) Mean spectra of optical water types", fontsize=14, loc='left')
    ax.grid(True, linestyle='--', alpha=0.3)

    ax = axs[0, 1]
    ax.set_xlim(430, 680)
    ax.set_ylim(-3.6, 3.5)
    
    for i, lbl in enumerate(labels):
        m = means[i, [0, 1]]
        c = covs[:2, :2, i]
        draw_ellipse(ax, m[0], m[1], c, colors[i], str(lbl))
        
    ax.set_xlabel("Apparent Visible Wavelength (AVW) [nm]", fontsize=12)
    ax.set_ylabel(r"Spectral Magnitude ($A_{BC}$)", fontsize=12)
    ax.set_title("(b) Spectral shape vs. magnitude", fontsize=14, loc='left')
    ax.grid(True, linestyle='--', alpha=0.3)

    ax = axs[1, 0]
    ax.set_xlim(430, 680)
    ax.set_ylim(-0.75, 1.0)
    
    for i, lbl in enumerate(labels):
        lbl_str = str(lbl)
        m = means[i, [0, 2]]
        c = covs[[0, 2], :][:, [0, 2], i]
        t_pos = (m[0], m[1])

        if lbl_str == '3a': t_pos = (m[0], m[1] + 0.10)
        if lbl_str == '3b': t_pos = (m[0], m[1] - 0.10)
        if lbl_str == '4a': t_pos = (m[0], m[1] + 0.12)
        if lbl_str == '4b': t_pos = (m[0], m[1] - 0.08)

        draw_ellipse(ax, m[0], m[1], c, colors[i], lbl_str, text_pos=t_pos)
        
    ax.set_xlabel("Apparent Visible Wavelength (AVW) [nm]", fontsize=12)
    ax.set_ylabel("Normalized Difference Index (NDI)", fontsize=12)
    ax.set_title("(c) Spectral shape vs. spectral Feature", fontsize=14, loc='left')
    ax.grid(True, linestyle='--', alpha=0.3)

    ax = axs[1, 1]
    ax.axis('off')
    
    table_data = [
        ["1", "Extremely clear waters"],
        ["2", "Blue waters with slightly higher detritus/CDOM"],
        ["3a", "Turquoise waters (moderate biomass/CDOM)"],
        ["3b", "High scattering (e.g., Coccolithophore blooms)"],
        ["4a", "Greenish water (dark, absorption dominated)"],
        ["4b", "Greenish water (bright, scattering dominated)"],
        ["5a", "Green eutrophic water (algal blooms)"],
        ["5b", "Green hyper-eutrophic (vegetation-like NIR)"],
        ["6", "Bright brown water (high detritus/sediment)"],
        ["7", "Dark brown water (high CDOM/humic)"]
    ]
    
    tbl = ax.table(cellText=table_data, colLabels=["OWT", "Description"], 
                   loc='center', cellLoc='left', bbox=[0, 0, 1, 1], colWidths=[0.15, 0.85])
    
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)
    
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', size=12)
            cell.set_facecolor('#f0f0f0')
            cell.set_height(0.08)
            if col == 0:
                cell.get_text().set_horizontalalignment('center')
                
        else:
            cell.set_height(0.085)
            if col == 0:
                cell.set_text_props(weight='bold', color='black')
                cell.get_text().set_horizontalalignment('center')
                cell.get_text().set_path_effects([PathEffects.withStroke(linewidth=3, foreground='white')])
                idx = row - 1
                if idx < len(colors):
                    cell.set_facecolor(colors[idx] + '60')
                    cell.set_alpha(0.7) 
            if col == 1:
                cell.PAD = 0.03

    ax.set_title("(d) Short description of optical water types", fontsize=14, loc='left')

    plt.tight_layout()
    plt.savefig(output_path, dpi=400, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    owt = OWT(560, 1, 0.5)
    plot_illustration(owt, output_path='projects/plot_for_essd/plot.png')

