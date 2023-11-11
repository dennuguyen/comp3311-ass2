# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts 
# you must submit this even if you add nothing

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
    curs = conn.cursor()
    curs.execute(
        f"""
        select people.*
        from people
        inner join students on students.id = people.id
        where people.id = '{zid}'
        """
    )
    info = curs.fetchone()
    curs.close()
    return info or None

