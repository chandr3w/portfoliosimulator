#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy_financial as npf


# App Title
st.set_page_config(page_title="VC Fund Simulator", page_icon="https://atas.vc/img/favicon.png")
st.markdown('<a href="https://atas.vc/"><img src="https://atas.vc/img/logo.png" width="150"></a>', unsafe_allow_html=True)
st.markdown(
    "This open source model was developed by [Andrew Chan](https://www.linkedin.com/in/chandr3w/) "
    "from [Atas VC](https://atas.vc/)."
)

st.title('VC Portfolio Simulator')

# Sidebar inputs
stages = ['Pre-Seed', 'Seed', 'Series A', 'Series B']
st.sidebar.header('Fund Parameters')
fund_size = st.number_input("Fund Size ($MM)", min_value=1, max_value=500, value=100, step=1)
initial_stage = st.sidebar.selectbox('Initial Investment Stage', stages)
stage_index = stages.index(initial_stage)

# Management Fee
st.sidebar.header('Fund Management Fee')
management_fee_pct = st.sidebar.slider('Annual Management Fee (%)', 0.0, 5.0, 2.0, step=0.1)
management_fee_years = st.sidebar.slider('Years Management Fee is Charged', 1, 10, 10, step=1)
deployment_years = st.sidebar.slider('Number of Deployment Years', 1, 10, 5, step=1)

# Robust Portfolio Allocation
st.sidebar.header('Portfolio Allocation (%) per Stage')
valid_stages = stages[stage_index:]
stage_allocations = {}
allocation_values = []
remaining_alloc = 100

num_simulations = st.sidebar.slider('Number of Simulations', 1, 1000, 100)

# Default allocation map
default_allocation_map = {
    'Pre-Seed': 20,
    'Seed': 60,
    'Series A': 10,
    'Series B': 10
}

st.sidebar.header('Portfolio Allocation (%) per Stage')
valid_stages = stages[stage_index:]
stage_allocations = {}
allocation_values = []
remaining_alloc = 100

for i, stage in enumerate(valid_stages):
    default_value = default_allocation_map.get(stage, 0)
    # Cap default at remaining allocation
    default_slider_value = min(default_value, remaining_alloc)

    if i == len(valid_stages) - 1:
        allocation = remaining_alloc
        st.sidebar.write(f"Allocation to {stage}: {allocation}% (auto-set)")
    else:
        max_alloc = remaining_alloc
        if max_alloc == 0:
            allocation = 0
            st.sidebar.write(f"Allocation to {stage}: 0% (auto-set since fully allocated)")
        else:
            allocation = st.sidebar.slider(
                f'Allocation to {stage} (%)',
                min_value=0,
                max_value=max_alloc,
                value=default_slider_value,
                step=5
            )
        remaining_alloc -= allocation
    allocation_values.append(allocation)
    stage_allocations[stage] = allocation

if sum(allocation_values) != 100:
    st.sidebar.warning(f"Total allocation is {sum(allocation_values)}%. Adjust allocations to total exactly 100%.")

st.sidebar.header('Entry Valuations and Check Sizes per Stage ($MM)')
valuations, check_sizes = {}, {}

# Separate out each stage by individual Valuation
# stages = ['Pre-Seed', 'Seed', 'Series A', 'Series B']

valuations['Pre-Seed'] = st.sidebar.slider(f'Entry Valuation Range Pre-Seed', 2, 40, (3, 6), step=1)
check_sizes['Pre-Seed'] = st.sidebar.slider(f'Check Size Range Pre-Seed', 0.25, 3.0, (1.0, 1.5), step=0.25)

valuations['Seed'] = st.sidebar.slider(f'Entry Valuation Range Seed', 4, 50, (8, 15), step=1)
check_sizes['Seed'] = st.sidebar.slider(f'Check Size Range Seed', 0.25, 10.0, (2.0, 5.0), step=0.5)

