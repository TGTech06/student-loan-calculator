import streamlit as st
import pandas as pd
import numpy as np
import uuid  # Added to assign unique IDs to dynamic rows
from datetime import datetime
import plotly.express as px

# -------------------------
# Custom CSS: Minimal styling and hide spinner for salary inputs only
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
    /* Only set fixed height when the screen is wide */
    @media (min-width: 600px) {
        .remove-button-container {
            display: flex;
            align-items: flex-end;
            height: 28px;
        }
    }
    /* On smaller screens, let the height adjust automatically */
    @media (max-width: 640px) {
        .remove-button-container {
            display: flex;
            align-items: flex-end;
            height: auto;
        }
    }
    /* Hide the spinner for salary number inputs (keys starting with 'salary_') */
    input[id^="salary_"]::-webkit-inner-spin-button,
    input[id^="salary_"]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    input[id^="salary_"] {
        -moz-appearance: textfield;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# App Title and Disclaimer
# -------------------------
st.title("UK Student Loan Repayment Simulator")
st.markdown("#### Calculate your repayment over 40 years")
st.markdown("""
**Disclaimer:** This tool is for informational purposes only and does not constitute financial advice.  
Always verify with an official source such as the UK Government website [https://www.gov.uk/repaying-your-student-loan](https://www.gov.uk/repaying-your-student-loan) before making financial decisions. I am not responsible for any inaccuracies or decisions made based on this tool.
""", unsafe_allow_html=True)

# -------------------------
# Student Loan Details Inputs
# -------------------------
st.markdown("### Student Loan Details")
tuition_loan = st.number_input(
    "Tuition Loan Amount (£ per year)", 
    value=9535.0, 
    step=100.0,
    format="%.2f"
)
maintenance_loan = st.number_input(
    "Maintenance Loan Amount (£ per year)", 
    value=6647.0, 
    step=100.0,
    format="%.2f"
)
study_years = st.number_input("Number of Years of Study", value=4, step=1)

# -------------------------
# Dynamic Salary Timeline Inputs (Working Perfectly)
# -------------------------
st.markdown("### Salary Timeline")
st.markdown("""
Enter your estimated annual salary (accounting for inflation) and the number of years at this salary.  
**Examples:** Entry Level – £30,000 for 5 years, Mid Level – £50,000 for 10 years, Senior – £70,000 until retirement.  
For the final row, enter **0** in "Years at this salary" to continue until the end of the simulation.
""")

if "salary_rows" not in st.session_state:
    st.session_state.salary_rows = [
        {"id": str(uuid.uuid4()), "salary": 30000.0, "years": 5},
        {"id": str(uuid.uuid4()), "salary": 50000.0, "years": 10},
        {"id": str(uuid.uuid4()), "salary": 70000.0, "years": 0}  # 0 means indefinite
    ]

def add_salary_row():
    st.session_state.salary_rows.append({"id": str(uuid.uuid4()), "salary": 0.0, "years": 0})

def remove_salary_row(row_id):
    st.session_state.salary_rows = [row for row in st.session_state.salary_rows if row["id"] != row_id]
    if len(st.session_state.salary_rows) == 0:
        st.session_state.salary_rows.append({"id": str(uuid.uuid4()), "salary": 0.0, "years": 0})

for row in st.session_state.salary_rows:
    cols = st.columns([3, 3, 1])
    with cols[0]:
        row["salary"] = st.number_input(
            label=f"Salary (£ per year)",
            value=row["salary"],
            key=f"salary_{row['id']}",
            format="%.2f",
            step=1000.0  # Change salary in steps of 1,000
        )
    with cols[1]:
        row["years"] = st.number_input(
            label=f"Years at this salary\n(Enter 0 for indefinite)",
            value=int(row["years"]),
            key=f"years_{row['id']}",
            step=1,
            format="%d"
        )
    with cols[2]:
        st.markdown("<div class='remove-button-container'>", unsafe_allow_html=True)
        st.button("Remove", key=f"remove_salary_{row['id']}", on_click=remove_salary_row, args=(row["id"],))
        st.markdown("</div>", unsafe_allow_html=True)
st.button("Add Salary Row", on_click=add_salary_row)

salary_df = pd.DataFrame(st.session_state.salary_rows)

# -------------------------
# Dynamic Inflation Timeline Inputs
# -------------------------
st.markdown("### Inflation Timeline")
st.markdown("""
Enter the estimated annual inflation rate and the number of years that rate applies.  
For the final row, enter **0** in "Years" to continue until the end of the simulation.  
**For loans taken out from 2023 (Plan 5):** Interest is charged at the Retail Price Index (RPI).  
**For loans taken out before 2023 (Plan 2):** Interest is charged at RPI + 3%.  
More details can be found on the [government website](https://www.gov.uk/repaying-your-student-loan/what-you-pay).
""")

if "inflation_rows" not in st.session_state:
    st.session_state.inflation_rows = [
        {"id": str(uuid.uuid4()), "inflation": 4.3, "years": 10},
        {"id": str(uuid.uuid4()), "inflation": 5, "years": 30}
    ]

def add_inflation_row():
    st.session_state.inflation_rows.append({"id": str(uuid.uuid4()), "inflation": 0.0, "years": 0})
    # No experimental_rerun() to avoid lag

def remove_inflation_row(row_id):
    st.session_state.inflation_rows = [row for row in st.session_state.inflation_rows if row["id"] != row_id]
    if len(st.session_state.inflation_rows) == 0:
        st.session_state.inflation_rows.append({"id": str(uuid.uuid4()), "inflation": 0.0, "years": 0})
    # No experimental_rerun() to avoid lag

for row in st.session_state.inflation_rows:
    cols = st.columns([3, 3, 1])
    with cols[0]:
        row["inflation"] = st.number_input(
            label=f"Inflation Rate % (Row)",
            value=row["inflation"],
            key=f"inflation_{row['id']}"
        )
    with cols[1]:
        row["years"] = st.number_input(
            label=f"Years\n(Enter 0 for indefinite)",
            value=int(row["years"]),
            key=f"inflation_years_{row['id']}",
            step=1,
            format="%d"
        )
    with cols[2]:
        st.markdown("<div class='remove-button-container'>", unsafe_allow_html=True)
        st.button("Remove", key=f"remove_inflation_{row['id']}", on_click=remove_inflation_row, args=(row["id"],))
        st.markdown("</div>", unsafe_allow_html=True)
st.button("Add Inflation Row", on_click=add_inflation_row)

inflation_df = pd.DataFrame(st.session_state.inflation_rows)

# -------------------------
# Dynamic Extra Repayment Timeline Inputs
# -------------------------
st.markdown("### Extra Repayments")
st.markdown("""
Enter the extra repayment amount you can contribute (per month), the **start month** (relative to your repayment start) and the **duration in months**.  
For the final row, enter **0** in "Duration in Months" to continue until the end of the simulation.
""")

if "extra_repayment_rows" not in st.session_state:
    st.session_state.extra_repayment_rows = [
        {"id": str(uuid.uuid4()), "extra_payment": 0.0, "start_month": 1, "duration_months": 0}
    ]

def add_extra_row():
    st.session_state.extra_repayment_rows.append({"id": str(uuid.uuid4()), "extra_payment": 0.0, "start_month": 1, "duration_months": 0})
    # No experimental_rerun() to avoid lag

def remove_extra_row(row_id):
    st.session_state.extra_repayment_rows = [row for row in st.session_state.extra_repayment_rows if row["id"] != row_id]
    if len(st.session_state.extra_repayment_rows) == 0:
        st.session_state.extra_repayment_rows.append({"id": str(uuid.uuid4()), "extra_payment": 0.0, "start_month": 1, "duration_months": 0})
    # No experimental_rerun() to avoid lag

for row in st.session_state.extra_repayment_rows:
    cols = st.columns([3, 3, 3, 1.5])
    with cols[0]:
        row["extra_payment"] = st.number_input(
            label="Extra Payment\n(£ per month)",
            value=row["extra_payment"],
            key=f"extra_payment_{row['id']}",
            format="%.2f",
            step=50.0
        )
    with cols[1]:
        row["start_month"] = st.number_input(
            label="Start Month\n(Relative to repayment start)",
            value=row["start_month"],
            key=f"extra_start_month_{row['id']}",
            step=1,
            format="%d"
        )
    with cols[2]:
        row["duration_months"] = st.number_input(
            label="Duration in Months\n(Enter 0 for indefinite)",
            value=row["duration_months"],
            key=f"extra_duration_{row['id']}",
            step=1,
            format="%d"
        )
    with cols[3]:
        st.markdown("<div class='remove-button-container'>", unsafe_allow_html=True)
        st.button("Remove", key=f"remove_extra_{row['id']}", on_click=remove_extra_row, args=(row["id"],))
        st.markdown("</div>", unsafe_allow_html=True)
st.button("Add Extra Repayment Row", on_click=add_extra_row)

extra_df = pd.DataFrame(st.session_state.extra_repayment_rows)

# -------------------------
# Calculation Information (Moved Just Above the Run Button)
# -------------------------
st.markdown("#### Calculation Information")
st.markdown("""
- **Regular Repayment:** Calculated as 9% of your annual income above £25,000 (pre‑tax).  
- **Extra Repayments:** Any extra repayment is applied directly to your outstanding loan balance, reducing future interest accrual and potentially shortening your repayment period.
""")

# -------------------------
# Other Repayment Details & Constants
# -------------------------
repayment_threshold = 27295  # UK Plan 2 annual threshold

# -------------------------
# Simulation Function with Extra Repayments
# -------------------------
def simulate_repayment(salary_df, inflation_df, starting_loan, total_years=40):
    total_months = total_years * 12  # 40 years
    # Set simulation start date: current year + study years + 1
    start_year = datetime.now().year + int(study_years) + 1
    start_date = pd.to_datetime(f"{start_year}-01-01")
    
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
        # For the "years" value: 0 means indefinite, so treat as None.
        yrs = int(row["years"]) if row["years"] != 0 else None
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
            yrs_val = int(row["years"]) if row["years"] != 0 else None
        except Exception:
            yrs_val = None
        if yrs_val is None:
            months = total_months - inflation_assigned
        else:
            months = int(yrs_val * 12)
        months = min(months, total_months - inflation_assigned)
        month_inflation_schedule.extend([inf_rate] * months)
        inflation_assigned += months
        if inflation_assigned >= total_months:
            break
    if inflation_assigned < total_months:
        last_inf = month_inflation_schedule[-1] if month_inflation_schedule else 0
        extra_months = total_months - inflation_assigned
        month_inflation_schedule.extend([last_inf] * extra_months)
    
    # Build month-by-month extra repayment schedule.
    extra_repayment_schedule = [0.0] * total_months
    if "extra_repayment_rows" in st.session_state:
        for row in st.session_state.extra_repayment_rows:
            try:
                extra_amount = float(row["extra_payment"])
            except Exception:
                extra_amount = 0.0
            # Adjust for 0-based indexing: if user enters month 1, start at index 0.
            start_month_offset = int(row["start_month"]) - 1  
            duration = int(row["duration_months"])
            if duration == 0:
                months_active = total_months - start_month_offset
            else:
                months_active = duration
            for m in range(start_month_offset, min(start_month_offset + months_active, total_months)):
                extra_repayment_schedule[m] += extra_amount
    
    # -------------------------
    # Simulation Loop
    # -------------------------
    loan_repaid_month = None  # Month when loan is fully repaid
    balance = starting_loan
    cumulative_paid = 0.0

    months_list = []
    dates_list = []
    salary_list = []
    regular_payment_list = []
    extra_payment_list = []
    total_payment_list = []
    balance_list = []
    cumulative_paid_list = []
    interest_list = []
    bracket_list = []
    min_salary_list = []  # Minimum salary required to cover interest

    for month in range(total_months):
        current_salary = month_salary_schedule[month]
        current_inf = month_inflation_schedule[month]
        current_monthly_inflation = (current_inf / 100) / 12

        # Regular monthly payment from salary (if above threshold)
        if current_salary > repayment_threshold:
            regular_payment = ((current_salary - repayment_threshold) * 0.09) / 12
        else:
            regular_payment = 0.0

        # Extra payment from extra repayments schedule
        extra_payment = extra_repayment_schedule[month]

        # Total scheduled payment before capping by remaining balance
        scheduled_payment = regular_payment + extra_payment

        # Accrue interest first
        interest = balance * current_monthly_inflation
        balance += interest

        # Cap payment if it exceeds remaining balance
        if scheduled_payment > balance:
            # Apply regular payment first, then extra repayment as possible.
            if regular_payment >= balance:
                regular_payment = balance
                extra_payment = 0.0
            else:
                extra_payment = balance - regular_payment
            scheduled_payment = balance

        balance -= scheduled_payment
        cumulative_paid += scheduled_payment

        # Calculate the minimum salary required to cover a year's worth of interest at this balance.
        min_salary = repayment_threshold + (balance * current_monthly_inflation * 12) / 0.09
        
        months_list.append(month + 1)
        current_date = start_date + pd.DateOffset(months=month)
        dates_list.append(current_date)
        salary_list.append(current_salary)
        regular_payment_list.append(regular_payment)
        extra_payment_list.append(extra_payment)
        total_payment_list.append(scheduled_payment)
        balance_list.append(balance)
        cumulative_paid_list.append(cumulative_paid)
        interest_list.append(interest)
        bracket_list.append(bracket_indices[month])
        min_salary_list.append(min_salary)

        if balance <= 0:
            loan_repaid_month = month + 1
            # Fill in remaining months with zeros if loan is repaid early.
            for extra_month in range(month+1, total_months):
                months_list.append(extra_month+1)
                current_date = start_date + pd.DateOffset(months=extra_month)
                dates_list.append(current_date)
                salary_list.append(month_salary_schedule[extra_month])
                regular_payment_list.append(0.0)
                extra_payment_list.append(0.0)
                total_payment_list.append(0.0)
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
        "Regular Payment": regular_payment_list,
        "Extra Payment": extra_payment_list,
        "Total Payment": total_payment_list,
        "Interest Accrued": interest_list,
        "Cumulative Paid": cumulative_paid_list,
        "Loan Balance": balance_list,
        "Bracket": bracket_list,
        "Minimum Salary (to Offset Interest)": min_salary_list
    })
    
    return sim_df, bracket_details, loan_repaid_month

