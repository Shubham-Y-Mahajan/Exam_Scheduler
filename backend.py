from initialization_backend import schedule_exam, clear_exam_scheduling_data ,slot_regex, initialize_scheduling
import re
import json
import sqlite3
db_filepath="Data.db"

def deschedule_course(db_filepath,exam_slot,course):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
    row = cursor.fetchone()
    if row:
        course_students = json.loads(row[0])
    else:
        course_students = []

    cursor.execute(f"SELECT courses FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_courses = json.loads(row[0])
    else:
        exam_courses = []


    cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_students = json.loads(row[0])
    else:
        exam_students = []

    exam_courses.remove(course)
    for student in course_students:
        exam_students.remove(student)

    total_exam_students=len(exam_students)

    serialized_exam_courses = json.dumps(exam_courses)

    serialized_exam_students = json.dumps(exam_students)

    cursor.execute(f"UPDATE exam_schedule SET courses = ?, students = ?, total_students = ? "
                   f"WHERE slot = ?", (serialized_exam_courses, serialized_exam_students,
                                       total_exam_students, exam_slot))

    serialized_course_students = json.dumps(course_students)
    new_row = [(course, serialized_course_students)]
    cursor.executemany("INSERT INTO not_scheduled VALUES(?,?)", new_row)

    connection.commit()
    connection.close()

def schedule_course(db_filepath,exam_slot,course):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT students FROM not_scheduled WHERE course_code = '{course}'")
    row = cursor.fetchone()
    if row:
        course_students = json.loads(row[0])
    else:
        course_students = []

    cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_students = json.loads(row[0])
    else:
        exam_students = []

    list_for_sets = [exam_students, course_students]
    sets = [set(lst) for lst in list_for_sets]

    # Find the intersection of sets
    common_elements = set.intersection(*sets)
    if common_elements:
        clashes=[]
        cursor.execute(f"SELECT courses FROM exam_schedule WHERE slot = '{exam_slot}'")
        row = cursor.fetchone()
        if row:
            exam_courses = json.loads(row[0])
        else:
            exam_courses = []

        for course in exam_courses:
            clash_students=[]
            cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
            row = cursor.fetchone()
            if row:
                course_students = json.loads(row[0])
            else:
                course_students = []

            for student in common_elements:
                if student in course_students:
                    clash_students.append(student)

            if clash_students:
                clashes.append((course,clash_students))

        return(clashes)

    # no students clashing but checking for slot capacity
    if (len(exam_students) + len(course_students)) > 700 :
        return 0

    # scheduling the exam
    cursor.execute(f"SELECT courses FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_courses = json.loads(row[0])
    else:
        exam_courses = []
    exam_courses.append(course)
    for student in course_students:
        exam_students.append(student)

    total_exam_students = len(exam_students)

    serialized_exam_courses = json.dumps(exam_courses)

    serialized_exam_students = json.dumps(exam_students)

    cursor.execute(f"UPDATE exam_schedule SET courses = ?, students = ?, total_students = ? "
                   f"WHERE slot = ?", (serialized_exam_courses, serialized_exam_students,
                                       total_exam_students, exam_slot))


    # updating not scheduled
    cursor.execute(f"DELETE FROM not_scheduled WHERE course_code = '{course}'")

    connection.commit()
    connection.close()

    return 1



if __name__ == "__main__":
    #clear_exam_scheduling_data(db_filepath)
    #content=initialize_scheduling(db_filepath=db_filepath)
    #schedule_exam(db_filepath=db_filepath,content=content)
    deschedule_course(db_filepath=db_filepath,exam_slot="13",course="CS101")
    #value=schedule_course(db_filepath=db_filepath,exam_slot="13",course="CS101")
    #print(value)