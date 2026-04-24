import time
import cv2 as cv
import sqlite3
from pyzbar.pyzbar import decode
from datetime import datetime, time as dtime, timedelta as dtime
import numpy as np

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()
cap = cv.VideoCapture(0)

def seconds_until_930pm(check_in_timestamp):
    last_checkin = datetime.fromtimestamp(check_in_timestamp)

    target = datetime.combine(
        last_checkin.date(),
        dtime(hour=21, minute=30)
    )

    return int((target - last_checkin).total_seconds())


def secondsToTotal(seconds):
    days = seconds // 86400
    seconds %= 86400

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60

    return f"{days} days, {hours} hours, {minutes} minutes"

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


def updateCheckOut(barcode, duration, timestamp):
    cursor.execute("""
    UPDATE attendance
    SET check_out = ?,
        total_time = total_time + ?,
        is_checked_in = 0
    WHERE barcode = ?
    """, (timestamp, duration, barcode))
    conn.commit()


def scanBarcode():
    frames = 0
    ret, frame = cap.read()
    if not ret:
        return None

    if frames < 7:
        green_overlay = np.full(frame.shape, (0, 255, 0), dtype=np.uint8)
        frame = cv.addWeighted(frame, 0.5, green_overlay, 0.5, 0)

    cv.imshow('frame', frame)

    results = decode(frame)
    frames += 1

    for r in results:
        data = r.data.decode()
        if data:
            frames = 0
            return data

    return None


def detectStudent(data):
    timestamp = time.time()
    student = getByBarcode(data)

    if not student:
        return

    is_checked_in = student[6]
    check_in = student[3]
    check_out = student[4]

    if is_checked_in == 1 and not check_in:
        return

    last_action_time = check_in if is_checked_in == 1 else check_out

    if last_action_time is not None and time.time() - last_action_time < 10:
        print("cant check in / out for 10s")
        return

    if is_checked_in == 0:
        print("checked in")
        updateCheckIn(data, timestamp)

    else:
        print("checked out")

        duration = int(timestamp - check_in)

        cutoff = seconds_until_930pm(check_in)

        if cutoff < duration:
            duration = max(0, cutoff)

        updateCheckOut(data, duration, timestamp)

    student = getByBarcode(data)
    print(f"time: {secondsToTotal(student[5])}")

while True:
    data = scanBarcode()

    if data:
        detectStudent(data)

    if cv.waitKey(1) == 27:
        break

    time.sleep(0.01)



# addStudent(id, name, barcode)

cap.release()
cv.destroyAllWindows()