# -------------------------
# Run Simulation Button
# -------------------------
if st.button("Run Simulation"):
    starting_loan = (tuition_loan + maintenance_loan) * study_years
    colA, colB = st.columns(2)
    with colA:
        st.metric("Starting Loan (when you graduate)", f"£{starting_loan:,.2f}")
    try:
        first_inflation = float(inflation_df.iloc[0]["inflation"])
    except Exception:
        first_inflation = 2.0
    first_monthly_inflation = (first_inflation / 100) / 12
    initial_min_salary = repayment_threshold + (starting_loan * first_monthly_inflation * 12) / 0.09
    with colB:
        st.metric("Initial Minimum Salary to Offset Interest", f"£{initial_min_salary:,.2f}")
    
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
       
        total_repaid = sim_df['Cumulative Paid'].iloc[-1]
        total_months = 40 * 12
        if loan_repaid_month is not None:
            avg_monthly_repayment = total_repaid / loan_repaid_month
        else:
            avg_monthly_repayment = total_repaid / total_months
        
        colC, colD = st.columns(2)
        with colC:
            st.metric("Total Amount Repaid", f"£{total_repaid:,.2f}")
        with colD:
            st.metric("Average Monthly Repayment", f"£{avg_monthly_repayment:,.2f}")
                
        # -------------------------
        # Pie Chart for Repayment Breakdown using Plotly
        # -------------------------
        if loan_repaid_month is not None:
            labels = ["Original Loan", "Interest Paid"]
            interest_paid = total_repaid - starting_loan
            values = [starting_loan, interest_paid]
            title = "Breakdown of Total Repayments: Original Loan vs Interest"
            color_sequence = ["forestgreen", "darkorange"]
        else:
            labels = ["Amount Repaid", "Outstanding Balance"]
            values = [total_repaid, sim_df["Loan Balance"].iloc[-1]]
            title = "Repaid vs Outstanding Balance"
            color_sequence = ["crimson", "royalblue"]

        values = [round(v, 2) for v in values]
        pie_fig = px.pie(
            names=labels,
            values=values,
            title=title,
            template="plotly_white",
            color_discrete_sequence=color_sequence
        )
        pie_fig.update_traces(
            texttemplate='£%{value:,.2f}',
            textfont_size=20
        )
        st.plotly_chart(pie_fig, use_container_width=True)

        # Additional pie chart if not fully repaid and total repaid > starting loan.
        if loan_repaid_month is None and total_repaid > starting_loan:
            labels2 = ["Original Loan", "Interest Paid"]
            values2 = [starting_loan, total_repaid - starting_loan]
            title2 = "Breakdown: Original Loan vs Interest Paid"
            color_sequence2 = ["forestgreen", "darkorange"]
            values2 = [round(v, 2) for v in values2]
            pie_fig2 = px.pie(
                names=labels2,
                values=values2,
                title=title2,
                template="plotly_white",
                color_discrete_sequence=color_sequence2
            )
            pie_fig2.update_traces(
                texttemplate='£%{value:,.2f}',
                textfont_size=20
            )
            st.plotly_chart(pie_fig2, use_container_width=True)

        # -------------------------
        # Line Charts using Streamlit's st.line_chart
        # -------------------------
        sim_df_graph = sim_df.copy()
        sim_df_graph["Loan Balance"] = sim_df_graph["Loan Balance"].round(2)
        sim_df_graph["Total Payment"] = sim_df_graph["Total Payment"].round(2)
        sim_df_graph["Minimum Salary (to Offset Interest)"] = sim_df_graph["Minimum Salary (to Offset Interest)"].round(2)
        sim_df_graph = sim_df_graph.set_index("Date")
        
        st.markdown("#### Loan Balance Over Time")
        st.line_chart(sim_df_graph[["Loan Balance"]])
        st.markdown("#### Total Monthly Payment Over Time")
        st.line_chart(sim_df_graph[["Total Payment"]])
        st.markdown("#### Minimum Salary to Offset Interest Over Time")
        st.line_chart(sim_df_graph[["Minimum Salary (to Offset Interest)"]])
        
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
            "Avg Minimum Salary (to Offset Interest)": []
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
            total_payment_bracket = df_bracket["Total Payment"].sum()
            total_interest = df_bracket["Interest Accrued"].sum()
            avg_growth = total_interest / len(df_bracket) if len(df_bracket) > 0 else 0
            avg_min_salary = df_bracket["Minimum Salary (to Offset Interest)"].mean() if len(df_bracket) > 0 else 0
            
            summary_data["Salary (Annual, £)"].append(f"£{sal:,.0f}")
            years_in_bracket = len(df_bracket) / 12
            summary_data["Years in Bracket"].append(f"{years_in_bracket:.0f}")
            summary_data["Monthly Payment (£)"].append(round(m_payment, 2))
            summary_data["Annual Payment (£)"].append(round(annual_payment, 2))
            summary_data["Weekly Payment (£)"].append(round(weekly_payment, 2))
            summary_data["Total Payment in Bracket (£)"].append(round(total_payment_bracket, 2))
            summary_data["Total Interest Accrued (£)"].append(round(total_interest, 2))
            summary_data["Avg Loan Growth per Month (£)"].append(round(avg_growth, 2))
            summary_data["Avg Minimum Salary (to Offset Interest)"].append(round(avg_min_salary, 2))
            
            start_idx = end_idx
        
        summary_df = pd.DataFrame(summary_data)
        st.markdown("#### Salary Bracket Summary")
        st.dataframe(summary_df)
        
        # -------------------------
        # Final Month-by-Month Repayment Details (Rounded to 2dp)
        # -------------------------
        sim_df["Date"] = sim_df["Date"].apply(lambda x: x.date())
        final_df = sim_df.drop(columns=["Month", "Bracket"]).reset_index(drop=True)
        final_df = final_df.round(2)
        st.markdown("#### Month-by-Month Repayment Details")
        st.dataframe(final_df)
