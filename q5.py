#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import traceback
import psycopg2
import re
from helpers import get_latest_student, get_program, get_stream, get_program_requirements, get_academic_objects, get_full_transcript, get_stream_requirements

def process_requirements(requirements):
    """
    Convert requirements into dicts and acadobjs from string to lists so that
    requirements are easier to use.
    """

    # Convert requirements from [namedtuple] into dict where rname is key.
    requirements = { req.rname: req._asdict() for req in requirements }

    # Convert acadobjs from strings to lists.
    for rname, req in requirements.items():
        if req["rtype"] in ["core", "elective"]:
            req["acadobjs"] = get_academic_objects(conn, req["rtype"], req["acadobjs"])
        if req["rtype"] in ["gened", "free"]:
            req["acadobjs"] = [[(req["acadobjs"], rname)]]

    return requirements

def course_code_matcher(test, code):
    return bool(re.match(test.replace("#", "."), code))

def tick_off(requirements, course, rtype):
    for rname, courses_list in requirements.items():
        if courses_list["rtype"] == rtype:
            acadobjs = courses_list["acadobjs"]
            for outer in acadobjs:
                for inner in outer:
                    course_code, course_name = inner
                    if rtype == "core":
                        if course_code == course["code"]:
                            acadobjs.remove(outer)
                            course["rname"] = rname
                            return True
                    elif courses_list["min_req"] > 0:
                        if course_code == course["code"]:
                            acadobjs.remove(outer)
                            courses_list["min_req"] -= course["uoc"]
                            # courses_list["max_req"] -= course["uoc"]
                            course["rname"] = rname
                            return True
                        if rtype in ["gened", "free"] or ("#" in course_code and course_code_matcher(course_code, course["code"])):
                            courses_list["min_req"] -= course["uoc"]
                            # courses_list["max_req"] -= course["uoc"]
                            course["rname"] = rname
                            return True
    return False

def tick_off_core(requirements, course):
    return tick_off(requirements, course, "core")

def tick_off_elective(requirements, course):
    return tick_off(requirements, course, "elective")

def tick_off_gened(requirements, course):
    return tick_off(requirements, course, "gened")

def tick_off_free(requirements, course):
    return tick_off(requirements, course, "free")

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

try:
    stu_info = get_latest_student(conn, zid)
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

    # Print header.
    print(f"{stu_info.zid} {stu_info.last_name}, {stu_info.first_name}")
    print(f"{stu_info.program_code} {stu_info.stream_code} {stu_info.program_name}")

    # Get program requirements.
    program_requirements = get_program_requirements(conn, program_info.code)
    program_requirements = process_requirements(program_requirements)

    # Get stream requirements.
    stream_requirements = get_stream_requirements(conn, stream_info.code)
    stream_requirements = process_requirements(stream_requirements)

    transcript, achieved_uoc, wam = get_full_transcript(conn, stu_info.zid)

    # Tick off requirements and attach requirements to each course on transcript.
    # Brute force it.
    for course in transcript:
        if "uoc" not in course["course_uoc"]:
            continue

        # Tick off stream then program cores.
        if tick_off_core(stream_requirements, course):
            continue
        if tick_off_core(program_requirements, course):
            continue

        # Tick off stream then program electives.
        if tick_off_elective(stream_requirements, course):
            continue
        if tick_off_elective(program_requirements, course):
            continue

        # Tick off general education.
        if tick_off_gened(stream_requirements, course):
            continue
        if tick_off_gened(program_requirements, course):
            continue

        # Tick off free electives.
        if tick_off_free(stream_requirements, course):
            continue
        if tick_off_free(program_requirements, course):
            continue

        course["rname"] = "Could not be allocated"
        course["course_uoc"] = " 0uoc"
        achieved_uoc -= course["uoc"]

    # Print transcript.
    for course in transcript:
        print(f"{course['code']} {course['term']} {course['title']:<32.31s}"
              f"{course['mark'] or '-':>3} {course['grade'] or '-':>2s}  {course.get('course_uoc', '')}  {course.get('rname', '')}")
    print(f"UOC = {achieved_uoc}, WAM = {wam:2.1f}")

    # Print remaining progression.
    print("Eligible to graduate")

except Exception:
    print(traceback.format_exc())
finally:
    if conn:
        conn.close()