valuations['Series A'] = st.sidebar.slider(f'Entry Valuation Range Series A', 20, 200, (40, 80), step=1)
check_sizes['Series A'] = st.sidebar.slider(f'Check Size Range Series A', 1.0, 20.0, (5.0, 10.0), step=1.0)

valuations['Series B'] = st.sidebar.slider(f'Entry Valuation Range Series B', 50, 400, (100, 150), step=5)
check_sizes['Series B'] = st.sidebar.slider(f'Check Size Range Series B', 1, 40, (5, 10), step=1)

st.sidebar.header('Stage Progression Probabilities (%)')
prob_advancement = {}
years_to_next = {}
for i in range(stage_index, len(stages)-1):
    if i==0:
        prob_advancement[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'{stages[i]} → {stages[i+1]}', 0, 100, 50, step=1)
        years_to_next[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'Years from {stages[i]} to {stages[i+1]}', 0, 10, (1,2), step=1)
    elif i==1:
        prob_advancement[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'{stages[i]} → {stages[i+1]}', 0, 100, 33, step=1)
        years_to_next[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'Years from {stages[i]} to {stages[i+1]}', 0, 10, (1,3), step=1)
        
    elif i==2:
        prob_advancement[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'{stages[i]} → {stages[i+1]}', 0, 100, 48, step=1)
        years_to_next[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'Years from {stages[i]} to {stages[i+1]}', 0, 10, (1,3), step=1)
        
prob_advancement['Series B to Series C'] = st.sidebar.slider('Series B → Series C', 0, 100, 43, step=1)
prob_advancement['Series C to IPO'] = st.sidebar.slider('Series C → IPO', 0, 100, 28, step=1)
years_to_next['Series B to Series C'] = st.sidebar.slider('Years from Series B to Series C', 0, 10, (1,3), step=1)
years_to_next['Series C to IPO'] = st.sidebar.slider('Years from Series C to IPO', 0, 10, (1,), step=1)

# Series B → Series C and Series C → IPO
#prob_advancement['Series B to Series C'] = st.sidebar.slider('Series B → Series C', 0, 100, 40, step=5)

#prob_advancement['Series C to IPO'] = st.sidebar.slider('Series C → IPO', 0, 100, 20, step=5)

st.sidebar.header('Dilution per Round (%)')
dilution = {}
for i in range(stage_index, len(stages)-1):
    dilution[stages[i]+' to '+stages[i+1]] = st.sidebar.slider(f'Dilution {stages[i]} → {stages[i+1]}', 0, 100, (10,25), step=5)
dilution['Series B to Series C'] = st.sidebar.slider('Dilution Series B → Series C', 0, 100, (10,15), step=5)
dilution['Series C to IPO'] = st.sidebar.slider('Dilution Series C → IPO', 0, 100, (10,15), step=5)

st.sidebar.header('Exit Valuations and Loss Ratio ($MM)')
exit_valuations = {}
zero_probabilities = {}
for stage in valid_stages + ['Series C', 'IPO']:
    if stage == 'Pre-Seed':
        exit_valuations[stage] = st.sidebar.slider(f'Exit Valuation at {stage}', 2, 20, (4, 10), step=1)
        zero_probabilities[stage] = st.sidebar.slider(f'Probability of Total Loss at {stage} (%)', 0, 100, 30, step=5)
    elif stage == 'Seed':
        exit_valuations[stage] = st.sidebar.slider(f'Exit Valuation at {stage}', 2, 40, (5, 10), step=1)
        zero_probabilities[stage] = st.sidebar.slider(f'Probability of Total Loss at {stage} (%)', 0, 100, 30, step=5)

    elif stage == 'Series A':
        exit_valuations[stage] = st.sidebar.slider(f'Exit Valuation at {stage}', 10, 100, (20, 40), step=1)
        zero_probabilities[stage] = st.sidebar.slider(f'Probability of Total Loss at {stage} (%)', 0, 100, 30, step=5)

    elif stage == 'Series B':
        exit_valuations[stage] = st.sidebar.slider(f'Exit Valuation at {stage}', 20, 200, (40, 120), step=1)
        zero_probabilities[stage] = st.sidebar.slider(f'Probability of Total Loss at {stage} (%)', 0, 100, 20, step=5)
    elif stage == 'Series C':
        exit_valuations[stage] = st.sidebar.slider(f'Exit Valuation at {stage}', 100, 1000, (200, 500), step=10)
        zero_probabilities[stage] = st.sidebar.slider(f'Probability of Total Loss at {stage} (%)', 0, 100, 20, step=5)

    elif stage == 'IPO':
        exit_valuations[stage] = st.sidebar.slider(f'Exit Valuation at {stage}', 1000, 10000, (1000, 2000), step=100)
        zero_probabilities[stage] = st.sidebar.slider(f'Probability of Total Loss at {stage} (%)', 0, 100, 0, step=5)
    else:
        continue
        


