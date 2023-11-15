#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import psycopg2
import re
from helpers import get_transcript, get_latest_student, get_program, get_stream, get_program_requirements

argc = len(sys.argv)
if argc < 2:
    print(f"Usage: {sys.argv[0]} zID [Program Stream]")
    exit(1)

zid = sys.argv[1]
if zid[0] == 'z':
    zid = zid[1:8]

digits = re.compile("^\d{7}$")
if not digits.match(zid):
    print("Invalid student ID")
    exit(1)

program_code = None
stream_code = None

if argc == 4:
    program_code = sys.argv[2]
    stream_code = sys.argv[3]

conn = psycopg2.connect("dbname=ass2")

############
def create_requirement_buckets(conn, string, query):
    output = ""
    curs = conn.cursor()
    array = string.split(",")
    for item in array:
        subitems = item.replace("{", "").replace("}", "").split(";")
        for i, subitem in enumerate(subitems):
            curs.execute(query, [subitem])
            name = curs.fetchone()[0]
            if i > 0:
                output += f"  or {subitem} {name}\n"
            else:
                output += f"- {subitem} {name}\n"
    curs.close()
    return output

try:
    stu_info = get_latest_student(conn, zid)
    print(stu_info)
    if not stu_info:
        print(f"Invalid student id {zid}")
        exit(1)

    program_info = get_program(conn, program_code or stu_info.program_code)
    if not program_info:
        print(f"Invalid program code {program_code}")
        exit(1)

    stream_info = get_stream(conn, stream_code or stu_info.stream_code)
    if not stream_info:
        print(f"Invalid program code {stream_code}")
        exit(1)

    print(program_info)

    transcript = get_transcript(conn, stu_info.zid)
    for result in transcript:
        # result['requirement'] = 
        obj = get_program_requirements(conn, program_info.code)
        print(obj)

    # ... add your code here ...

except Exception as err:
    print(err)
finally:
    if conn:
        conn.close()

