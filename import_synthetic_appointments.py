import csv
import os
import sys
from pathlib import Path

import psycopg2

CSV_FILE = Path(
    r"E:\CliniFlow\synthetic_appointments_preview.csv"
)
EXPECTED_NEW = 8388
EXPECTED_TOTAL = 8400

DOCTORS = {
    "Cardiology": 1,
    "Dermatology": 2,
    "General Medicine": 3,
    "Orthopedics": 4,
}

STATUSES = {"Completed", "Booked", "Cancelled", "No-show"}


def load_and_validate_csv():
    with CSV_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    if len(rows) != EXPECTED_NEW:
        raise ValueError(f"Expected {EXPECTED_NEW} rows; got {len(rows)}")

    seen = set()

    for row in rows:
        sid = row["synthetic_appointment_id"]

        if sid in seen:
            raise ValueError(f"Duplicate synthetic ID: {sid}")
        seen.add(sid)

        if row["is_synthetic"] != "TRUE":
            raise ValueError("Synthetic label missing.")

        department = row["department_name"]
        if department not in DOCTORS:
            raise ValueError(f"Invalid department: {department}")

        if int(row["doctor_id"]) != DOCTORS[department]:
            raise ValueError("Doctor/department mismatch.")

        if not 1 <= int(row["patient_id"]) <= 8:
            raise ValueError("Invalid patient ID.")

        if row["status"] not in STATUSES:
            raise ValueError(f"Invalid status: {row['status']}")

        wait = row["wait_time_minutes"]

        if row["status"] == "Completed":
            if not wait or int(wait) < 0:
                raise ValueError("Invalid completed wait time.")
        elif wait:
            raise ValueError("Unexpected wait time for non-completed row.")

    return rows


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_FILE}")

    if not os.environ.get("CLINIFLOW_DB_PASSWORD"):
        raise RuntimeError(
            "Password variable missing. Set it in this PowerShell session."
        )

    rows = load_and_validate_csv()
    print("CSV validation passed:", len(rows), "rows")

    connection = psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="cliniflow",
        user=os.environ.get("CLINIFLOW_DB_USER"),
        password=os.environ.get("CLINIFLOW_DB_PASSWORD"),
    )

    try:
        connection.autocommit = False

        with connection.cursor() as cursor:
            # Lock the table against concurrent writes during this import.
            cursor.execute(
                "LOCK TABLE appointments IN SHARE ROW EXCLUSIVE MODE"
            )

            cursor.execute("SELECT COUNT(*) FROM appointments")
            before_count = cursor.fetchone()[0]

            if before_count != 12:
                raise ValueError(
                    f"Expected 12 existing appointments; found {before_count}. "
                    "Nothing was imported."
                )

            cursor.execute("""
                SELECT COUNT(*)
                FROM patients
                WHERE patient_id BETWEEN 1 AND 8
            """)
            if cursor.fetchone()[0] != 8:
                raise ValueError("Expected patient IDs 1 through 8.")

            cursor.execute("""
                SELECT COUNT(*)
                FROM doctors
                WHERE (doctor_id, department_id) IN (
                    (1, 1), (2, 2), (3, 3), (4, 4)
                )
            """)
            if cursor.fetchone()[0] != 4:
                raise ValueError("Doctor/department mapping changed.")

            for row in rows:
                wait = row["wait_time_minutes"]
                cursor.execute(
                    """
                    INSERT INTO appointments
                        (patient_id, doctor_id, appointment_date,
                         status, wait_time_minutes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        int(row["patient_id"]),
                        int(row["doctor_id"]),
                        row["appointment_date"],
                        row["status"],
                        int(wait) if wait else None,
                    ),
                )

            cursor.execute("SELECT COUNT(*) FROM appointments")
            after_count = cursor.fetchone()[0]

            if after_count != EXPECTED_TOTAL:
                raise ValueError(
                    f"Expected {EXPECTED_TOTAL} total rows; got {after_count}"
                )

            cursor.execute("""
                SELECT COUNT(*)
                FROM appointments
                WHERE appointment_id <= 12
            """)
            original_count = cursor.fetchone()[0]

            if original_count != 12:
                raise ValueError("Original appointment IDs changed.")

        # Only commit after every check has passed.
        connection.commit()

        print("Import committed successfully.")
        print("Original appointments preserved:", original_count)
        print("New synthetic appointments:", EXPECTED_NEW)
        print("Final appointment count:", after_count)

    except Exception:
        connection.rollback()
        print("Import failed. Transaction rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error)
        sys.exit(1)