# Simulation function
def simulate_portfolio():
    investments = []

    for stage in valid_stages:
        allocation_amount = (stage_allocations[stage] / 100) * fund_size
        deployed_in_stage = 0

        while deployed_in_stage < allocation_amount:
            valuation = np.random.uniform(*valuations[stage])
            check_size = np.random.uniform(*check_sizes[stage])
            check_size = min(check_size, allocation_amount - deployed_in_stage)
            deployed_in_stage += check_size
            equity = check_size / valuation

            investment = {'Entry Stage': stage, 'Entry Amount': check_size}
            current_stage = stage

            stages_sequence = stages[stages.index(stage):] + ['Series C', 'IPO']
            for i, next_stage in enumerate(stages_sequence[1:], start=stages.index(stage)):
                key = stages_sequence[i-1] + ' to ' + next_stage
                if np.random.rand() * 100 <= prob_advancement.get(key, 0):
                    dilution_pct = np.random.uniform(*dilution.get(key, (0,0))) / 100
                    equity *= (1 - dilution_pct)
                    current_stage = next_stage
                else:
                    break

            if np.random.rand() * 100 <= zero_probabilities.get(current_stage, 0):
                exit_amount = 0
            else:
                exit_valuation = np.random.uniform(*exit_valuations[current_stage])
                exit_amount = equity * exit_valuation
            investment.update({'Exit Stage': current_stage, 'Exit Amount': exit_amount})
            investments.append(investment)

    return pd.DataFrame(investments)

# Run simulations
all_sim_results = [simulate_portfolio() for _ in range(num_simulations)]
paid_in = [res['Entry Amount'].sum() for res in all_sim_results]
distributions = [res['Exit Amount'].sum() for res in all_sim_results]
moics = [d/p for d,p in zip(distributions, paid_in)]

# Calculate fund-level IRR based on simulated cash flows
adjusted_irrs = []
realized_years_list = []
for sim_df in all_sim_results:
    cash_flows_by_year = {}
    sim_df['Deployment Year'] = np.random.randint(0, deployment_years, size=len(sim_df))

    # Track entries and exits by year with stage-based holding period
    for _, inv in sim_df.iterrows():
        year = inv['Deployment Year']
        cash_flows_by_year[year] = cash_flows_by_year.get(year, 0) - inv['Entry Amount']

        # Use years from stage sliders (range or fixed) and sum per stage
        entry_stage = inv['Entry Stage']
        exit_stage = inv['Exit Stage']
        stage_order = stages + ['Series C', 'IPO']
        entry_index = stage_order.index(entry_stage)
        exit_index = stage_order.index(exit_stage)

        hold_years = 0
        for i in range(entry_index, exit_index):
            key = stage_order[i] + ' to ' + stage_order[i + 1]
            years_slider = years_to_next.get(key, 0)
            # If the slider is a range, sample from it
            if isinstance(years_slider, tuple):
                stage_years = np.random.uniform(*years_slider)
            else:
                stage_years = years_slider
            hold_years += stage_years

        exit_year = year + int(np.ceil(hold_years))
        cash_flows_by_year[exit_year] = cash_flows_by_year.get(exit_year, 0) + inv['Exit Amount']

    # Add annual management fees during deployment
    for fee_year in range(management_fee_years):
        fee = fund_size * (management_fee_pct / 100)
        cash_flows_by_year[fee_year] = cash_flows_by_year.get(fee_year, 0) - fee

    # Re-indent IRR calculation inside the simulation loop
    max_exit_year = max(cash_flows_by_year.keys())
    years = range(0, max_exit_year + 1)
    cash_flows = [cash_flows_by_year.get(y, 0) for y in years]

    # Use the exact cash_flow_schedule logic for IRR calculation
    cash_flow_schedule = pd.DataFrame(sorted(cash_flows_by_year.items()), columns=["Year", "Net Cash Flow"])
    cash_flow_list = cash_flow_schedule['Net Cash Flow'].tolist()

    if all(c <= 0 for c in cash_flow_list[1:]):
        fund_irr = 0
    else:
        try:
            irr_val = npf.irr(cash_flow_list)
            fund_irr = 0 if (irr_val is None or np.isnan(irr_val)) else irr_val * 100
        except:
            fund_irr = 0

    adjusted_irrs.append(fund_irr)
    realized_years_list.append(max_exit_year)





