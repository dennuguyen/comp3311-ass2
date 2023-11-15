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

conn = None
curs = None

try:
    conn = psycopg2.connect("dbname=ass2")
    curs = conn.cursor()

    # Get subject information.
    curs.execute("select code, title from subjects where code = %s", [subject])
    code, title = curs.fetchone()
    print(code, title)

    # Get satisfaction rate, number of responses, and number of students for each course.
    curs.execute(
        """
        select
            terms.code as term,
            courses.satisfact as satisfaction,
            courses.nresponses as nresponses,
            count(students) as nstudents,
            people.full_name as convenor
        from course_enrolments
        inner join students on students.id = course_enrolments.student
        full join courses on courses.id = course_enrolments.course
        inner join subjects on subjects.id = courses.subject
        inner join terms on terms.id = courses.term
        inner join staff on staff.id = courses.convenor
        inner join people on people.id = staff.id
        where subjects.code = %s
        group by
            terms.code,
            courses.satisfact,
            courses.nresponses,
            people.full_name
        """,
        [subject],
    )

    print("Term  Satis  #resp   #stu  Convenor")
    for code, satisfaction, nresponses, nstudents, convenor in curs.fetchall():
        print(
            f"{code} {satisfaction or '?':>6} {nresponses or '?':>6}"
            f"{nstudents:>6}  {convenor}"
        )

except Exception as err:
    print(err)
finally:
    if curs:
        curs.close()
    if conn:
        conn.close()
