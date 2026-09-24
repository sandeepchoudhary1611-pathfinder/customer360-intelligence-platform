"""
Customer360 Intelligence Platform - Master Runner
=================================================
This script runs the entire project end-to-end in one command:
1. Generates 8,000 customers and 24,740 orders into SQLite database.
2. Executes and validates advanced analytical SQL views.
3. Trains machine learning models (Random Forest), computes metrics, and saves charts.
4. Executes GenAI Copilot to generate executive retention memos.
"""

import os
import sys
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable

def print_header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def run_step(step_name, script_path):
    print_header(f"RUNNING STEP: {step_name}")
    start_time = time.time()
    
    cmd = [PYTHON_EXE, script_path]
    result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=False)
    
    elapsed = time.time() - start_time
    if result.returncode == 0:
        print(f"\n--> [SUCCESS] {step_name} completed in {elapsed:.1f}s.")
    else:
        print(f"\n--> [ERROR] {step_name} failed with return code {result.returncode}.")
        sys.exit(result.returncode)

def main():
    print("""
    ===================================================================
                  CUSTOMER360 INTELLIGENCE PLATFORM
                 End-to-End Enterprise Analytics Demo
    ===================================================================
    This pipeline demonstrates:
    1. SQL Database Modeling & Analytical Queries (RFM, Cohorts, CLV)
    2. Python Data Processing & Predictive Churn Modeling (Scikit-Learn)
    3. Evaluation Artifact Generation (ROC-AUC, Precision-Recall, Feature Importance)
    4. GenAI Strategy Engine (Gemini API / Executive Retention Briefing)
    5. Power BI Ready Data Exports
    ===================================================================
    """)
    
    # Step 1: Generate Data & Database
    run_step(
        "Step 1: Database Setup & Synthetic Transaction Generation",
        os.path.join(BASE_DIR, "src", "generate_synthetic_data.py")
    )
    
    # Step 2: Train ML Model & Score Customers
    run_step(
        "Step 2: Predictive Churn Modeling & Leakage Prevention",
        os.path.join(BASE_DIR, "src", "churn_model.py")
    )
    
    # Step 3: Run GenAI Copilot
    run_step(
        "Step 3: GenAI Executive Retention Copilot",
        os.path.join(BASE_DIR, "src", "ai_retention_copilot.py")
    )
    
    print_header("ALL STEPS COMPLETED SUCCESSFULLY!")
    print(f"""
Where to find your deliverables:
1. SQLite Database:        {os.path.join(BASE_DIR, 'data', 'customer360.db')}
2. Scored Customers CSV:   {os.path.join(BASE_DIR, 'data', 'processed', 'customer_churn_scored.csv')}
3. Evaluation Charts:      {os.path.join(BASE_DIR, 'artifacts')}
   - roc_curve_comparison.png
   - precision_recall_curve.png
   - confusion_matrix.png
   - feature_importance.png
4. GenAI Strategy Memo:    {os.path.join(BASE_DIR, 'artifacts', 'executive_ai_retention_briefing.md')}
5. Power BI DAX Formulas:  {os.path.join(BASE_DIR, 'power_bi', 'dax_measures.md')}
6. Interview Guide:        {os.path.join(BASE_DIR, 'docs', 'interview_talking_points.md')}
""")

if __name__ == "__main__":
    main()