# Apply Management Fee
fund_life_years = 10
management_fees = [fund_size * (management_fee_pct / 100) * management_fee_years for _ in paid_in]
adjusted_distributions = [d - fee for d, fee in zip(distributions, management_fees)]
adjusted_moics = [max(d / p, 0) for d, p in zip(adjusted_distributions, paid_in)]


# Display summary statistics
st.subheader("Simulation Summary Statistics")
# First row of metrics
row1 = st.columns(4)
for col, metric, val in zip(
    row1,
    ["Paid-in", "Distributed", "MOIC", "Mean IRR %"],
    [
        np.mean(paid_in),
        np.mean(distributions),
        np.mean(moics),
        np.mean(adjusted_irrs)
    ]
):
    col.metric(f"{metric}", f"{val:,.2f}")

# Second row of metrics
row2 = st.columns(4)
for col, metric, val in zip(
    row2,
    ["Net DPI", "# Investments", "Mgmt Fees"],
    [
                np.mean([ad / p for ad, p in zip(adjusted_distributions, paid_in)]),  # Net DPI after fees
        np.mean([len(r) for r in all_sim_results]),
        np.mean(management_fees)
    ]
):
    if metric == "Mgmt Fees":
        col.metric(f"{metric}", f"${val:,.2f}MM")
    else:
        col.metric(f"{metric}", f"{val:.2f}")

# MOIC Distribution
st.subheader("Distribution of Fund MOIC")
fig, ax = plt.subplots(figsize=(8, 4), dpi=120)
sns.histplot(moics, bins=15, kde=True, ax=ax)
st.pyplot(fig)

# Stacked Bar Chart - Entry vs Exit per Investment
st.subheader("Entry Capital vs. Exit Value per Investment (Sample Simulation)")
sample_sim = all_sim_results[0].reset_index(drop=True)

fig, ax = plt.subplots(figsize=(12, 6), dpi=120)

# Compute gain/loss
exit_minus_entry = sample_sim['Exit Amount'] - sample_sim['Entry Amount']
gains = exit_minus_entry.clip(lower=0)
losses = exit_minus_entry.clip(upper=0)

# Plot entry amount
ax.bar(sample_sim.index, sample_sim['Entry Amount'], label='Initial Investment', color='skyblue')

# Plot gains in green
ax.bar(sample_sim.index, gains, bottom=sample_sim['Entry Amount'], label='Gain', color='seagreen', alpha=0.7)

# Plot losses in red
ax.bar(sample_sim.index, losses, bottom=sample_sim['Entry Amount'], label='Loss', color='crimson', alpha=0.7)

ax.set_xlabel('Investment #')
ax.set_ylabel('Value ($MM)')
ax.set_title('Stacked Entry Capital and Exit Value per Investment')
ax.legend()

st.pyplot(fig)


# Investment Schedule
st.subheader("Sample Simulation Investments")
st.dataframe(all_sim_results[0])
