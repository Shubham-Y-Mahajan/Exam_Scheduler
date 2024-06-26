import os.path
from collections import Counter
from initialization_backend import first_draft, clear_exam_scheduling_data ,slot_regex, initialize_scheduling
import random
import json
import sqlite3
import xlsxwriter
import datetime
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
        new_row = [(course, serialized_course_students, 0)]
        cursor.executemany("INSERT INTO not_scheduled VALUES(?,?,?)", new_row)

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
    """fetching the data of max capacity"""
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute("SELECT capacity FROM constraints")
    row = cursor.fetchone()
    max_capacity = row[0]

    if (len(exam_students) + len(course_students)) > max_capacity:
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


def swap_slot_content(db_filepath,slot1,slot2):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT courses,students,total_students FROM exam_schedule WHERE slot = '{slot1}'")
    row1 = cursor.fetchone()
    cursor.execute(f"SELECT courses,students,total_students FROM exam_schedule WHERE slot = '{slot2}'")
    row2 = cursor.fetchone()
    cursor.execute(f"UPDATE exam_schedule SET courses = ? , students = ? , total_students = ? WHERE slot = {slot1}", row2)
    cursor.execute(f"UPDATE exam_schedule SET courses = ? , students = ? , total_students = ? WHERE slot = {slot2}",row1)

    connection.commit()
    connection.close()

def balancer_swapper(slot1 , slot2 , cursor):
    """ Same as swap slot content but special modifications done for use in balancer function"""

    cursor.execute(f"SELECT courses,students,total_students FROM exam_schedule WHERE slot = '{slot1}'")
    row1 = cursor.fetchone()
    cursor.execute(f"SELECT courses,students,total_students FROM exam_schedule WHERE slot = '{slot2}'")
    row2 = cursor.fetchone()
    cursor.execute(f"UPDATE exam_schedule SET courses = ? , students = ? , total_students = ? WHERE slot = {slot1}",
                   row2)
    cursor.execute(f"UPDATE exam_schedule SET courses = ? , students = ? , total_students = ? WHERE slot = {slot2}",
                   row1)


def balancer(db_filepath,type):
    """ Uses a greedy approach thus not the most optimal solution , solution changes based on the state on which
        the function was called.
        As a solution to the above problem we are randomising it as much as possible
    """
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT slot FROM exam_schedule ")
    rows = cursor.fetchall()
    exam_slots=[row[0] for row in rows]
    exam_slots2=[row[0] for row in rows]
    if type == 1:
        pass
    elif type == 2:
        exam_slots.reverse()
        exam_slots2.reverse()
    elif type == 3:
        random.shuffle(exam_slots)
        random.shuffle(exam_slots2)

    while True:
        print("wait")
        swap_flag=0
        for slot1 in exam_slots:
            cursor.execute(f"SELECT abc from analysis")
            rows = cursor.fetchall()
            abc = [len(json.loads(row[0])) for row in rows]
            initial_abc = sum(abc)

            best_swap = None
            min_abc = initial_abc

            for slot2 in exam_slots2:
                balancer_swapper(slot1=slot1, slot2=slot2, cursor=cursor)
                connection.commit()
                update_analysis(db_filepath=db_filepath)

                cursor.execute(f"SELECT abc from analysis")
                rows=cursor.fetchall()
                abc=[len(json.loads(row[0])) for row in rows]
                total_abc=sum(abc)

                balancer_swapper(slot1=slot1, slot2=slot2, cursor=cursor)
                connection.commit()
                update_analysis(db_filepath=db_filepath)

                if total_abc < min_abc:
                    min_abc=total_abc
                    best_swap=slot2



            #applying best swap
            if best_swap:
                swap_flag=1
                balancer_swapper(slot1=slot1, slot2=best_swap, cursor=cursor)
                connection.commit()
                update_analysis(db_filepath=db_filepath)
                print("Loading...")


        if swap_flag==0:
            connection.close()
            return 1


def day_swap(db_filepath,dayA,dayB):

    for i in range(1,4):
        swap_slot_content(db_filepath=db_filepath,slot1=f"{dayA}{i}",slot2=f"{dayB}{i}")

    update_analysis(db_filepath=db_filepath)
    return 1



def possible_slots(db_filepath,course):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute(f"SELECT registered_students FROM course_data WHERE course_code = '{course}'")
    row = cursor.fetchone()

    if row:
        course_students = set(json.loads(row[0]))

    else:
        connection.close()

        return -1 # course not present in table
    cursor.execute(f"SELECT slot from exam_schedule")
    rows = cursor.fetchall()

    slots=[]
    for row in rows:
        slots.append(row[0])


    possible=[]
    for exam_slot in slots:
        cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{exam_slot}'")
        row = cursor.fetchone()
        if row:
            exam_students = set(json.loads(row[0]))
        else:
            connection.close()
            return -2  # exam slot does not exist
        sets = [exam_students, course_students]

        common_elements = set.intersection(*sets)
        if not common_elements:
            possible.append(exam_slot)

    connection.close()

    if possible:
        return possible
    else:
        return 0


