import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_process_logs(output_path, num_records=105000):
    print(f"Starting generation of {num_records} unique process logs...")
    np.random.seed(42)  # For reproducibility

    # 1. Define configuration for processes
    processes = {
        "Invoice Processing": {
            "dept": "Finance",
            "owner": "Sarah Jenkins",
            "std_cycle_time": 24.0,  # hours
            "base_cost": 15.0,
            "rework_multiplier": 5.0,
            "employees": [f"Fin_User_{i:02d}" for i in range(1, 11)],
            "base_error_rate": 0.05,
            "sla_target_hours": 24.0
        },
        "Customer Onboarding": {
            "dept": "Customer Service",
            "owner": "Marcus Vance",
            "std_cycle_time": 48.0,
            "base_cost": 50.0,
            "rework_multiplier": 15.0,
            "employees": [f"CS_User_{i:02d}" for i in range(1, 16)],
            "base_error_rate": 0.02,
            "sla_target_hours": 48.0
        },
        "IT Support Ticket": {
            "dept": "IT Operations",
            "owner": "Elena Rostova",
            "std_cycle_time": 12.0,
            "base_cost": 30.0,
            "rework_multiplier": 10.0,
            "employees": [f"IT_User_{i:02d}" for i in range(1, 9)],
            "base_error_rate": 0.04,
            "sla_target_hours": 12.0
        },
        "Employee Offboarding": {
            "dept": "Human Resources",
            "owner": "David Kross",
            "std_cycle_time": 72.0,
            "base_cost": 100.0,
            "rework_multiplier": 20.0,
            "employees": [f"HR_User_{i:02d}" for i in range(1, 6)],
            "base_error_rate": 0.01,
            "sla_target_hours": 72.0
        },
        "Order Fulfillment": {
            "dept": "Operations",
            "owner": "Jane Doe",
            "std_cycle_time": 8.0,
            "base_cost": 3.5,
            "rework_multiplier": 1.5,
            "employees": [f"Ops_User_{i:02d}" for i in range(1, 21)],
            "base_error_rate": 0.03,
            "sla_target_hours": 8.0
        }
    }

    process_keys = list(processes.keys())
    # Distribute logs: Operations (Fulfillment) is high volume, HR is low volume.
    process_probs = [0.15, 0.15, 0.20, 0.05, 0.45] 

    # 2. Date ranges (1 year)
    start_period = datetime(2025, 6, 1)
    end_period = datetime(2026, 6, 1)
    total_days = (end_period - start_period).days

    # Pre-generate lists for DF
    data = []

    for i in range(1, num_records + 1):
        process_id = f"PRC-2026-{i:06d}"
        
        # Select process type
        p_name = np.random.choice(process_keys, p=process_probs)
        config = processes[p_name]
        
        # Date selection
        random_days = np.random.randint(0, total_days)
        random_seconds = np.random.randint(0, 86400)
        start_date = start_period + timedelta(days=random_days, seconds=random_seconds)
        
        # Determine base attributes
        std_time = config["std_cycle_time"]
        emp = np.random.choice(config["employees"])
        
        # Volume details
        if p_name == "Order Fulfillment":
            volume = np.random.randint(10, 100)
        elif p_name == "Invoice Processing":
            volume = np.random.randint(1, 15)
        else:
            volume = 1

        # Introduce Bottlenecks programmatically (systemic variations)
        # Bottleneck 1: Invoice Processing (Finance) in Q4 (Oct-Dec) is overloaded
        is_q4 = start_date.month in [10, 11, 12]
        # Bottleneck 2: CS_User_03 and CS_User_07 are slow (Customer Service)
        is_slow_cs_user = (p_name == "Customer Onboarding" and emp in ["CS_User_03", "CS_User_07"])
        # Bottleneck 3: Operations Order Fulfillment has a supplier delay on Fridays/Saturdays
        is_ops_weekend = (p_name == "Order Fulfillment" and start_date.weekday() in [4, 5])

        # Calculate actual cycle time (hours)
        cycle_multiplier = 1.0
        error_rate_mod = 1.0

        if p_name == "Invoice Processing" and is_q4:
            cycle_multiplier += np.random.uniform(0.5, 1.2)  # 50% to 120% delay
            error_rate_mod += 1.5
        if is_slow_cs_user:
            cycle_multiplier += np.random.uniform(0.6, 1.5)  # slow employee bottleneck
            error_rate_mod += 0.5
        if is_ops_weekend:
            cycle_multiplier += np.random.uniform(0.4, 0.9)
            error_rate_mod += 1.2
            
        # Lognormal distribution for cycle time (realistic operational distributions)
        shape, scale = 0.25, std_time * cycle_multiplier
        cycle_time = round(np.random.lognormal(mean=np.log(scale), sigma=shape), 2)
        
        # End date calculation
        end_date = start_date + timedelta(hours=cycle_time)
        
        # Error and rework calculations
        error_rate = config["base_error_rate"] * error_rate_mod
        error_count = 0
        if volume > 1:
            error_count = int(np.random.binomial(volume, min(error_rate, 0.99)))
        else:
            if np.random.rand() < error_rate:
                error_count = 1
                
        rework_count = 0
        if error_count > 0:
            rework_count = np.random.randint(0, error_count + 1)
            
        tasks_completed = volume - error_count
        
        # Cost calculation
        proc_cost = round((volume * config["base_cost"]) + (rework_count * config["base_cost"] * config["rework_multiplier"] * 0.2), 2)
        
        # Productivity calculation
        # Normalized productivity % based on standard cycle time and completion rate
        efficiency_factor = std_time / max(cycle_time, 0.1)
        completion_factor = tasks_completed / volume if volume > 0 else 0
        prod_pct = round(min(125.0, max(15.0, efficiency_factor * completion_factor * 100)), 2)
        
        # Customer complaints
        complaint_prob = 0.01
        if cycle_time > config["sla_target_hours"]:
            complaint_prob += 0.15
        if error_count > 0:
            complaint_prob += 0.10
        
        customer_complaints = 1 if np.random.rand() < complaint_prob else 0
        
        # SLA targeting
        sla_target = config["sla_target_hours"]
        sla_achieved = "Yes" if cycle_time <= sla_target else "No"
        
        # Process status
        if cycle_time > sla_target * 1.5:
            p_status = "Delayed"
        elif np.random.rand() < 0.02:
            p_status = "Pending Approval"
        else:
            p_status = "Completed"
            
        # Opportunity Identification
        if cycle_time > sla_target * 1.4:
            opp = "Cycle Time Reduction (Resource Allocation)"
        elif error_count / volume > 0.10:
            opp = "Quality Audit & Staff Training"
        elif rework_count > 2:
            opp = "Rework Automation (RPA Implementation)"
        elif customer_complaints > 0:
            opp = "Client Feedback Loop Restructuring"
        elif prod_pct < 60.0:
            opp = "Resource Re-training"
        else:
            opp = "Continuous Monitoring"

        data.append([
            process_id, p_name, config["dept"], config["owner"],
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date.strftime("%Y-%m-%d %H:%M:%S"),
            cycle_time, std_time, emp, volume, tasks_completed,
            prod_pct, error_count, rework_count, proc_cost,
            customer_complaints, sla_target, sla_achieved, p_status, opp
        ])

        if i % 25000 == 0:
            print(f"Generated {i} records...")

    # Define columns
    columns = [
        "Process ID", "Process Name", "Department", "Process Owner",
        "Start Date", "End Date", "Cycle Time (Hours)", "Standard Cycle Time",
        "Employee Assigned", "Task Volume", "Tasks Completed", "Productivity %",
        "Error Count", "Rework Count", "Process Cost", "Customer Complaints",
        "SLA Target", "SLA Achieved", "Process Status", "Improvement Opportunity"
    ]

    df = pd.DataFrame(data, columns=columns)
    
    # Save directory verification
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated and saved {len(df)} records to {output_path}")

if __name__ == "__main__":
    output_file = "../data/raw_process_logs.csv"
    # Resolve relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(script_dir, output_file)
    generate_process_logs(target_path)
