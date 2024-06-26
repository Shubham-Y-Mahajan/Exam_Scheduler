import csv
import sqlite3
import json
from initialization_backend import slot_regex
csv_filepath="input.csv"
db_filepath="Data.db"
def csv_to_db(csv_filepath,db_filepath):
    data=[]
    with open(csv_filepath) as file:
        reader=csv.reader(file)
        for index,line in enumerate(reader):
            if (index != 0):  # to skip the first row
                data.append(tuple(line))
                #print(data)

    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()


    # Insert new rows
    rows=data

    for row in rows:
        cursor.execute(f"INSERT INTO student_enrollment_data VALUES(?,?,?,?)", row)


    connection.commit()
    connection.close()
    return 1

def clear_course_slot_db(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()


    cursor.execute("DELETE FROM course_data")

    cursor.execute(f"UPDATE slot_data SET courses = '[]' ")

    connection.commit()
    connection.close()
    return 1
def populate_course_table(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute("SELECT course_code FROM student_enrollment_data")

    rows = cursor.fetchall()

    lst_of_tples = rows
    lst = [item[0] for item in lst_of_tples]


    unique_elements = list(set(lst))
    sorted_unique=sorted(unique_elements)


    for course in sorted_unique:
        cursor.execute(f"SELECT instructor, slot FROM student_enrollment_data WHERE course_code='{course}'")
        rows = cursor.fetchall()
        instructor=rows[0][0]
        slot=rows[0][1]

        slot_codes=slot_regex(course,slot)

        if slot_codes != 0 :
            populate_slot_table(slot_codes,course,connection)

        cursor.execute(f"SELECT id FROM student_enrollment_data WHERE course_code='{course}'")
        rows = cursor.fetchall()
        registered_students=[item[0] for item in rows]

        serialized_list = json.dumps(registered_students)

        new_row = [(course, instructor, slot, serialized_list,len(registered_students)),]

        cursor.executemany("INSERT INTO course_data VALUES(?,?,?,?,?)", new_row)

    connection.commit()
    connection.close()
    return 1
def populate_slot_table(slot_codes,course,connection):
    cursor=connection.cursor()
    for slot in slot_codes:
        cursor.execute(f"SELECT courses FROM slot_data WHERE slot='{slot}'")
        row = cursor.fetchone()

        if row:
            course_list=json.loads(row[0])
        else:
            return -3 # slot dne in Time Table

        course_list.append(course)
        serialized_list = json.dumps(course_list)


        cursor.execute(f"UPDATE slot_data SET courses = ? WHERE slot = ?", (serialized_list, slot))

    connection.commit()

    return 1

def clear_exam_schedule_table(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM exam_schedule")
    cursor.execute("DELETE FROM not_scheduled")

    connection.commit()
    connection.close()
    return 1

def clear_student_enrollment_data(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM student_enrollment_data")


    connection.commit()
    connection.close()
    return 1
def initialize_exam_schedule_table(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM constraints")
    row=cursor.fetchall()

    days=row[0][0]
    slots=row[0][1]

    new_rows=[]
    for i in range(days):
        for j in range(slots):
            new_rows.append((f"{i+1}{j+1}","[]","[]",0))



    cursor.executemany("INSERT INTO exam_schedule VALUES(?,?,?,?)", new_rows)
    connection.commit()
    connection.close()


def extract_not_scheduled(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute("SELECT course_code FROM not_scheduled")
    rows = cursor.fetchall()
    not_scheduled_course_list = []
    for tple in rows:
        not_scheduled_course_list.append(tple[0])
    connection.close()
    return not_scheduled_course_list
if __name__ == "__main__":
    # csv_to_db(csv_filepath,db_filepath) # for spreadsheet csv to student enrollment table fill

    #clear_course_slot_db(db_filepath) # course_data and slot_data table emptied

    #populate_course_table(db_filepath) # student enrollment data se course_data table fill hoga then usse slot data filled

    #clear_exam_schedule_table(db_filepath=db_filepath) # clean wipe
    #initialize_exam_schedule_table(db_filepath=db_filepath) # initialization ( [] , [] )
    pass