def update_analysis(db_filepath):

    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM analysis")
    cursor.execute("SELECT days FROM constraints")
    row = cursor.fetchone()

    days=row[0]

    for i in range(1,days+1,1):
        cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{i}1'")
        row1 = cursor.fetchone()
        cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{i}2'")
        row2 = cursor.fetchone()
        cursor.execute(f"SELECT students FROM exam_schedule WHERE slot = '{i}3'")
        row3 = cursor.fetchone()
        if row1 and row2 and row3:
            a = set(json.loads(row1[0]))
            b = set(json.loads(row2[0]))
            c = set(json.loads(row3[0]))

        else:
            connection.close()
            return -2  # exam slot does not exist

        sets_ab = [a,b]
        sets_bc = [b, c]
        sets_ac = [a, c]
        sets_abc = [a,b,c]

        common_elements_ab = json.dumps(list(set.intersection(*sets_ab)))
        common_elements_bc = json.dumps(list(set.intersection(*sets_bc)))
        common_elements_ac = json.dumps(list(set.intersection(*sets_ac)))
        common_elements_abc = json.dumps(list(set.intersection(*sets_abc)))

        new_row = [(i,common_elements_ab,common_elements_bc,common_elements_ac,common_elements_abc),]
        cursor.executemany("INSERT INTO analysis VALUES(?,?,?,?,?)", new_row)

    connection.commit()
    connection.close()
    return 1

