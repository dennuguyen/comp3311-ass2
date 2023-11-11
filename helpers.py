# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts 
# you must submit this even if you add nothing

import psycopg2.extras

def get_program_info(conn, code):
    curs = conn.cursor()
    curs.execute(f"select * from programs where programs.code = '{code}'")
    info = curs.fetchone()
    curs.close()
    return info or None

def get_stream_info(conn, code):
    curs = conn.cursor()
    curs.execute(f"select * from streams where streams.code = '{code}'")
    info = curs.fetchone()
    curs.close()
    return info or None

def get_student_info(conn, zid):
    curs = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    curs.execute(
        f"""
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
        where people.zid = '{zid}'
        order by terms.starting desc
        """
    )
    info = curs.fetchone()
    curs.close()
    return info or None

