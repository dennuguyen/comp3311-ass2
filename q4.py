#!/usr/bin/python3
# COMP3311 22T3 Ass2 ... print a transcript for a given student

import sys
import psycopg2
import re
from helpers import get_latest_student, get_full_transcript, print_transcript

argc = len(sys.argv)
if argc < 2:
    print(f"Usage: {sys.argv[0]} zID")
    exit(1)

zid = sys.argv[1]
if zid[0] == "z":
    zid = zid[1:8]

digits = re.compile("^\d{7}$")
if not digits.match(zid):
    print(f"Invalid student ID {zid}")
    exit(1)

conn = None

try:
    conn = psycopg2.connect("dbname=ass2")

    # Get student information.
    stu_info = get_latest_student(conn, zid)
    if not stu_info:
        print(f"Invalid student ID {zid}")
        exit(1)

    # Print header.
    print(f"{stu_info.zid} {stu_info.last_name}, {stu_info.first_name}")
    print(f"{stu_info.program_code} {stu_info.stream_code} {stu_info.program_name}")

    transcript, achieved_uoc, wam = get_full_transcript(conn, stu_info.zid)
    print_transcript(transcript, achieved_uoc, wam)

except Exception as err:
    print(err)
finally:
    if conn:
        conn.close()