def current_analysis(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM analysis")
    rows = cursor.fetchall()
    result = []
    for tple in rows:
        result.append([tple[0], len(json.loads(tple[1])), len(json.loads(tple[2])), len(json.loads(tple[3])),
                       len(json.loads(tple[4]))])


    connection.close()
    return result



def detailed_analysis_abc(db_filepath):
    """ Exam report vala code le , 3 list le har slot ka ek list then voh index wise pront"""
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT day,abc FROM analysis ")
    rows = cursor.fetchall()

    day_abc={row[0]:json.loads(row[1]) for row in rows}


    cursor.execute(f"SELECT days FROM constraints")
    row=cursor.fetchone()
    days=row[0]

    detailed_set=[]

    for i in range(1,days+1):
        day_set=[]
        cursor.execute(f"SELECT courses from exam_schedule WHERE slot = '{i}1'")
        row1 = cursor.fetchone()

        cursor.execute(f"SELECT courses from exam_schedule WHERE slot = '{i}2'")
        row2 = cursor.fetchone()

        cursor.execute(f"SELECT courses from exam_schedule WHERE slot = '{i}3'")

        row3 = cursor.fetchone()

        exam_day_courses = []
        for course in json.loads(row1[0]):
            exam_day_courses.append(course)
        for course in json.loads(row2[0]):
            exam_day_courses.append(course)
        for course in json.loads(row3[0]):
            exam_day_courses.append(course)


        for student in day_abc[i]:
            student_set=[]
            student_set.append(student)
            cursor.execute(f"SELECT course_code FROM student_enrollment_data WHERE id='{student}'")
            rows=cursor.fetchall()
            student_courses=[row[0] for row in rows]

            for course in student_courses:
                if course in exam_day_courses:
                    student_set.append(course)

            day_set.append(student_set)

        detailed_set.append(day_set)

    connection.close()

    return detailed_set


def analysis_excel_writer(detailed_abc,detailed_cummalative):
    if os.path.exists("Analysis Report.xlsx"):
        os.remove("Analysis Report.xlsx")
    workbook = xlsxwriter.Workbook(f"Analysis Report.xlsx")
    worksheet = workbook.add_worksheet()

    row=0

    for index, data in enumerate(detailed_abc):
        day=index+1
        worksheet.write(row, 0, f" Day {day}")
        row += 1
        col=1
        for student_set in data:
            for item in student_set:
                worksheet.write(row, col, item)
                col += 1
            row+=1
            col=1
        row += 2

    worksheet = workbook.add_worksheet()
    row=0
    col=0
    worksheet.write(row,col,"ID")
    worksheet.write(row,col+1,"a")
    worksheet.write(row,col+2,"b")
    worksheet.write(row,col+3,"c")
    worksheet.write(row,col+4,"Day")

    row += 2

    for index, data in enumerate(detailed_cummalative):
        day=index+1
        row += 1
        col=0
        for student_set in data:
            for item in student_set:
                worksheet.write(row, col, item)
                
                col += 1
            worksheet.write(row, col, day)
            row+=1
            col=0
        row += 2

    workbook.close()
    return 1

def detailed_analysis_all(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT day FROM analysis ")
    rows = cursor.fetchall()
    days=[row[0] for row in rows]

    detailed_set=[]
    for day in days:
        day_set=[]
        cursor.execute(f"SELECT courses,students FROM exam_schedule WHERE slot = '{day}1' ")
        rows = cursor.fetchall()
        a_courses=json.loads([row[0] for row in rows][0])
        a_students=json.loads([row[1] for row in rows][0])
        cursor.execute(f"SELECT courses,students FROM exam_schedule WHERE slot = '{day}2' ")
        rows = cursor.fetchall()
        b_courses = json.loads([row[0] for row in rows][0])
        b_students = json.loads([row[1] for row in rows][0])
        cursor.execute(f"SELECT courses,students FROM exam_schedule WHERE slot = '{day}3' ")
        rows = cursor.fetchall()
        c_courses = json.loads([row[0] for row in rows][0])
        c_students = json.loads([row[1] for row in rows][0])

        all_students=a_students+b_students+c_students
        day_students=list(set(all_students))
        for student in day_students:
            student_set=["","","",""]
            student_set[0]=student
            cursor.execute(f"SELECT course_code FROM student_enrollment_data WHERE id='{student}'")
            rows = cursor.fetchall()
            student_courses = [row[0] for row in rows]

            for course in student_courses:
                if course in a_courses:
                    student_set[1]=course
                elif course in b_courses:
                    student_set[2]=course
                elif course in c_courses:
                    student_set[3]=course


            count=0
            for item in student_set:
                if item=="":
                    count += 1

            if count < 2:
                day_set.append(student_set)
        detailed_set.append(day_set)

    return detailed_set



def exam_schedule_excel_writer(db_filepath):
    if os.path.exists("Exam Schedule.xlsx"):
        os.remove("Exam Schedule.xlsx")
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(f"Exam Schedule.xlsx")
    worksheet = workbook.add_worksheet()

    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM exam_schedule ")
    rows = cursor.fetchall()
    slots=[row[0] for row in rows]
    total_students=[row[3] for row in rows]
    courses=[json.loads(row[1]) for row in rows]

    row=0
    col=0

    worksheet.write(row, col, f"Slot")
    worksheet.write(row, col+1, f"Total Students")
    worksheet.write(row, col+2, f"Courses")

    row += 2

    for i in range(len(slots)):
        col=0
        worksheet.write(row, col, f"{slots[i]}")
        col += 1
        worksheet.write(row, col, f"{total_students[i]}")
        col += 1
        for course in courses[i]:
            worksheet.write(row, col, f"{course}")
            row += 1 # col +=1 if you want courses to be printed in horizontal

        row += 2


    workbook.close()
    return 1


def faculty_schedule_report(db_filepath):
    connection = sqlite3.connect(db_filepath)
    cursor = connection.cursor()
    cursor.execute(f"SELECT slot,courses FROM exam_schedule ")

    rows = cursor.fetchall()
    slots=[json.loads(row[0]) for row in rows]
    courses=[json.loads(row[1]) for row in rows]


    detailed_set=[]
    for i in range(len(slots)):
        instructor_course_list=[]
        instructors=[]
        slot_number=slots[i]
        for course in courses[i]:
            cursor.execute(f"SELECT instructor FROM course_data WHERE course_code = '{course}' ")

            row = cursor.fetchone()
            instructors.append(row[0])
            instructor_course_list.append([row[0],course])
        #print(courses[i])
        #print(instructors)
        item_counts = Counter(instructors)



        for faculty, count in item_counts.items():
            if count > 1:
                instructor_set=[]
                instructor_set.append(slot_number)
                instructor_set.append(faculty)
                instructor_set.append(count)
                course_list=[]
                for index,instructor in enumerate(instructors):
                    if faculty == instructor:
                        course_list.append(courses[i][index])
                instructor_set.append(course_list)
                detailed_set.append(instructor_set)

    """ EXCEL Writing  """
    if os.path.exists("Faculty Check Report.xlsx"):
        os.remove("Faculty Check Report.xlsx")
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook(f"Faculty Check Report.xlsx")
    worksheet = workbook.add_worksheet()

    row = 0
    col=0
    worksheet.write(row,col,"Slot")
    worksheet.write(row, col+1, "Instructor")


    row += 2
    for line in detailed_set:
        col=0
        worksheet.write(row, col, line[0])
        col += 1
        worksheet.write(row, col, line[1])
        col += 1

        for course in line[3]:
            worksheet.write(row, col, course)
            col += 1

        row += 1

    workbook.close()
    return 1





if __name__ == "__main__":
    #clear_exam_scheduling_data(db_filepath)
    #content=initialize_scheduling(db_filepath=db_filepath)
    #first_draft(db_filepath=db_filepath,content=content)
    #value = deschedule_course(db_filepath=db_filepath,exam_slot="13",course="CYP502")
    #value=schedule_course(db_filepath=db_filepath,exam_slot="32",course="CYP502")
    #print(value)
    #update_analysis(db_filepath)
    #swap_slot_content(db_filepath,23,12)
    #update_analysis(db_filepath)
    #balancer(db_filepath)
    #day_swap(db_filepath=db_filepath,dayA=1,dayB=4)
    #detailed_abc=detailed_analysis_abc(db_filepath=db_filepath)
    #detailed_2 = detailed_analysis_all(db_filepath=db_filepath)
    #analysis_excel_writer(detailed_abc=detailed_abc,detailed_cummalative=detailed_2)
    #exam_schedule_excel_writer(db_filepath)
    faculty_schedule_report(db_filepath=db_filepath)

