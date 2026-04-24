import time
import cv2 as cv
import sqlite3
from pyzbar.pyzbar import decode

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

# DELETE LATER -------------------
def clearTable():
    cursor.execute("""
    DELETE FROM attendance
    """)
    conn.commit()
# DELETE LATER -------------------


def getAllStudents():
    cursor.execute("""
    SELECT * FROM attendance
    """)
    return cursor.fetchall()

def getByBarcode(barcode):
    cursor.execute("""
    SELECT * FROM attendance WHERE barcode = ?
    """, (barcode,))
    return cursor.fetchone()

def updateCheckIn(barcode, timestamp):
    cursor.execute("""
    UPDATE attendance
    SET check_in = ?, is_checked_in = 1
    WHERE barcode = ?
    """, (timestamp, barcode))
    conn.commit()

def updateCheckOut(barcode, check_in):
    timestamp = time.time()
    duration = int(timestamp - check_in)

    cursor.execute("""
    UPDATE attendance
    SET check_out = ?,
        total_time = total_time + ?,
        is_checked_in = 0
    WHERE barcode = ?
    """, (timestamp, duration, barcode))

    conn.commit()

def addStudent(id, name, barcode):
    cursor.execute("""
    INSERT OR IGNORE INTO attendance (id, name, barcode, check_in, check_out, total_time, is_checked_in)
    VALUES (?, ?, ?, NULL, NULL, 0, 0)
    """, (id, name, barcode))
    conn.commit()

def removeStudent(barcode):
    cursor.execute("""
    DELETE FROM attendance WHERE barcode = ?
    """, (barcode,))
    conn.commit()

def secondsToTotal(seconds):

    days = 0
    hours = 0
    minutes = 0

    if seconds > 86400:
        days = seconds // 86400
        seconds -= days * 86400
    if seconds > 3600:
        hours = seconds // 3600
        seconds -= hours * 3600
    if seconds > 60:
        minutes = seconds // 60
    print(f"{days} days, {hours} hours, {minutes} minutes")

def scanBarcode():
    cap = cv.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv.imshow('frame', frame)
        results = decode(frame)

        for r in results:
            data = r.data.decode()

            if data:
                cap.release()
                cv.destroyAllWindows()
                return data


def detectStudent():

    data = scanBarcode()

    timestamp = time.time()
    student = getByBarcode(data)

    if not student:
        return

    is_checked_in = student[6]
    check_in = student[3]

    last_action_time = student[3] if student[6] == 1 else student[4]

    if last_action_time is not None and time.time() - last_action_time < 10:
        print("cant check in / out for 10s")
        return

    if is_checked_in == 0:
        print("checked in")
        updateCheckIn(data, timestamp)
    else:
        print("checked out")
        updateCheckOut(data, check_in)

    student = getByBarcode(data)
    print(f"time: {student[5]}s")

    return

# test barcode = 0076950450479
# test 2 = 0051000012517

