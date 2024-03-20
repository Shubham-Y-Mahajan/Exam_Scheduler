from initialization_backend import first_draft, clear_exam_scheduling_data ,slot_regex, initialize_scheduling
import re
import json
import sqlite3
db_filepath="Data.db"

def deschedule_course(db_filepath,exam_slot,course):
    # if a non scheduled course is attempted to be descheduled then error
    """ return types : -1 = course not in table , -2= exam slot dne , -3 = data inconsistency a)course is already not scheduled or b) exam slot and course dont match"""
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
    row = cursor.fetchone()

    if row:
        course_students = json.loads(row[0])
    else:
        connection.close()
        return -1 # course not present in table

    cursor.execute(f"SELECT courses FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_courses = json.loads(row[0])
    else:
        connection.close()
        return -2  # exam slot does not exist


    cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_students = json.loads(row[0])
    else:
        connection.close()
        return -2  # exam slot does not exist
    try:
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
        return 1
    except ValueError:
        connection.close()
        return -3

def schedule_course(db_filepath,exam_slot,course):
    """ return types  : integer > 700 = capacity exceed , 1 = succesfull , -1 = course not in table , -2= exam slot dne ,  -3 Database error"""
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT students FROM not_scheduled WHERE course_code = '{course}'")
    row = cursor.fetchone()

    if row:
        course_students = json.loads(row[0])
    else:
        connection.close()

        return -1 # course not present in table
    cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_students = json.loads(row[0])
    else:
        connection.close()
        return -2 # exam slot does not exist

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
            connection.close()
            return -2  # exam slot does not exist

        for exam_course in exam_courses:
            clash_students=[]
            cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{exam_course}'")
            row = cursor.fetchone()

            if row:
                course_students = json.loads(row[0])

            else:
                connection.close()

                return -3 # Database error

            for student in common_elements:
                if student in course_students:
                    clash_students.append(student)

            if clash_students:
                clashes.append((exam_course,clash_students))

        connection.close()
        return(clashes)

    # no students clashing but checking for slot capacity
    if (len(exam_students) + len(course_students)) > 700 :
        connection.close()
        return (len(exam_students) + len(course_students))

    # scheduling the exam
    cursor.execute(f"SELECT courses FROM exam_schedule WHERE slot = '{exam_slot}'")
    row = cursor.fetchone()
    if row:
        exam_courses = json.loads(row[0])
    else:
        connection.close()
        return -2  # exam slot does not exist
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

    return 1 # success




if __name__ == "__main__":
    #clear_exam_scheduling_data(db_filepath)
    content=initialize_scheduling(db_filepath=db_filepath)
    first_draft(db_filepath=db_filepath,content=content)
    #value = deschedule_course(db_filepath=db_filepath,exam_slot="13",course="CYP502")
    #value=schedule_course(db_filepath=db_filepath,exam_slot="32",course="CYP502")
    #print(value)