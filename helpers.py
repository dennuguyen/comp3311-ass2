# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts 
# you must submit this even if you add nothing

import psycopg2.extras

def get_program_info(conn, code):
    curs = conn.cursor()
    curs.execute("select * from programs where programs.code = %s", [code])
    info = curs.fetchone()
    curs.close()
    return info or None

def get_stream_info(conn, code):
    curs = conn.cursor()
    curs.execute("select * from streams where streams.code = %s", [code])
    info = curs.fetchone()
    curs.close()
    return info or None

def get_latest_student_info(conn, zid):
    curs = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    curs.execute(
        """
        select
            people.id as id,
            people.zid as zid,
            people.family_name as last_name,
            people.given_names as first_name,
            programs.code as program_code,
            programs.name as program_name,
            streams.code as stream_code,
            streams.name as stream_name
        from people
        inner join program_enrolments on program_enrolments.student = people.id
        inner join stream_enrolments on stream_enrolments.part_of = program_enrolments.id
        inner join programs on programs.id = program_enrolments.program
        inner join streams on streams.id = stream_enrolments.stream
        inner join terms on terms.id = program_enrolments.term
        where people.zid = %s
        order by terms.starting desc
        """
    , [zid])
    info = curs.fetchone()
    curs.close()
    return info or None

def get_transcript(conn, zid):
    curs = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    curs.execute(
        """
        with transcript as (
            select
                subjects.code as code,
                terms.code as term,
                subjects.title as title,
                course_enrolments.mark as mark,
                course_enrolments.grade as grade,
                subjects.uoc as uoc
            from course_enrolments
            inner join courses on courses.id = course_enrolments.course
            inner join subjects on subjects.id = courses.subject
            inner join people on people.id = course_enrolments.student
            inner join terms on terms.id = courses.term
            where people.zid = %s
        )
        select * from transcript
        order by transcript.term, transcript.code
        """
    , [zid])
    info = curs.fetchone()
    curs.close()
    return info or None
