import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# CliniFlow: synthetic appointment preview
# This script does NOT connect to PostgreSQL.

random.seed(42)

OUTPUT_FILE = Path(
    r"E:\CliniFlow\synthetic_appointments_preview.csv"
)

TOTAL_NEW_RECORDS = 8388

DEPARTMENTS = [
    ("Cardiology", 1),
    ("Dermatology", 2),
    ("General Medicine", 3),
    ("Orthopedics", 4),
]

STATUSES = ["Completed", "Booked", "Cancelled", "No-show"]
STATUS_WEIGHTS = [70, 15, 10, 5]

START_DATE = datetime(2025, 1, 1, 9, 0)
END_DATE = datetime(2026, 10, 1, 17, 0)

with OUTPUT_FILE.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "synthetic_appointment_id",
            "patient_id",
            "doctor_id",
            "department_name",
            "appointment_date",
            "status",
            "wait_time_minutes",
            "is_synthetic",
        ],
    )

    writer.writeheader()

    for number in range(1, TOTAL_NEW_RECORDS + 1):

        department_name, doctor_id = random.choice(DEPARTMENTS)
        appointment_date = START_DATE + timedelta(
            seconds=random.randint(
                0, int((END_DATE - START_DATE).total_seconds())
            )
        )

        status = random.choices(
            STATUSES, weights=STATUS_WEIGHTS, k=1
        )[0]

        wait_time = (
            random.randint(5, 90)
            if status == "Completed"
            else ""
        )

        writer.writerow({
            "synthetic_appointment_id": number,
            "patient_id": random.randint(1, 8),
            "doctor_id": doctor_id,
            "department_name": department_name,
            "appointment_date": appointment_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "status": status,
            "wait_time_minutes": wait_time,
            "is_synthetic": "TRUE",
        })

print("Synthetic preview created.")
print("New records:", TOTAL_NEW_RECORDS)
print("Output:", OUTPUT_FILE)
print("Original database and files were not changed.")