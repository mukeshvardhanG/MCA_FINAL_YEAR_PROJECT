"""Helper: generate 5000 records"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.generate_dataset import generate_synthetic_dataset

os.makedirs("data", exist_ok=True)
df = generate_synthetic_dataset(5000)
df.to_csv(os.path.join("data", "dataset2.csv"), index=False)
print(f"Generated {len(df)} records")
print(f"Grade distribution:\n{df['performance_grade'].value_counts().sort_index()}")
print(f"Score range: {df['overall_pe_score'].min():.1f} - {df['overall_pe_score'].max():.1f}")
