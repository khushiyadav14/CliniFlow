
import os
import csv
import psycopg2

output_file = r"E:\CliniFlow\cliniflow_appointments_8400.csv"
password = os.environ.get("CLINIFLOW_DB_PASSWORD")

if not password:
    raise RuntimeError(
        "CLINIFLOW_DB_PASSWORD is missing. Use the PowerShell session "
        "where you set your database password."
    )

connection = psycopg2.connect(
    host="localhost",
    port=5433,
    database="cliniflow",
    user=os.environ.get("CLINIFLOW_DB_USER"),
    password=os.environ.get("CLINIFLOW_DB_PASSWORD"),
)

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                a.appointment_id,
                d.department_name,
                a.status,
                a.wait_time_minutes,
                a.appointment_date,
                CASE
                    WHEN a.appointment_id <= 12 THEN 'Original'
                    ELSE 'Synthetic'
                END AS data_origin
            FROM appointments AS a
            JOIN doctors AS doc
                ON a.doctor_id = doc.doctor_id
            JOIN departments AS d
                ON doc.department_id = d.department_id
            ORDER BY a.appointment_id;
        """)

        columns = [item[0] for item in cursor.description]

        with open(
            output_file, "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(cursor)

        print("Export completed successfully!")
        print("Columns:", ", ".join(columns))
        print("Rows exported:", 8400)
        print("Saved file:", output_file)

finally:
    connection.close()
