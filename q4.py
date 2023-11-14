#!/usr/bin/python3
# COMP3311 22T3 Ass2 ... print a transcript for a given student

import sys
import psycopg2
import re
from helpers import get_latest_student_info, get_transcript

argc = len(sys.argv)
if argc < 2:
    print(f"Usage: {sys.argv[0]} zID")
    exit(1)

zid = sys.argv[1]
if zid[0] == 'z':
    zid = zid[1:8]

digits = re.compile("^\d{7}$")
if not digits.match(zid):
    print(f"Invalid student ID {zid}")
    exit(1)

conn = psycopg2.connect("dbname=ass2")

try:
    stu_info = get_latest_student_info(conn, zid)
    if not stu_info:
        print(f"Invalid student ID {zid}")
        exit(1)

    print(f"{stu_info.zid} {stu_info.last_name}, {stu_info.first_name}")
    print(f"{stu_info.program_code} {stu_info.stream_code} {stu_info.program_name}")

    transcript = get_transcript(conn, stu_info.zid)

    wam = 0
    weighted_mark_sum = 0
    attempted_uoc = 0
    achieved_uoc = 0

    for result in transcript:
        # Assume subject UOC is unresolved.
        subject_uoc = f"{'unrs':>5}"

        # Grade is valid so give subject UOC a value and sum achieved UOC.
        if result.grade in ["A", "B", "C", "D", "HD", "DN", "CR", "PS", "XE", "T", "SY", "EC", "RC"]:
            subject_uoc = f"{result.uoc:2d}uoc"
            achieved_uoc += result.uoc

        # Grade is fail so mark subject UOC as fail.
        subject_uoc = f"{'fail':>5}" if result.grade in ["AF", "FL", "UF", "E", "F"] else subject_uoc

        # Attempted UOC only counts for these grades.
        attempted_uoc += result.uoc if result.grade in ["HD", "DN", "CR", "PS", "AF", "FL", "UF", "E", "F"] else 0

        # Compute weighted mark sum.
        weighted_mark_sum += result.uoc * (result.mark or 0)

        print(f"{result.code} {result.term} {result.title:<32.31s}"
              f"{result.mark or '-':>3} {result.grade:>2s}  {subject_uoc}")

    wam = weighted_mark_sum / attempted_uoc
    print(f"UOC = {achieved_uoc}, WAM = {wam:2.1f}")

except Exception as err:
    print(err)
finally:
    if conn:
        conn.close()
