import streamlit as st

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# LOAD DATA
# -------------------------
df = pd.read_excel("combined.xlsx")

# -------------------------
# FILTER (пример)
# -------------------------
company = st.selectbox("Company", df["company"].unique())

filtered = df[df["company"] == company]

# -------------------------
# PLOT
# -------------------------
fig, ax = plt.subplots(figsize=(10, 7))

mean_value = filtered['Литри'].mean()

ax.bar(filtered['Дата'], filtered['Литри'])
ax.axhline(mean_value, color='red', linestyle='--', linewidth=2, label='Mean value')

ax.set_title(f'Diesel Economy [{company}]')
ax.set_xlabel('Дата')
ax.set_ylabel('Количество')
ax.legend()

plt.xticks(rotation=90)

# -------------------------
# SHOW IN DASHBOARD
# -------------------------
st.pyplot(fig)