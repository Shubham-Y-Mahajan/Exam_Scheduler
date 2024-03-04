import csv
import sqlite3
import json
from initialization_backend import slot_regex
csv_filepath="acad_office_data.csv"
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

def clear_course_slot_db(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()


    cursor.execute("DELETE FROM course_data")

    cursor.execute(f"UPDATE slot_data SET courses = '[]' ")

    connection.commit()
    connection.close()

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

def populate_slot_table(slot_codes,course,connection):
    cursor=connection.cursor()
    for slot in slot_codes:
        cursor.execute(f"SELECT courses FROM slot_data WHERE slot='{slot}'")
        row = cursor.fetchone()

        if row:
            course_list=json.loads(row[0])
        else:
            course_list=[]

        course_list.append(course)
        serialized_list = json.dumps(course_list)


        cursor.execute(f"UPDATE slot_data SET courses = ? WHERE slot = ?", (serialized_list, slot))

    connection.commit()






if __name__ == "__main__":
    # csv_to_db(csv_filepath,db_filepath)
    clear_course_slot_db(db_filepath)

    populate_course_table(db_filepath)
