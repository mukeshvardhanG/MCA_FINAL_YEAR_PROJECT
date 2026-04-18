"""
Research Plots Generator
Reads the CSV outputs from the experimental modules and generates
IEEE-compliant bar and line graphs representing model performance, 
ablation studies, and scalability.

Usage:
    python -m research.plots
"""
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set plotting style (IEEE style mimicking: grayscale or high-contrast crisp colors)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.5)
sns.set_palette("colorblind")

RESULTS_DIR = os.path.join("research", "results")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def plot_model_comparison():
    """Bar chart comparing RMSE and R² of individual models vs Ensemble."""
    df_path = os.path.join(RESULTS_DIR, "model_comparison_table.csv")
    if not os.path.exists(df_path):
        return
    
    df = pd.read_csv(df_path)
    
    # Plot R²
    plt.figure(figsize=(8, 6))
    ax = sns.barplot(x="Model", y="R²", hue="Model", data=df, palette="Blues_d", legend=False)
    plt.title("Model Performance Comparison (Test Set R²)")
    plt.ylim(0, 1.0)
    plt.ylabel("R² Score")
    for i, p in enumerate(ax.patches):
        ax.annotate(f"{p.get_height():.3f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=12, color='black', xytext=(0, 5),
                    textcoords='offset points')
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "model_comparison_r2.png"), dpi=300)
    plt.close()

def plot_ablation_study():
    """Line/bar chart showing performance scaling as features are added."""
    df_path = os.path.join(RESULTS_DIR, "ablation_ensemble_summary.csv")
    if not os.path.exists(df_path):
        return
    
    df = pd.read_csv(df_path)
    # df has Config, R²
    
    plt.figure(figsize=(10, 6))
    plt.plot(df["Config"], df["R²"], marker='o', linestyle='-', linewidth=2, markersize=10, color="#d9534f")
    plt.title("Ablation Study: Predictive Capability by Feature Set")
    plt.xlabel("Feature Set Configuration")
    plt.ylabel("Ensemble R² Score")
    plt.ylim(0, 1.05)
    plt.grid(True, linestyle="--", alpha=0.7)
    
    for i, r2 in enumerate(df["R²"]):
        plt.text(i, r2 + 0.02, f"{r2:.3f}", ha='center', fontsize=12, fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "ablation_study_line.png"), dpi=300)
    plt.close()

def plot_scalability():
    """Line graph of computation time scaling across 100, 1000, 10000 records."""
    df_path = os.path.join(RESULTS_DIR, "scalability_analysis.csv")
    if not os.path.exists(df_path):
        return
    
    df = pd.read_csv(df_path)
    
    plt.figure(figsize=(8, 6))
    plt.plot(df["N_Records"], df["Total_Mean_s"], marker='s', linestyle='-', linewidth=2, color="#5bc0de", label='Total Time (s)')
    plt.title("Scalability Analysis: Execution Time by Record Volume")
    plt.xlabel("Number of Records")
    plt.ylabel("Time (seconds)")
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, which="both", ls="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "scalability_analysis_log_line.png"), dpi=300)
    plt.close()

if __name__ == "__main__":
    print(f"Generating paper-ready charts to {FIG_DIR}...")
    plot_model_comparison()
    plot_ablation_study()
    plot_scalability()
    print("Graphs successfully created.")
