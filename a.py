import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# -------------------------
# (Optional) Minimal Custom CSS for minor spacing adjustments
# -------------------------
st.markdown("""
    <style>
    .header {
        text-align: center;
        font-size: 1.75rem;
        color: #333;
    }
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# App Title
# -------------------------
st.title("UK Student Loan Repayment Simulator")
st.markdown("##### Calculate your repayment over 40 years")

# -------------------------
# Student Loan Details Inputs
# -------------------------
st.markdown("### Student Loan Details")
tuition_loan = st.number_input("Tuition Loan Amount (£ per year)", value=9550.0, step=100.0)
maintenance_loan = st.number_input("Maintenance Loan Amount (£ per year)", value=6647.0, step=100.0)
study_years = st.number_input("Number of Years of Study", value=4, step=1)

# -------------------------
# Dynamic Salary Timeline Inputs
# -------------------------
st.markdown("### Salary Timeline")
st.markdown("Enter the annual salary and the number of years at that salary. For the final row, leave 'Years' blank to continue until the end of the simulation.")

if "salary_rows" not in st.session_state:
    st.session_state.salary_rows = [
        {"salary": 30000.0, "years": "5"},
        {"salary": 40000.0, "years": "10"},
        {"salary": 50000.0, "years": ""}
    ]

def add_salary_row():
    st.session_state.salary_rows.append({"salary": 0.0, "years": ""})

def remove_salary_row(index):
    if len(st.session_state.salary_rows) > 1:
        st.session_state.salary_rows.pop(index)

for i, row in enumerate(st.session_state.salary_rows):
    cols = st.columns([3, 3, 1])
    with cols[0]:
        st.session_state.salary_rows[i]["salary"] = st.number_input(
            label=f"Salary (Row {i+1})",
            value=st.session_state.salary_rows[i]["salary"],
            key=f"salary_{i}"
        )
    with cols[1]:
        st.session_state.salary_rows[i]["years"] = st.text_input(
            label=f"Years (Row {i+1})",
            value=st.session_state.salary_rows[i]["years"],
            key=f"years_{i}"
        )
    with cols[2]:
        st.button("Remove", key=f"remove_salary_{i}", on_click=remove_salary_row, args=(i,))
st.button("Add Salary Row", on_click=add_salary_row)
salary_df = pd.DataFrame(st.session_state.salary_rows)

# -------------------------
# Dynamic Inflation Timeline Inputs
# -------------------------
st.markdown("### Inflation Timeline")
st.markdown("Enter the annual inflation rate (%) and the number of years that rate applies. For the final row, leave 'Years' blank to continue until the end of the simulation.")

if "inflation_rows" not in st.session_state:
    st.session_state.inflation_rows = [
        {"inflation": 2.0, "years": "40"}
    ]

def add_inflation_row():
    st.session_state.inflation_rows.append({"inflation": 0.0, "years": ""})

def remove_inflation_row(index):
    if len(st.session_state.inflation_rows) > 1:
        st.session_state.inflation_rows.pop(index)

for i, row in enumerate(st.session_state.inflation_rows):
    cols = st.columns([3, 3, 1])
    with cols[0]:
        st.session_state.inflation_rows[i]["inflation"] = st.number_input(
            label=f"Inflation Rate % (Row {i+1})",
            value=st.session_state.inflation_rows[i]["inflation"],
            key=f"inflation_{i}"
        )
    with cols[1]:
        st.session_state.inflation_rows[i]["years"] = st.text_input(
            label=f"Years (Row {i+1})",
            value=st.session_state.inflation_rows[i]["years"],
            key=f"inflation_years_{i}"
        )
    with cols[2]:
        st.button("Remove", key=f"remove_inflation_{i}", on_click=remove_inflation_row, args=(i,))
st.button("Add Inflation Row", on_click=add_inflation_row)
inflation_df = pd.DataFrame(st.session_state.inflation_rows)

# -------------------------
# Other Repayment Details & Constants
# -------------------------
repayment_threshold = 27295  # UK Plan 2 annual threshold

# -------------------------
# Simulation Function
# -------------------------
def simulate_repayment(salary_df, inflation_df, starting_loan, total_years=40):
    total_months = total_years * 12  # 40 years
    
    # Build month-by-month salary schedule.
    month_salary_schedule = []
    bracket_indices = []  # row index in salary_df for each month
    bracket_details = []  # list of tuples: (salary, months_in_bracket)
    assigned_months = 0
    for idx, row in salary_df.iterrows():
        try:
            sal = float(row["salary"])
        except Exception:
            st.error(f"Invalid salary value in row {idx+1}")
            return None, None, None
        try:
            yrs = float(row["years"]) if row["years"].strip() != "" else None
        except Exception:
            yrs = None
        if yrs is None:
            months = total_months - assigned_months
        else:
            months = int(yrs * 12)
        months = min(months, total_months - assigned_months)
        bracket_details.append((sal, months))
        month_salary_schedule.extend([sal] * months)
        bracket_indices.extend([idx] * months)
        assigned_months += months
        if assigned_months >= total_months:
            break
    if assigned_months < total_months:
        last_sal = bracket_details[-1][0] if bracket_details else 0
        extra_months = total_months - assigned_months
        bracket_details.append((last_sal, extra_months))
        month_salary_schedule.extend([last_sal] * extra_months)
        bracket_indices.extend([len(bracket_details)-1] * extra_months)
    
    # Build month-by-month inflation schedule.
    month_inflation_schedule = []
    inflation_assigned = 0
    for idx, row in inflation_df.iterrows():
        try:
            inf_rate = float(row["inflation"])
        except Exception:
            st.error(f"Invalid inflation rate in row {idx+1}")
            return None, None, None
        try:
            yrs = float(row["years"]) if row["years"].strip() != "" else None
        except Exception:
            yrs = None
        if yrs is None:
            months = total_months - inflation_assigned
        else:
            months = int(yrs * 12)
        months = min(months, total_months - inflation_assigned)
        month_inflation_schedule.extend([inf_rate] * months)
        inflation_assigned += months
        if inflation_assigned >= total_months:
            break
    if inflation_assigned < total_months:
        last_inf = month_inflation_schedule[-1] if month_inflation_schedule else 0
        extra_months = total_months - inflation_assigned
        month_inflation_schedule.extend([last_inf] * extra_months)
    
    # -------------------------
    # Simulation Loop
    # -------------------------
    balance = starting_loan
    cumulative_paid = 0.0

    months_list = []
    dates_list = []
    salary_list = []
    payment_list = []
    balance_list = []
    cumulative_paid_list = []
    interest_list = []
    bracket_list = []
    min_salary_list = []  # Dynamic minimum salary list
    
    start_date = pd.to_datetime("2030-01-01")
    loan_repaid_month = None

    for month in range(total_months):
        current_salary = month_salary_schedule[month]
        # Use current month's inflation rate.
        current_inf = month_inflation_schedule[month]
        current_monthly_inflation = (current_inf / 100) / 12

        # Calculate monthly payment if salary > threshold.
        if current_salary > repayment_threshold:
            monthly_payment = ((current_salary - repayment_threshold) * 0.09) / 12
        else:
            monthly_payment = 0.0

        # Compute interest and update balance.
        interest = balance * current_monthly_inflation
        balance += interest
        payment = monthly_payment if monthly_payment < balance else balance
        balance -= payment
        cumulative_paid += payment

        # Calculate dynamic minimum salary required to just cover interest.
        min_salary = repayment_threshold + (balance * current_monthly_inflation * 12) / 0.09
        
        months_list.append(month + 1)
        current_date = start_date + pd.DateOffset(months=month)
        dates_list.append(current_date)
        salary_list.append(current_salary)
        payment_list.append(payment)
        balance_list.append(balance)
        cumulative_paid_list.append(cumulative_paid)
        interest_list.append(interest)
        bracket_list.append(bracket_indices[month])
        min_salary_list.append(min_salary)

        if balance <= 0:
            loan_repaid_month = month + 1
            for extra_month in range(month+1, total_months):
                months_list.append(extra_month+1)
                current_date = start_date + pd.DateOffset(months=extra_month)
                dates_list.append(current_date)
                salary_list.append(month_salary_schedule[extra_month])
                payment_list.append(0.0)
                balance_list.append(0.0)
                cumulative_paid_list.append(cumulative_paid)
                interest_list.append(0.0)
                bracket_list.append(bracket_indices[extra_month])
                min_salary_list.append(repayment_threshold)
            break

    sim_df = pd.DataFrame({
        "Month": months_list,
        "Date": dates_list,
        "Salary": salary_list,
        "Monthly Payment": payment_list,
        "Interest Accrued": interest_list,
        "Cumulative Paid": cumulative_paid_list,
        "Loan Balance": balance_list,
        "Bracket": bracket_list,
        "Min Salary": min_salary_list
    })
    
    return sim_df, bracket_details, loan_repaid_month

# -------------------------
# Run Simulation Button and Simulation Summary
# -------------------------
if st.button("Run Simulation"):
    starting_loan = (tuition_loan + maintenance_loan) * study_years
    # Display key metrics using default Streamlit styles (st.metric, st.success/st.error)
    colA, colB = st.columns(2)
    with colA:
         st.metric("Starting Loan", f"£{starting_loan:,.2f}")
    try:
         first_inflation = float(inflation_df.iloc[0]["inflation"])
    except Exception:
         first_inflation = 2.0
    first_monthly_inflation = (first_inflation / 100) / 12
    initial_min_salary = repayment_threshold + (starting_loan * first_monthly_inflation * 12) / 0.09
    with colB:
         st.metric("Initial Minimum Salary to avoid loan growing", f"£{initial_min_salary:,.2f}")
    
    result = simulate_repayment(salary_df, inflation_df, starting_loan, total_years=40)
    if result[0] is None:
         st.error("Simulation failed due to input errors.")
    else:
         sim_df, bracket_details, loan_repaid_month = result
         st.markdown("### Simulation Summary")
         if loan_repaid_month:
             years = loan_repaid_month // 12
             rem_months = loan_repaid_month % 12
             st.success(f"### Loan fully repaid in {years} years, {rem_months} months.")
         else:
             st.error(f"##### Loan not fully repaid within 40 years. \n ### Outstanding Balance: £{sim_df['Loan Balance'].iloc[-1]:,.2f}")
         st.metric("Total Amount Repaid", f"£{sim_df['Cumulative Paid'].iloc[-1]:,.2f}")
         
         # -------------------------
         # Graphs (using default Streamlit styles)
         # -------------------------
         sim_df_graph = sim_df.copy()
         sim_df_graph["Loan Balance"] = sim_df_graph["Loan Balance"].round(2)
         sim_df_graph["Monthly Payment"] = sim_df_graph["Monthly Payment"].round(2)
         sim_df_graph["Min Salary"] = sim_df_graph["Min Salary"].round(2)
         sim_df_graph = sim_df_graph.set_index("Date")
         
         st.markdown("#### Loan Balance Over Time")
         st.line_chart(sim_df_graph[["Loan Balance"]])
         
         st.markdown("#### Monthly Payment Over Time")
         st.line_chart(sim_df_graph[["Monthly Payment"]])
         
         st.markdown("#### Minimum Salary (to avoid loan growing) Over Time")
         st.line_chart(sim_df_graph[["Min Salary"]])
         
         # -------------------------
         # Detailed Salary Bracket Summary
         # -------------------------
         summary_data = {
             "Salary (Annual, £)": [],
             "Years in Bracket": [],
             "Monthly Payment (£)": [],
             "Annual Payment (£)": [],
             "Weekly Payment (£)": [],
             "Total Payment in Bracket (£)": [],
             "Total Interest Accrued (£)": [],
             "Avg Loan Growth per Month (£)": [],
             "Avg Min Salary (£)": []
         }
         
         start_idx = 0
         for i, (sal, months_in_bracket) in enumerate(bracket_details):
             end_idx = start_idx + months_in_bracket
             df_bracket = sim_df[(sim_df["Month"] > start_idx) & (sim_df["Month"] <= end_idx)]
             if sal > repayment_threshold:
                 m_payment = ((sal - repayment_threshold) * 0.09) / 12
             else:
                 m_payment = 0.0
             annual_payment = m_payment * 12
             weekly_payment = annual_payment / 52
             total_payment = df_bracket["Monthly Payment"].sum()
             total_interest = df_bracket["Interest Accrued"].sum()
             avg_growth = total_interest / len(df_bracket) if len(df_bracket) > 0 else 0
             avg_min_salary = df_bracket["Min Salary"].mean() if len(df_bracket) > 0 else 0
             
             summary_data["Salary (Annual, £)"].append(f"£{sal:,.0f}")
             years_in_bracket = len(df_bracket) / 12
             summary_data["Years in Bracket"].append(round(years_in_bracket, 2))
             summary_data["Monthly Payment (£)"].append(round(m_payment, 2))
             summary_data["Annual Payment (£)"].append(round(annual_payment, 2))
             summary_data["Weekly Payment (£)"].append(round(weekly_payment, 2))
             summary_data["Total Payment in Bracket (£)"].append(round(total_payment, 2))
             summary_data["Total Interest Accrued (£)"].append(round(total_interest, 2))
             summary_data["Avg Loan Growth per Month (£)"].append(round(avg_growth, 2))
             summary_data["Avg Min Salary (£)"].append(round(avg_min_salary, 2))
             
             start_idx = end_idx
         
         summary_df = pd.DataFrame(summary_data)
         st.markdown("#### Salary Bracket Summary")
         st.dataframe(summary_df)
         
         st.markdown("#### Month-by-Month Repayment Details")
         st.dataframe(sim_df.round(2))
