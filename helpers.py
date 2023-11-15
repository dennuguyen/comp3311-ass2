# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts
# you must submit this even if you add nothing

from psycopg2.extras import NamedTupleCursor
from psycopg2.extensions import AsIs


def stringify_acadobjs(input):
    """
    Given a list of academic objects, stringifies it in the following format:
    - COMP9900 Information Technology Project
      or COMP9991 Research Project A
    """
    output = ""
    for item in input:
        for i, subitem in enumerate(item):
            output += ("  or " if i > 0 else "- ") + f"{subitem[0]} {subitem[1]}\n"
    return output


def get_program(conn, code):
    """
    Get program code and name given program code.
    """
    curs = conn.cursor(cursor_factory=NamedTupleCursor)
    curs.execute("select code, name from programs where code = %s", [code])
    info = curs.fetchone()
    curs.close()
    return info or None


def get_stream(conn, code):
    """
    Get stream code and name given stream code.
    """
    curs = conn.cursor(cursor_factory=NamedTupleCursor)
    curs.execute("select code, name from streams where code = %s", [code])
    info = curs.fetchone()
    curs.close()
    return info or None


def get_subject(conn, code):
    """
    Get subject code, name, and uoc given subject code.
    """
    curs = conn.cursor(cursor_factory=NamedTupleCursor)
    curs.execute(
        "select code, title as name, uoc from subjects where code = %s", [code]
    )
    info = curs.fetchone()
    curs.close()
    return info or None


def get_latest_student(conn, zid):
    """
    Get student id, zid, last name, first name, program code, program name, stream code,
    and stream name given zid. This is the latest student info.
    """
    curs = conn.cursor(cursor_factory=NamedTupleCursor)
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
        """,
        [zid],
    )
    info = curs.fetchone()
    curs.close()
    return info or None


def get_requirements(conn, codeOf, code):
    """
    Get requirement subject/stream code, subject/stream name, requirement name,
    requirement type, min requirements, max requirements, and academic objects
    given subject/stream type (codeOf) and subject/stream code (code).
    """
    curs = conn.cursor(cursor_factory=NamedTupleCursor)
    curs.execute(
        """
        select
            %ss.code as scode,
            %ss.name as sname,
            requirements.name as rname,
            requirements.rtype as rtype,
            requirements.min_req as min_req,
            requirements.max_req as max_req,
            requirements.acadobjs as acadobjs
        from %ss
        inner join requirements on requirements.for_%s = %ss.id
        where %ss.code = %s
        """,
        [AsIs(codeOf) for i in range(6)] + [code],
    )
    info = curs.fetchall()
    curs.close()
    return info or None


def get_stream_requirements(conn, code):
    """
    Convenience function to get stream requirements.
    """
    return get_requirements(conn, "stream", code)


def get_program_requirements(conn, code):
    """
    Convenience function to get program requirements.
    """
    return get_requirements(conn, "program", code)


def get_academic_objects(conn, rtype, acadobjs):
    """
    Gets academic objects as a list of (code, name).

    The academic objects given must be retrieved directly from get_requirements.

    Example usage:
        for transcript[i] in requirements:
            if transcript[i].rtype in ["core", "stream"]:
                acadobjs_list = get_academic_objects(conn, transcript[i].rtype,
                                                     transcript[i].acadobjs)
    """

    query = ""
    if rtype in ["core", "elective"]:
        query = "select title as name from subjects where code = %s"
    elif rtype == "stream":
        query = "select name as name from streams where code = %s"

    output = []
    curs = conn.cursor()
    for item in acadobjs.split(","):

        # The next level of for loop handles OR case.
        subitems = item.replace("{", "").replace("}", "").split(";")
        for i, code in enumerate(subitems):
            curs.execute(query, [code])
            acadobj = curs.fetchone()
            name = rtype if acadobj is None else acadobj[0]
            if i > 0:
                output[-1].append((code, name))
            else:
                output.append([(code, name)])
    curs.close()
    return output


def get_transcript(conn, zid):
    """
    Get academic transcript as set of code, term, title, mark, grade, and uoc
    given a zid. This is ordered by term then by code.
    """
    curs = conn.cursor(cursor_factory=NamedTupleCursor)
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
        """,
        [zid],
    )
    info = curs.fetchall()
    curs.close()
    return info or None


def get_full_transcript(conn, zid):
    """
    Gets the academic transcript with UOC passed for each course and with WAM.
    """
    transcript = get_transcript(conn, zid)

    wam = 0
    weighted_mark_sum = 0
    attempted_uoc = 0
    achieved_uoc = 0

    for i in range(len(transcript)):
        course_uoc = f"{'unrs':>5}"

        # Grade is valid so give subject UOC a value and sum achieved UOC.
        if transcript[i].grade in [
            "A",
            "B",
            "C",
            "D",
            "HD",
            "DN",
            "CR",
            "PS",
            "XE",
            "T",
            "SY",
            "EC",
            "RC",
        ]:
            course_uoc = f"{transcript[i].uoc:2d}uoc"
            achieved_uoc += transcript[i].uoc

        # Grade is fail so mark subject UOC as fail.
        if transcript[i].grade in ["AF", "FL", "UF", "E", "F"]:
            course_uoc = f"{'fail':>5}"

        # Attempted UOC only counts for these grades.
        attempted_uoc += (
            transcript[i].uoc
            if transcript[i].grade
            in ["HD", "DN", "CR", "PS", "AF", "FL", "UF", "E", "F"]
            else 0
        )

        # Compute weighted mark sum.
        weighted_mark_sum += transcript[i].uoc * (transcript[i].mark or 0)

        # Mark unresolved if there is no mark but a grade.
        if not transcript[i].mark and not transcript[i].grade:
            course_uoc = ""

        # Overwrite namedtuple as dict to allow course UOC insertion.
        transcript[i] = transcript[i]._asdict()
        transcript[i]["course_uoc"] = course_uoc

        # Handle edge cases where FL and AF should just have 0 mark.
        if transcript[i]["grade"] in ["FL", "AF"] and not transcript[i]["mark"]:
            transcript[i]["mark"] = "0"

    wam = weighted_mark_sum / attempted_uoc

    return (transcript, achieved_uoc, wam)


def print_transcript(transcript, achieved_uoc, wam):
    """
    Prints a full transcript. Requires achieved UOC and WAM.
    """
    for course in transcript:
        print(
            f"{course['code']} {course['term']} {course['title']:<32.31s}"
            f"{course['mark'] or '-':>3} {course['grade'] or '-':>2s}  "
            f"{course.get('course_uoc', '')}  {course.get('rname', '')}"
        )
    print(f"UOC = {achieved_uoc}, WAM = {wam:2.1f}")
