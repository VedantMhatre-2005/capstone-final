"""
plot_pipeline_latency.py
========================
Generates a publication-quality chart visualizing the execution latency
breakdown of the 8-Node Mumbai Traffic Forecasting & QAOA Optimization Pipeline.

Data:
  - ST-QGCN Traffic Flow Prediction      :  13.32 ms  (3.94%)
  - Congestion Detection & Detour Routing:   5.14 ms  (1.52%)
  - QUBO Problem Formulation             :   2.88 ms  (0.85%)
  - QAOA Quantum Solver Execution        : 313.37 ms (92.61%)
  - Dynamic Signal Timing Optimization   :   3.65 ms  (1.08%)
  - Total End-to-End Execution Time      : 338.36 ms (~0.34 s)
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Ensure charts directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pipeline_latency_breakdown.png")

# Data definitions
stages = [
    "ST-QGCN Traffic Forecasting",
    "Congestion Detection & Detour Routing",
    "QUBO Problem Formulation",
    "QAOA Quantum Solver Execution",
    "Dynamic Signal Timing Optimization"
]

latencies = [13.32, 5.14, 2.88, 313.37, 3.65]
total_latency = sum(latencies)  # 338.36 ms
percentages = [(lat / total_latency) * 100.0 for lat in latencies]

# Curated modern color palette
colors = [
    "#2563EB",  # Royal Blue (ST-QGCN)
    "#0D9488",  # Teal (Congestion & Routing)
    "#D97706",  # Warm Amber (QUBO Formulation)
    "#7C3AED",  # Deep Violet (QAOA Quantum Solver)
    "#059669",  # Emerald (Signal Timing)
]

# Configure typography and styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 10,
    "axes.edgecolor": "#CBD5E1",
    "axes.linewidth": 1.0,
})

fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)

y_pos = np.arange(len(stages))[::-1]
bars = ax.barh(y_pos, latencies, color=colors, height=0.52, edgecolor="#1E293B", linewidth=0.8, zorder=3)

# Grid lines and spines
ax.grid(axis="x", linestyle="--", alpha=0.5, color="#94A3B8", zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#64748B")
ax.spines["bottom"].set_color("#64748B")

ax.set_yticks(y_pos)
ax.set_yticklabels(stages, fontsize=10.5, fontweight="600", color="#0F172A")
ax.set_xlabel("Execution Time (ms)", fontsize=11, fontweight="bold", labelpad=8, color="#0F172A")
ax.set_title("Pipeline Component Execution Latency (8-Node Mumbai Network)", fontsize=13, fontweight="bold", pad=15, loc="left", color="#0F172A")
ax.set_xlim(0, 360)

# Add exact value badges
for bar, lat, pct in zip(bars, latencies, percentages):
    width = bar.get_width()
    y_center = bar.get_y() + bar.get_height() / 2.0
    text_label = f"{lat:.2f} ms  ({pct:.1f}%)"
    if width > 50:
        ax.text(width - 8, y_center, text_label,
                ha="right", va="center", color="white", fontsize=9.5, fontweight="bold")
    else:
        ax.text(width + 6, y_center, text_label,
                ha="left", va="center", color="#0F172A", fontsize=9.5, fontweight="bold")

# Add summary box in upper right
total_box = (
    r"$\mathbf{End\text{-}to\text{-}End\ Pipeline\ Total:}$" + "\n"
    r"$\mathbf{338.36\ ms\ (\approx 0.34\ seconds)}$"
)
ax.text(
    0.97, 0.58, total_box,
    transform=ax.transAxes,
    ha="right", va="center",
    fontsize=10.5,
    color="#1E293B",
    bbox=dict(boxstyle="round,pad=0.6", facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.close()

print(f"[SUCCESS] Chart saved to: {OUTPUT_FILE}")
