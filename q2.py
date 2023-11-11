#!/usr/bin/python3
# COMP3311 23T3 Ass2 ... track satisfaction in a given subject

import sys
import psycopg2
import re

argc = len(sys.argv)

if argc < 2:
    print(f"Usage: {sys.argv[0]} SubjectCode")
    exit(1)

subject = sys.argv[1]
if not re.compile("^[A-Z]{4}[0-9]{4}$").match(subject):
    print("Invalid subject code")
    exit(1)

code = None
def row():
  return f"{code} {satisfaction:6d} {num_responses:6d} {num_students:6d}  {convenor}"

with psycopg2.connect("dbname=ass2") as conn:
    with conn.cursor() as curs:
        subjectInfo = getSubject(conn, subject)
        if not subjectInfo:
            print(f"Invalid subject code {code}")
            exit(1)
        #print(subjectInfo)  #debug

        # List satisfaction for subject over time

        # ... add your code here ...