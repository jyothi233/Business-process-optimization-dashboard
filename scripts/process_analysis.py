import os
import json
import pandas as pd
import numpy as np

def run_analysis(raw_data_path, output_json_path):
    print(f"Loading raw data from {raw_data_path}...")
    df = pd.read_csv(raw_data_path)
    
    # ------------------ Data Cleaning ------------------
    # 1. Clean missing values and fill with safe defaults
    df['Task Volume'] = pd.to_numeric(df['Task Volume'], errors='coerce').fillna(1).astype(int)
    df['Tasks Completed'] = pd.to_numeric(df['Tasks Completed'], errors='coerce').fillna(0).astype(int)
    df['Error Count'] = pd.to_numeric(df['Error Count'], errors='coerce').fillna(0).astype(int)
    df['Rework Count'] = pd.to_numeric(df['Rework Count'], errors='coerce').fillna(0).astype(int)
    df['Process Cost'] = pd.to_numeric(df['Process Cost'], errors='coerce').fillna(0.0)
    df['Customer Complaints'] = pd.to_numeric(df['Customer Complaints'], errors='coerce').fillna(0).astype(int)
    df['Cycle Time (Hours)'] = pd.to_numeric(df['Cycle Time (Hours)'], errors='coerce').fillna(0.0)
    df['Standard Cycle Time'] = pd.to_numeric(df['Standard Cycle Time'], errors='coerce').fillna(0.0)
    df['Productivity %'] = pd.to_numeric(df['Productivity %'], errors='coerce').fillna(0.0)
    df['SLA Achieved'] = df['SLA Achieved'].fillna('No')
    df['Department'] = df['Department'].fillna('Unknown')
    df['Process Name'] = df['Process Name'].fillna('Unknown')
    
    null_counts = df.isnull().sum()
    print("Null value counts (after cleaning):")
    print(null_counts[null_counts > 0])
    
    # 2. Parse datetime columns
    df['Start Date'] = pd.to_datetime(df['Start Date'])
    df['End Date'] = pd.to_datetime(df['End Date'])
    
    # 3. Sort by Start Date
    df = df.sort_values(by='Start Date')
    
    # ------------------ KPI Calculations ------------------
    # Global metrics
    total_logs = len(df)
    total_volume = int(df['Task Volume'].sum())
    total_completed = int(df['Tasks Completed'].sum())
    total_errors = int(df['Error Count'].sum())
    total_rework = int(df['Rework Count'].sum())
    total_cost = float(df['Process Cost'].sum())
    total_complaints = int(df['Customer Complaints'].sum())
    
    avg_cycle_time = float(df['Cycle Time (Hours)'].mean()) if total_logs > 0 else 0.0
    avg_std_cycle_time = float(df['Standard Cycle Time'].mean()) if total_logs > 0 else 0.0
    
    # Formulas
    # Process Efficiency %: Mean of (Standard Cycle Time / Actual Cycle Time * 100), capped at 100%
    df['Efficiency Ratio'] = np.where(df['Cycle Time (Hours)'] > 0, np.minimum(100.0, (df['Standard Cycle Time'] / df['Cycle Time (Hours)']) * 100), 0.0)
    global_efficiency = float(df['Efficiency Ratio'].mean()) if total_logs > 0 else 0.0
    
    global_productivity = float(df['Productivity %'].mean()) if total_logs > 0 else 0.0
    
    # SLA Achievement %: % of records with SLA Achieved == "Yes"
    sla_achieved_count = len(df[df['SLA Achieved'] == 'Yes'])
    global_sla_achieved = float((sla_achieved_count / total_logs) * 100) if total_logs > 0 else 0.0
    
    # Error, Rework and Task rates
    global_error_rate = float((total_errors / total_volume) * 100) if total_volume > 0 else 0.0
    global_rework_rate = float((total_rework / total_volume) * 100) if total_volume > 0 else 0.0
    global_task_completion_rate = float((total_completed / total_volume) * 100) if total_volume > 0 else 0.0
    global_complaint_rate = float((total_complaints / total_logs) * 100) if total_logs > 0 else 0.0
    cost_per_task = float(total_cost / total_completed) if total_completed > 0 else 0.0

    global_kpis = {
        "total_records": total_logs,
        "total_volume": total_volume,
        "total_completed": total_completed,
        "total_cost": round(total_cost, 2),
        "cost_per_task": round(cost_per_task, 2),
        "process_efficiency_pct": round(global_efficiency, 2),
        "productivity_pct": round(global_productivity, 2),
        "sla_achievement_pct": round(global_sla_achieved, 2),
        "avg_cycle_time": round(avg_cycle_time, 2),
        "avg_standard_cycle_time": round(avg_std_cycle_time, 2),
        "error_rate_pct": round(global_error_rate, 2),
        "rework_rate_pct": round(global_rework_rate, 2),
        "task_completion_rate": round(global_task_completion_rate, 2),
        "customer_complaint_rate": round(global_complaint_rate, 2)
    }
    
    print("\n--- Global KPIs Calculated ---")
    for k, v in global_kpis.items():
        print(f"{k}: {v}")

    # ------------------ Department Analysis ------------------
    dept_grp = df.groupby('Department')
    dept_analysis = []
    for dept_name, group in dept_grp:
        d_vol = int(group['Task Volume'].sum())
        d_comp = int(group['Tasks Completed'].sum())
        d_err = int(group['Error Count'].sum())
        d_rew = int(group['Rework Count'].sum())
        d_cost = float(group['Process Cost'].sum())
        d_sla_yes = len(group[group['SLA Achieved'] == 'Yes'])
        d_logs = len(group)
        
        dept_analysis.append({
            "department": dept_name,
            "count": d_logs,
            "avg_cycle_time": round(float(group['Cycle Time (Hours)'].mean()), 2) if d_logs > 0 else 0.0,
            "avg_std_cycle_time": round(float(group['Standard Cycle Time'].mean()), 2) if d_logs > 0 else 0.0,
            "avg_productivity": round(float(group['Productivity %'].mean()), 2) if d_logs > 0 else 0.0,
            "avg_efficiency": round(float(group['Efficiency Ratio'].mean()), 2) if d_logs > 0 else 0.0,
            "sla_achievement_pct": round(float((d_sla_yes / d_logs) * 100), 2) if d_logs > 0 else 0.0,
            "total_cost": round(d_cost, 2),
            "error_rate_pct": round(float((d_err / d_vol) * 100), 2) if d_vol > 0 else 0.0,
            "rework_rate_pct": round(float((d_rew / d_vol) * 100), 2) if d_vol > 0 else 0.0
        })

    # ------------------ Process Analysis ------------------
    proc_grp = df.groupby('Process Name')
    proc_analysis = []
    for proc_name, group in proc_grp:
        p_vol = int(group['Task Volume'].sum())
        p_comp = int(group['Tasks Completed'].sum())
        p_err = int(group['Error Count'].sum())
        p_rew = int(group['Rework Count'].sum())
        p_cost = float(group['Process Cost'].sum())
        p_sla_yes = len(group[group['SLA Achieved'] == 'Yes'])
        p_logs = len(group)
        
        proc_analysis.append({
            "process_name": proc_name,
            "department": group['Department'].iloc[0] if len(group) > 0 else "Unknown",
            "count": p_logs,
            "avg_cycle_time": round(float(group['Cycle Time (Hours)'].mean()), 2) if p_logs > 0 else 0.0,
            "std_cycle_time": round(float(group['Standard Cycle Time'].iloc[0]), 2) if p_logs > 0 else 0.0,
            "avg_productivity": round(float(group['Productivity %'].mean()), 2) if p_logs > 0 else 0.0,
            "avg_efficiency": round(float(group['Efficiency Ratio'].mean()), 2) if p_logs > 0 else 0.0,
            "sla_achievement_pct": round(float((p_sla_yes / p_logs) * 100), 2) if p_logs > 0 else 0.0,
            "total_cost": round(p_cost, 2),
            "error_rate_pct": round(float((p_err / p_vol) * 100), 2) if p_vol > 0 else 0.0,
            "rework_rate_pct": round(float((p_rew / p_vol) * 100), 2) if p_vol > 0 else 0.0
        })

    # ------------------ Monthly Trends ------------------
    df['Year-Month'] = df['Start Date'].dt.to_period('M').astype(str)
    month_grp = df.groupby('Year-Month')
    monthly_trends = []
    for month_name, group in month_grp:
        m_sla_yes = len(group[group['SLA Achieved'] == 'Yes'])
        m_logs = len(group)
        monthly_trends.append({
            "month": month_name,
            "count": m_logs,
            "total_cost": round(float(group['Process Cost'].sum()), 2),
            "avg_cycle_time": round(float(group['Cycle Time (Hours)'].mean()), 2) if m_logs > 0 else 0.0,
            "sla_achievement_pct": round(float((m_sla_yes / m_logs) * 100), 2) if m_logs > 0 else 0.0
        })

    # ------------------ Bottlenecks (Top 10 Slowest Employee/Process Combinations) ------------------
    bottleneck_grp = df.groupby(['Process Name', 'Employee Assigned', 'Department'])
    bottlenecks = []
    for keys, group in bottleneck_grp:
        proc_n, emp_n, dept_n = keys
        b_sla_yes = len(group[group['SLA Achieved'] == 'Yes'])
        b_logs = len(group)
        b_vol = int(group['Task Volume'].sum())
        b_err = int(group['Error Count'].sum())
        
        bottlenecks.append({
            "process_name": proc_n,
            "employee": emp_n,
            "department": dept_n,
            "count": b_logs,
            "avg_cycle_time": round(float(group['Cycle Time (Hours)'].mean()), 2) if b_logs > 0 else 0.0,
            "std_cycle_time": round(float(group['Standard Cycle Time'].iloc[0]), 2) if len(group) > 0 else 0.0,
            "sla_achievement_pct": round(float((b_sla_yes / b_logs) * 100), 2) if b_logs > 0 else 0.0,
            "avg_productivity": round(float(group['Productivity %'].mean()), 2) if b_logs > 0 else 0.0,
            "error_rate_pct": round(float((b_err / b_vol) * 100), 2) if b_vol > 0 else 0.0,
            "total_cost": round(float(group['Process Cost'].sum()), 2)
        })
    
    # Sort bottlenecks by avg_cycle_time deviation or descending cycle time (filtering for minimum 50 occurrences to show systemic issues)
    bottlenecks_df = pd.DataFrame(bottlenecks)
    systemic_bottlenecks = bottlenecks_df[bottlenecks_df['count'] >= 50]
    # Find ones with highest average cycle time relative to standard cycle time
    systemic_bottlenecks['deviation'] = systemic_bottlenecks['avg_cycle_time'] - systemic_bottlenecks['std_cycle_time']
    top_bottlenecks = systemic_bottlenecks.sort_values(by='deviation', ascending=False).head(10).drop(columns=['deviation']).to_dict(orient='records')

    # ------------------ Process Improvement Opportunities ------------------
    opp_counts = df['Improvement Opportunity'].value_counts()
    opportunities = []
    for opp_name, count in opp_counts.items():
        opportunities.append({
            "opportunity": opp_name,
            "count": int(count),
            "percentage": round(float((count / total_logs) * 100), 2) if total_logs > 0 else 0.0
        })

    # ------------------ Prepare Full Dashboard JSON ------------------
    dashboard_data = {
        "global_kpis": global_kpis,
        "department_analysis": dept_analysis,
        "process_analysis": proc_analysis,
        "monthly_trends": monthly_trends,
        "bottlenecks": top_bottlenecks,
        "opportunities": opportunities
    }

    # Verify and create output directory
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w') as f:
        json.dump(dashboard_data, f, indent=4)
    print(f"\nSuccessfully wrote aggregated dashboard data to {output_json_path}")

    # Also write a JS wrapped version to bypass local browser CORS policy
    output_js_path = output_json_path.replace(".json", ".js")
    with open(output_js_path, 'w') as f:
        f.write("const dashboardData = ")
        json.dump(dashboard_data, f, indent=4)
        f.write(";")
    print(f"Successfully wrote JS wrapped data to {output_js_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_csv = os.path.join(script_dir, "../data/raw_process_logs.csv")
    out_json = os.path.join(script_dir, "../dashboard/data/dashboard_data.json")
    run_analysis(raw_csv, out_json)
