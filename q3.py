#!/usr/bin/python3
# COMP3311 23T3 Ass2 ... print list of rules for a program or stream

import sys
import psycopg2
import re
from helpers import get_program, get_stream, get_requirements

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

core_string = ""
elective_string = ""
free_string = ""
gened_string = ""
stream_string = ""
uoc_string = ""

try:
    if codeOf == "program":
        program_info = get_program(conn, code)
        if not program_info:
            print("Invalid program code", code)
            exit(1)

        print(program_info.code, program_info.name)

    elif codeOf == "stream":
        stream_info = get_stream(conn, code)
        if not stream_info:
            print("Invalid stream code", code)
            exit(1)

        print(stream_info.code, stream_info.name)

    requirements = get_requirements(conn, codeOf, code)

    print("Academic Requirements:")

    # Iterates through each requirement type.
    for result in requirements:
        if result.rtype == "core":
            core_string += f"all courses from {result.rname}\n"
            core_string += string_to_list(conn, result.acadobjs, "select title from subjects where code = %s")
        elif result.rtype == "elective":
            elective_string += f"{min_max_to_str(result.min_req, result.max_req)} UOC courses from {result.rname}\n"
            elective_string += "- " + result.acadobjs + "\n"
        elif result.rtype == "free":
            free_string += f"{min_max_to_str(result.min_req, result.max_req)} UOC of {result.rname}\n"
        elif result.rtype == "gened":
            gened_string += f"{min_max_to_str(result.min_req, result.max_req)} UOC of {result.rname}\n"
        elif result.rtype =="stream":
            stream_string += f"{min_max_to_str(result.min_req, result.max_req)} stream from {result.rname}\n"
            stream_string += string_to_list(conn, result.acadobjs, "select name from streams where code = %s")
        elif result.rtype == "uoc":
            uoc_string += f"Total UOC {min_max_to_str(result.min_req, result.max_req)} UOC\n"
        else:
            raise ValueError("Invalid requirement type")

    # Print everything at the end in the correct order.
    print(uoc_string)
    print(stream_string)
    print(core_string)
    print(elective_string)
    print(gened_string)
    print(free_string)

except Exception as err:
  print(err)
finally:
    if conn:
        conn.close()
