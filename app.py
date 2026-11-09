
import os
import pandas as pd
from sqlalchemy import create_engine, text

# Read your PostgreSQL password from an environment variable
password = os.environ.get("CLINIFLOW_DB_PASSWORD")

if not password:
    raise ValueError(
        "Please set the CLINIFLOW_DB_PASSWORD environment variable."
    )

# Connect to your local PostgreSQL database
connection_url = (
    f"postgresql+psycopg://postgres:{""}"
    "@localhost:5433/cliniflow"
)

engine = create_engine(connection_url)

# Read appointment data into a Pandas DataFrame
query = """
SELECT
    d.department_name,
    a.status,
    a.wait_time_minutes,
    a.appointment_date
FROM appointments a
JOIN doctors doc
    ON a.doctor_id = doc.doctor_id
JOIN departments d
    ON doc.department_id = d.department_id
ORDER BY a.appointment_date;
"""

with engine.connect() as connection:
    df = pd.read_sql(text(query), connection)

print("\nCliniFlow appointment data:")
print(df.to_string(index=False))

print("\nTotal rows:", len(df))

print("\n--- CLINIFLOW DATA ANALYSIS ---")

# 1. Count appointments by status
print("\n1. Appointment count by status:")
print(df["status"].value_counts())

# 2. Calculate appointment completion rate
total_appointments = len(df)
completed = (df["status"] == "Completed").sum()

completion_rate = (
    completed / total_appointments * 100
    if total_appointments > 0 else 0
)

print(f"\n2. Total appointments: {total_appointments}")
print(f"Completed appointments: {completed}")
print(f"Completion rate: {completion_rate:.2f}%")

# 3. Calculate average wait by department
print("\n3. Average waiting time by department:")
completed_df = df[df["status"] == "Completed"]

average_wait = (
    completed_df.groupby("department_name")["wait_time_minutes"]
    .mean()
    .round(2)
    .sort_values(ascending=False)
)

print(average_wait)

# 4. Export appointment data for Power BI
df.to_csv("cliniflow_appointments.csv", index=False)

print("\n4. Export successful!")
print("File created: cliniflow_appointments.csv")

engine.dispose()


engine.dispose()

