#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import traceback
import psycopg2
import re
from helpers import (
    get_latest_student,
    get_program,
    get_stream,
    get_program_requirements,
    get_academic_objects,
    get_full_transcript,
    get_stream_requirements,
    stringify_acadobjs,
    get_subject,
    print_transcript,
)


def process_requirements(requirements):
    """
    Convert requirements into dicts and acadobjs from string to lists so that
    requirements are easier to use.
    """

    # Convert requirements from [namedtuple] into dict where rname is key.
    requirements = {req.rname: req._asdict() for req in requirements}

    # Convert acadobjs from strings to lists.
    for rname, req in requirements.items():
        if req["rtype"] in ["core", "elective"]:
            req["acadobjs"] = get_academic_objects(conn, req["rtype"], req["acadobjs"])
        if req["rtype"] in ["gened", "free"]:
            req["acadobjs"] = [[(req["acadobjs"], rname)]]

    return requirements


def course_code_matcher(test, code):
    """
    Tests course codes against a generic code e.g.
        COMP#### + COMP1234 => True
        ####1#### + MATH1000 => True
    """
    return bool(re.match(test.replace("#", "."), code))


def tick_off(requirements, course, rtype):
    """
    Ticks off all requirement types and updates course transcript if necessary.
    This is done by brute force.
    """
    for rname, courses in requirements.items():

        def cleanup():
            """
            Cleanup function on tick off success. Will always update total UOC and
            attach transcript with requirement names.

            This could be turned into a decorator if there was more time.
            """
            requirements["Total UOC"]["min_req"] -= course["uoc"]
            course["rname"] = rname
            return True

        if courses["rtype"] == rtype and requirements["Total UOC"]["min_req"] > 0:
            acadobjs = courses["acadobjs"]

            # Top level courses.
            for outer in acadobjs:

                # This handles OR cases in next depth of courses.
                for inner in outer:
                    course_code, _ = inner
                    if rtype == "core":
                        if course_code == course["code"]:
                            acadobjs.remove(outer)
                            return cleanup()
                    elif courses["min_req"] - course["uoc"] >= 0:
                        if courses["max_req"] is None:
                            if course_code == course["code"]:
                                acadobjs.remove(outer)
                                courses["min_req"] -= course["uoc"]
                                return cleanup()
                            if rtype in ["gened", "free"] or (
                                "#" in course_code
                                and course_code_matcher(course_code, course["code"])
                            ):
                                courses["min_req"] -= course["uoc"]
                                return cleanup()
                        elif courses["max_req"] - course["uoc"] >= 0:
                            if course_code == course["code"]:
                                acadobjs.remove(outer)
                                courses["min_req"] -= course["uoc"]
                                courses["max_req"] -= course["uoc"]
                                return cleanup()
                            if rtype in ["gened", "free"] or (
                                "#" in course_code
                                and course_code_matcher(course_code, course["code"])
                            ):
                                courses["min_req"] -= course["uoc"]
                                courses["max_req"] -= course["uoc"]
                                return cleanup()
    return False


def tick_off_core(requirements, course):
    """
    Convenience function to tick off core requirements.
    """
    return tick_off(requirements, course, "core")


def tick_off_elective(requirements, course):
    """
    Convenience function to tick off elective requirements.
    """
    return tick_off(requirements, course, "elective")


def tick_off_gened(requirements, course):
    """
    Convenience function to tick off general education requirements.
    """
    return tick_off(requirements, course, "gened")


def tick_off_free(requirements, course):
    """
    Convenience function to tick off free elective requirements.
    """
    return tick_off(requirements, course, "free")


def check_off(requirements, rtype):
    """
    Checks if requirements have been met. Will print to output.

    Returns a boolean on success of check or not depending on what requirement
    type we're checking against.
    """
    checked_off = True
    for rname, courses in requirements.items():
        if courses["rtype"] == rtype:
            if courses["rtype"] == "core":
                sum_uoc = 0
                output = ""
                acadobjs = courses["acadobjs"]

                # If true, academic objects is not empty and there exists courses to tick off.
                if acadobjs:
                    # Sum UOC across all academic objects.
                    for outer in acadobjs:
                        # No need for inner loop since inner loop represents OR.
                        subject = get_subject(conn, outer[0][0])
                        sum_uoc += subject.uoc

                    # Prepare academic objects for output.
                    output += stringify_acadobjs(acadobjs)

                    # Prepend UOC count to academic object list.
                    output = (
                        f"Need {sum_uoc} more UOC for {courses['rname']}\n" + output
                    )
                    print(output)
                    checked_off = False

            # Only need to check min req for this since student may take any variety of courses.
            if courses["rtype"] in ["elective", "gened", "free"]:
                if courses["min_req"] > 0:
                    print(
                        f"Need {courses['min_req']} more UOC for {courses['rname']}\n"
                    )
                    checked_off = False

    return checked_off


argc = len(sys.argv)
if argc < 2:
    print(f"Usage: {sys.argv[0]} zID [Program Stream]")
    exit(1)

zid = sys.argv[1]
if zid[0] == "z":
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

conn = None

try:
    conn = psycopg2.connect("dbname=ass2")

    # Get student information.
    stu_info = get_latest_student(conn, zid)
    if not stu_info:
        print(f"Invalid student id {zid}")
        exit(1)

    # Get program information.
    program_info = get_program(conn, program_code or stu_info.program_code)
    if not program_info:
        print(f"Invalid program code {program_code}")
        exit(1)

    # Get stream information.
    stream_info = get_stream(conn, stream_code or stu_info.stream_code)
    if not stream_info:
        print(f"Invalid program code {stream_code}")
        exit(1)

    # Print header.
    print(f"{stu_info.zid} {stu_info.last_name}, {stu_info.first_name}")
    print(f"{program_info.code} {stream_info.code} {program_info.name}")

    # Get program requirements.
    program_requirements = get_program_requirements(conn, program_info.code)
    program_requirements = process_requirements(program_requirements)

    # Get stream requirements.
    stream_requirements = get_stream_requirements(conn, stream_info.code)
    stream_requirements = process_requirements(stream_requirements)

    transcript, achieved_uoc, wam = get_full_transcript(conn, stu_info.zid)

    # Tick off requirements.
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

        # Nothing could be ticked off so course cannot be counted.
        course["rname"] = "Could not be allocated"
        course["course_uoc"] = " 0uoc"
        achieved_uoc -= course["uoc"]

    print_transcript(transcript, achieved_uoc, wam)

    # Print remaining progression.
    is_eligible = True
    is_eligible &= check_off(stream_requirements, "core")
    is_eligible &= check_off(program_requirements, "core")
    is_eligible &= check_off(stream_requirements, "elective")
    is_eligible &= check_off(program_requirements, "elective")
    is_eligible &= check_off(stream_requirements, "gened")
    is_eligible &= check_off(program_requirements, "gened")
    is_eligible &= check_off(stream_requirements, "free")
    is_eligible &= check_off(program_requirements, "free")

    if is_eligible:
        print("Eligible to graduate")

except Exception:
    print(traceback.format_exc())
finally:
    if conn:
        conn.close()
