#!/usr/bin/python3
# COMP3311 23T3 Ass2 ... print list of rules for a program or stream

import sys
import psycopg2
import re
from helpers import get_program_info, get_stream_info

def min_max_to_str(min_req, max_req):
    if min_req and not max_req:
        return f"at least {min_req}"
    if not min_req and max_req:
        return f"up to {max_req}"
    if min_req and max_req and min_req < max_req:
        return f"between {min_req} and {max_req}"
    if min_req and max_req and min_req == max_req:
        return f"{min_req}"
    return ""  # min_req and max_req are null

def string_to_list(conn, string, query):
    curs = conn.cursor()
    array = string.split(",")
    for item in array:
        subitems = item.replace("{", "").replace("}", "").split(";")
        for i, subitem in enumerate(subitems):
            curs.execute(query + f"'{subitem}'")
            name = curs.fetchone()[0]
            if i > 0:
                print(f"  or {subitem} {name}")
            else:
                print(f"- {subitem} {name}")
    curs.close()

argc = len(sys.argv)
if argc < 2:
    print(f"Usage: {sys.argv[0]} (ProgramCode|StreamCode)")
    exit(1)

code = sys.argv[1]
if len(code) == 4:
    codeOf = "program"
elif len(code) == 6:
    codeOf = "stream"
else:
    print("Invalid code")
    exit(1)

conn = psycopg2.connect("dbname=ass2")
curs = conn.cursor()

try:
    if codeOf == "program":
        program_info = get_program_info(conn, code)
        if not program_info:
            print("Invalid program code", code)
            exit()

        print(program_info[1], program_info[2])
        print("Academic Requirements:")

        curs.execute(
            f"""
            select * from programs
            inner join requirements on requirements.for_program = programs.id
            where programs.code = '{code}'
            """
        )

    elif codeOf == "stream":
        stream_info = get_stream_info(conn, code)
        if not stream_info:
            print("Invalid stream code", code)
            exit()

        print(stream_info[1], stream_info[2])
        print("Academic Requirements:")

        curs.execute(
            f"""
            select * from streams
            inner join requirements on requirements.for_stream = streams.id
            where streams.code = '{code}'
            """
        )

    # Iterates through each requirement type.
    for _, code, pname, _, rname, rtype, min_req, max_req, acadobjs, stream, program in curs.fetchall():
        if rtype == 'core':
            print(f"all courses from {rname}")
            string_to_list(conn, acadobjs, "select title from subjects where code = ")
        elif rtype == 'elective':
            print(f"{min_max_to_str(min_req, max_req)} UOC courses from {rname}")
            print("- " + acadobjs)
        elif rtype == 'free':
            print(f"{min_max_to_str(min_req, max_req)} UOC of {rname}")
        elif rtype == 'gened':
            print(f"{min_max_to_str(min_req, max_req)} UOC of {rname}")
        elif rtype =='stream':
            print(f"{min_max_to_str(min_req, max_req)} stream from {rname}")
            string_to_list(conn, acadobjs, "select name from streams where code = ")
        elif rtype == 'uoc':
            print(f"Total UOC {min_max_to_str(min_req, max_req)} UOC")
        else:
            raise ValueError("Invalid requirement type")

except Exception as err:
  print(err)
finally:
    if curs:
        curs.close()
    if conn:
        conn.close()
