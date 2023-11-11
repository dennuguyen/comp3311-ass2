#!/usr/bin/python3
# COMP3311 23T3 Ass2 ... track proportion of overseas students

import sys
import psycopg2
import re

conn = psycopg2.connect("dbname=ass2")
curs = conn.cursor()

try:
    curs.execute(
        """
        with student_enrolments as (
            select distinct on (program_enrolments.term, program_enrolments.student)
            terms.code as term,
            students.status as status
            from terms
            inner join program_enrolments on program_enrolments.term = terms.id
            inner join students on students.id = program_enrolments.student
        )
        select * from student_enrolments order by term
        """
    )

    # Print header.
    print("Term  #Locl  #Intl Proportion")

    prev_term = "19T1"
    num_locals = 0
    num_intls = 0
    
    # Helper to print table rows.
    def row():
        return f"{prev_term} {num_locals:6d} {num_intls:6d} {(num_locals / num_intls if num_intls else 0):6.1f}"

    for [term, status] in curs.fetchall():
        if status == "INTL":
            num_intls += 1
        else:
            num_locals += 1

        # When term changes, print the proportion so far
        if prev_term != term:
            print(row())
            prev_term = term
            num_locals = 0
            num_intls = 0

    # Print very last row
    print(row())
except err:
    print(err)
finally:
    if curs:
        curs.close()
    if conn:
        conn.close()
