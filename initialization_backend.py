import re
import json
import sqlite3
db_filepath="Data.db"
def slot_regex(course_code,slot):
    add=[]
    keys = []
    slots=slot.split(",")

    pattern1 = re.compile("[A-Z]{1}[0-9]{2}")  # for D12 vaghera
    pattern2 = re.compile("[A-Z]{1}[0-9]{1}")  # for D1



    for slot in slots:
        slot = slot.strip()

        if re.findall(pattern1, slot) == []:
            if re.findall(pattern2, slot) == []:  # single alphabet or (LAB/TBA/NA (ie text string))

                alphabet = slot
                # ( "N" or "O" or "V" or "W" or "P" or "Q" or "R" or "S" or "T" or "U")
                match alphabet:
                    case "N":
                        add.append(f"B1")
                        add.append(f"C1")
                        add.append(f"E1")
                    case "O":
                        add.append(f"K1")
                        add.append(f"L1")
                        add.append(f"I1")
                    case "V":
                        add.append(f"D1")
                        add.append(f"C2")
                        add.append(f"BLANK")
                    case "W":
                        add.append(f"L2")
                        add.append(f"J1")
                        add.append(f"M1")
                    case "P":
                        add.append(f"A2")
                        add.append(f"D2")
                        add.append(f"F1")
                    case "Q":
                        add.append(f"K2")
                        add.append(f"M2")
                        add.append(f"I2")
                    case "R":
                        add.append(f"B3")
                        add.append(f"C3")
                        add.append(f"E3")
                    case "S":
                        add.append(f"L3")
                        add.append(f"M3")
                        add.append(f"J2")
                    case "T":
                        add.append(f"A3")
                        add.append(f"D3")
                        add.append(f"F3")
                    case "U":
                        add.append(f"K3")
                        add.append(f"J3")
                        add.append(f"I3")

                    case "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M":
                        add.append(f"{alphabet}1")
                        add.append(f"{alphabet}2")
                        add.append(f"{alphabet}3")

                    case _:  # NON DEFINED SLOTS
                        add.append(f"NA")


            else:
                add.append(slot)
        else:
            alphabet = slot[0]
            dig_1 = slot[1]
            dig_2 = slot[2]

            add.append(f"{alphabet}{dig_1}")
            add.append(f"{alphabet}{dig_2}")

    return add

def initialize_scheduling(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute("SELECT course_code FROM course_data")
    rows = cursor.fetchall()
    courses= [item[0] for item in rows]

    cursor.execute("SELECT slot FROM exam_schedule")
    rows = cursor.fetchall()
    exam_slots = [item[0] for item in rows]

    cursor.execute("SELECT slot FROM slot_data")
    rows = cursor.fetchall()
    course_slots = [item[0] for item in rows]
    course_slots.pop()# to remove NA
    print(course_slots)

    connection.close()
    return ([courses,exam_slots,course_slots])

def first_draft(db_filepath,content): # for first draft of the exams
    """ return types :  -1 = course not in table , -2= exam slot dne , -3 Slot dne in Time Table"""
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    scheduled=[]
    not_scheduled=content[0]
    exam_slots=content[1]
    course_slots=content[2]

    for exam_slot in exam_slots:

        for course_slot in course_slots:
            cursor.execute(f"SELECT courses FROM slot_data WHERE slot = '{course_slot}'")
            row = cursor.fetchone()
            if row:
                courses = json.loads(row[0])
            else:
                return -3 # slot dne in Time Table
            # jo bhi slot_data table me courses hai vahi schedule honge
            # note that not_scheduled[] has been fetched from table 'course_data' which has all the courses
            for course in courses:

                if course not in scheduled:
                    cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{exam_slot}'")
                    row = cursor.fetchone()
                    if row:
                        exam_students = json.loads(row[0])
                    else:
                        return -2

                    capacity_filled = len(exam_students)

                    cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
                    row = cursor.fetchone()
                    if row:
                        course_students = json.loads(row[0])
                    else:
                        return -1 # course dne in table

                    number_of_students=len(course_students)

                    list_for_sets=[exam_students,course_students]
                    sets = [set(lst) for lst in list_for_sets]

                    # Find the intersection of sets
                    common_elements = set.intersection(*sets)

                    load = capacity_filled + number_of_students

                    if not common_elements and load <= 700:
                        cursor.execute(f"SELECT courses FROM exam_schedule WHERE slot = '{exam_slot}'")
                        row = cursor.fetchone()
                        if row:
                            exam_courses = json.loads(row[0])
                        else:
                            return -2 # exam slot dne

                        exam_courses.append(course)
                        scheduled.append(course)

                        not_scheduled.remove(course)

                        serialized_exam_courses = json.dumps(exam_courses)

                        for student in course_students:
                            exam_students.append(student)

                        serialized_exam_students = json.dumps(exam_students)



                        cursor.execute(f"UPDATE exam_schedule SET courses = ?, students = ?, total_students = ? "
                                       f"WHERE slot = ?", (serialized_exam_courses, serialized_exam_students ,
                                                           load,exam_slot))

    """NA courses being loaded with not scheduled table with flag"""
    cursor.execute(f"SELECT courses FROM slot_data WHERE slot = 'NA' ")
    row = cursor.fetchone()
    if row:
        NA_courses = json.loads(row[0])
    else:
        return -3  # slot dne in Time Table

    for course in NA_courses:
        cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
        row = cursor.fetchone()
        if row:
            students = json.loads(row[0])
        else:
            return -1  # course dne in table
        serialized_students = json.dumps(students)

        new_row = [(course, serialized_students, 1)]
        cursor.executemany("INSERT INTO not_scheduled VALUES(?,?,?)", new_row)
        not_scheduled.remove(course)


    for course in not_scheduled: # will not include any NA course
        cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
        row = cursor.fetchone()
        if row:
            students = json.loads(row[0])
        else:
            return -1 # course dne in table
        serialized_students = json.dumps(students)


        new_row=[(course,serialized_students,0)]
        cursor.executemany("INSERT INTO not_scheduled VALUES(?,?,?)", new_row)

    connection.commit()
    connection.close()
    return 1
def clear_exam_scheduling_data(db_filepath):
    #clears both exam_schedule table and not_scheduled table
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute(f"UPDATE exam_schedule SET courses = '[]' , students ='[]' , total_students = 0  ")
    cursor.execute("DELETE FROM not_scheduled")
    connection.commit()
    connection.close()

    return 1

if __name__ == "__main__":
    #clear_exam_scheduling_data(db_filepath) # exam _schedule table empty but initialized ( [], [])
    content=initialize_scheduling(db_filepath=db_filepath)
    #first_draft(db_filepath=db_filepath,content=content) # first draft filled in exam_schedule table (used along with initialize scheduling)
