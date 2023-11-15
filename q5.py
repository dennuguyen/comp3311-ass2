#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import traceback
import psycopg2
import re
from helpers import get_latest_student, get_program, get_stream, get_program_requirements, get_academic_objects, get_full_transcript, get_stream_requirements

def invert_dict_recursive(input_dict):
    inverted_dict = {}
    for rname, courses_list in input_dict.items():
        for outer in courses_list:
            for inner in outer:
                course_code, course_name = inner
                inverted_dict[course_code] = rname
    return inverted_dict

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
req_buckets = {}
req_quantities = {}

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

    # Build requirement buckets from programs and stream.
    program_requirements = get_program_requirements(conn, program_info.code)
    stream_requirements = get_stream_requirements(conn, stream_info.code)
    
    print("\n\n\n")
    for t in program_requirements:
        print(t)
    print("\n\n\n")

    for t in stream_requirements:
        print(t)
    print("\n\n\n")

    # Create requirement buckets.
    for requirement in program_requirements + stream_requirements:
        if requirement.rname not in req_buckets:
            if requirement.rtype in ["core", "elective"]:
                acadobjs = get_academic_objects(conn, requirement.rtype, requirement.acadobjs)
                req_buckets[requirement.rname] = acadobjs
                req_quantities[requirement.rname] = (requirement.min_req, requirement.max_req)
            if requirement.rtype in ["gened", "free"]:
                req_buckets[requirement.rname] = [[(requirement.acadobjs, requirement.rname)]]
                req_quantities[requirement.rname] = (requirement.min_req, requirement.max_req)

    transcript, achieved_uoc, wam = get_full_transcript(conn, stu_info.zid)

    for k, v in req_buckets.items():
        print(k, v)
    print("\n\n\n")

    # Invert the requirement buckets to allow look-up by subjects.
    inverted_req_bucket = invert_dict_recursive(req_buckets)

    # Tick off requirements and attach requirements to each course on transcript.
    for course in transcript:
        if "uoc" in course["course_uoc"]:
            course["rname"] = inverted_req_bucket.get(course["code"], None)
            if course["rname"]:
                # Pop course from requirements bucket because done.
                inverted_req_bucket.pop(course["code"])
            else:
                # Handle #### cases.
                for code, rname in inverted_req_bucket.items():
                    min_req, max_req = req_quantities[rname]

                    # if is stream core

                    # if is program core

                    # if is stream elective

                    # if is program elective

                    # if is general education

                    # if is free elective

                    # else:
                        # "Could not be allocated"
                        # course["uoc"] = "0uoc"
                qty = req_quantities.get(course["rname"], 0)
                print(course, qty)

    # Print transcript.
    for course in transcript:
        print(f"{course.get('code')} {course.get('term')} {course.get('title'):<32.31s} {course.get('mark') or '-':>3} "
                f"{course.get('grade') or '-':>2s}  {course.get('course_uoc') or ''}  {course.get('rname') or ''}")

    # Print remaining progression.
    if not inverted_req_bucket:
        print("Eligible to graduate")
    else:
        pass

except Exception:
    print(traceback.format_exc())
finally:
    if conn:
        conn.close()

