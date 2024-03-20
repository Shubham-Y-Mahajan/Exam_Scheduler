import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLineEdit, QPushButton, QComboBox, QMainWindow, \
    QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QToolBar, QStatusBar, QMessageBox

import sys
from backend import schedule_course,deschedule_course

db_filepath="Data.db"
class DatabaseConnection():
    def __init__(self, database=db_filepath):
        self.db = database

    def connection(self):
        connection = sqlite3.connect(self.db)
        return connection


# for larger apps QMainWindow is used as it has more capability(menu bar ,toolbar etc) than QWidget
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Exam Management System")
        self.setMinimumSize(1000, 800)  # min window size

        file_menu_item = self.menuBar().addMenu("&File")
        help_menu_item = self.menuBar().addMenu("&Help")
        edit_menu_item = self.menuBar().addMenu("&Edit")


        schedule_action = QAction(QIcon("icons/add.png"), "[Schedule]", self)
        schedule_action.triggered.connect(self.insert)
        file_menu_item.addAction(schedule_action)

        deschedule_action = QAction(QIcon("icons/search.png"), "[De-schedule]", self)
        deschedule_action.triggered.connect(self.deschedule)
        edit_menu_item.addAction(deschedule_action)

        about_action = QAction("About", self)

        help_menu_item.addAction(about_action)
        """IF THE HELP ITEM DIDNT SHOW 
        about_action.setMenuRole(QAction.MenuRole.NoRole)
        """
        about_action.triggered.connect(self.about)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.table1 = QTableWidget()
        self.table1.setColumnCount(3)
        self.table1.setHorizontalHeaderLabels(("slot", "courses","Total Students"))
        self.table1.verticalHeader().setVisible(False)
        # this disables the by default index column that appears in the table
        #self.setCentralWidget(self.table1)  # special for Q main window

        self.table2 = QTableWidget()

        self.table2.setColumnCount(5)

        self.table2.verticalHeader().setVisible(False)

        # Create a layout to arrange the tables
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.table1)
        layout.addWidget(self.table2)

        # create a toolbar and add toolbar elements
        # By default in toolbar icons are used if QIcons elemnt is present
        toolbar = QToolBar()
        toolbar.setMovable(True)
        self.addToolBar(toolbar)

        """toolbar.addAction(schedule_action)
        toolbar.addAction(deschedule_action)"""

        # Create stautus bar

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # detect a cell click
        self.table2.cellClicked.connect(self.cell_clicked_table2)
        self.table1.cellClicked.connect(self.cell_clicked_table1)

    def load_exam_schedule(self):

        connection = DatabaseConnection().connection()
        cursor=connection.cursor()

        cursor.execute("SELECT slot,courses,total_students FROM exam_schedule")
        result = cursor.fetchall()

        new_result = [(t[0], " , ".join(eval(t[1])), t[2]) for t in result]
        #python list ["A","B","C"] to a string "A,B,C"



        self.table1.setRowCount(0)
        # This command resets the table , thus whenever u run the program you wont get duplicate data
        for row_number, row_data in enumerate(new_result):
            self.table1.insertRow(row_number)
            # This inserts an empty row in the window
            for column_number, data in enumerate(row_data):
                # row_data is a tuple where each element of tuple is a column item
                self.table1.setItem(row_number, column_number, QTableWidgetItem(str(data)))
                # setItem is used to populate the empty row with data
        connection.close()
    def load_not_scheduled(self):
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()

        cursor.execute("SELECT course_code FROM not_scheduled")
        rows = cursor.fetchall()
        not_scheduled_course_list = []
        for tple in rows:
            not_scheduled_course_list.append(tple[0])

        # Set the size of each sublist
        sublist_size = 5

        # Use a list comprehension to create sublists
        result = [not_scheduled_course_list[i:i + sublist_size] for i in
                  range(0, len(not_scheduled_course_list), sublist_size)]

        self.table2.setRowCount(0)
        # This command resets the table , thus whenever u run the program you wont get duplicate data
        for row_number, row_data in enumerate(result):
            self.table2.insertRow(row_number)
            # This inserts an empty row in the window
            for column_number, data in enumerate(row_data):
                # row_data is a tuple where each element of tuple is a column item
                self.table2.setItem(row_number, column_number, QTableWidgetItem(str(data)))
                # setItem is used to populate the empty row with data
        connection.close()



    def cell_clicked_table1(self):
        Deschedule_button = QPushButton("Deschedule Course")
        Deschedule_button.clicked.connect(self.deschedule)

        #delete_button.clicked.connect(self.delete)

        # the below steps were taken to avoid duplication of buttons when we click on multiple cells
        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(Deschedule_button)



    def cell_clicked_table2(self):
        Schedule_button = QPushButton("Schedule Course")
        Schedule_button.clicked.connect(self.schedule)
        delete_button = QPushButton("Delete Record")
        #delete_button.clicked.connect(self.delete)

        # the below steps were taken to avoid duplication of buttons when we click on multiple cells
        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(Schedule_button)
        self.statusbar.addWidget(delete_button)

    def schedule(self):
        schedule_dialog = ScheduleDialog()
        schedule_dialog.exec()

    def deschedule(self):
        deschedule_dialog = DescheduleDialog()
        deschedule_dialog.exec()

    def insert(self):
        dialog_insert = InsertDialog()
        dialog_insert.exec()  # opens new window

    def search(self):
        dialog_search = SearchDialog()
        dialog_search.exec()

    def edit(self):
        dialog = EditDialog()
        dialog.exec()

    def delete(self):
        dialog = DeleteDialog()
        dialog.exec()

    def about(self):
        dialog = AboutDialog()
        dialog.exec()




class ScheduleDialog(QDialog):
    def __init__(self):
        super().__init__()



        self.setWindowTitle("Schedule Course")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

        # Widgets
        # course code
        selected_row=window.table2.currentRow()
        selected_column=window.table2.currentColumn()
        #print(selected_column)
        #print(selected_row)

        not_scheduled_list=self.extract_not_scheduled()
        # 5 is size of sublist
        index=(selected_row*5)+selected_column

        selected_code=not_scheduled_list[index]




        self.course_code = QLineEdit(selected_code)
        self.course_code.setPlaceholderText("Course Code")
        layout.addWidget(self.course_code)

        #  courses drop down list

        self.slot = QComboBox()
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()
        cursor.execute("SELECT slot FROM exam_schedule")

        rows = cursor.fetchall()

        lst_of_tples = rows
        lst = [item[0] for item in lst_of_tples]

        self.slot.addItems(lst)

        layout.addWidget(self.slot)


        # update button
        button = QPushButton("Submit")
        button.clicked.connect(self.Schedule)
        layout.addWidget(button)

        self.setLayout(layout)

    def extract_not_scheduled(self):
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()

        cursor.execute("SELECT course_code FROM not_scheduled")
        rows = cursor.fetchall()
        not_scheduled_course_list = []
        for tple in rows:
            not_scheduled_course_list.append(tple[0])
        connection.close()
        return not_scheduled_course_list


    def Schedule(self):
        exam_slot = self.slot.itemText(self.slot.currentIndex())
        course = self.course_code.text()

        value=schedule_course(db_filepath=db_filepath,exam_slot=exam_slot,course=course)

        if value == 1 :

            window.load_exam_schedule()
            window.load_not_scheduled()
            self.close()  # the dialog box closes

            # Creating confirmation message box
            # the purpose of a Q meesage box is to show prompts and messages
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Success")
            confirmation_widget.setText("The course was scheduled successfully")
            confirmation_widget.exec()

        elif value == -1:
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error: Invalid Course Code ")
            confirmation_widget.setText(" Kindly enter a valid course code")
            confirmation_widget.exec()
        elif value == -2:
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error: Invalid Exam Slot ")
            confirmation_widget.setText("Exam Slot Does Not Exist")
            confirmation_widget.exec()

        elif value == -3:
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error: Data Inconsistency")
            confirmation_widget.setText("Database error , kindly save current status and reboot the database")
            confirmation_widget.exec()

        elif type(value) == int: # value is integer > 700
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error: Capacity Exceeded")
            confirmation_widget.setText(f"The course could not be scheduled as the specified capacity was exceeded\n"
                                        f"Resultant capacity on scheduling would be = {value}")
            confirmation_widget.exec()

        else : # clash list
            self.close()  # the dialog box closes
            dialog_box = QDialog()
            dialog_box.setMinimumSize(300, 200)
            dialog_box.setWindowTitle("Error: Conflict (Clash)")

            layout = QVBoxLayout()

            dialog_box.table = QTableWidget()
            dialog_box.table.setColumnCount(2)
            dialog_box.table.setHorizontalHeaderLabels(("Course", "Students"))
            dialog_box.table.verticalHeader().setVisible(False)
            dialog_box.table.setRowCount(0)


            for row_number, row_data in enumerate(value):
                dialog_box.table.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    dialog_box.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))

            layout.addWidget(dialog_box.table)

            button = QPushButton("OK")
            button.clicked.connect(dialog_box.close)  # Fix: Connect to the close method without parentheses
            layout.addWidget(button)

            dialog_box.setLayout(layout)

            dialog_box.exec()

class DescheduleDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Deschedule Course")
        self.setFixedWidth(300)
        self.setFixedHeight(300)
        index = window.table1.currentRow()
        slot = window.table1.item(index, 0).text()
        courses_string = window.table1.item(index, 1).text()
        layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

        self.slot= QLineEdit(slot)
        self.slot.setPlaceholderText("Slot")
        layout.addWidget(self.slot)

        #  courses drop down list

        self.courses = QComboBox()

        lst=courses_string.split(",")


        for i in range(len(lst)):
            lst[i] = lst[i].strip()


        self.courses.addItems(lst)

        layout.addWidget(self.courses)


        # update button
        button = QPushButton("Submit")
        button.clicked.connect(self.Deschedule)
        layout.addWidget(button)

        self.setLayout(layout)

    def Deschedule(self):
        course = self.courses.itemText(self.courses.currentIndex())
        exam_slot= self.slot.text()

        value = deschedule_course(db_filepath=db_filepath, exam_slot=exam_slot, course=course)
        print(value)
        if value == 1:

            window.load_exam_schedule()
            window.load_not_scheduled()
            self.close()  # the dialog box closes

            # Creating confirmation message box
            # the purpose of a Q meesage box is to show prompts and messages
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Success")
            confirmation_widget.setText("The course was descheduled successfully")
            confirmation_widget.exec()

        elif value == -1:
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error: Invalid Course Code ")
            confirmation_widget.setText(" Kindly enter a valid course code")
            confirmation_widget.exec()

        elif value == -2:
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error: Invalid Exam Slot ")
            confirmation_widget.setText("Exam Slot Does Not Exist")
            confirmation_widget.exec()
        else:
            self.close()  # the dialog box closes
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error : Data Inconsistency ")
            confirmation_widget.setText("Invalid Operation due to two possible reasons :\n"
                                        "a) Course is not scheduled in the first place.\n"
                                        "b) Course Code and Exam Slot don't match")
            confirmation_widget.exec()




class AboutDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")

        content = """
        This app was created during the "Python Mega Course"  
        skibibopopop"""

        self.setText(content)
        # self itself is the Mesage box instance


class EditDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Update Student Data")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

        # get index of row which is selected which is selected
        index = window.table.currentRow()
        column=window.table.currentColumn()
        print(column)


        # from row get student name
        student_name = window.table.item(index, 1).text()
        # from row get id
        self.student_id = window.table.item(index, 0).text()
        # from row get mobile and course
        Course = window.table.item(index, 2).text()
        mobile = window.table.item(index, 3).text()

        # Widgets
        # student name
        self.student_name = QLineEdit(student_name)
        self.student_name.setPlaceholderText("Name")
        layout.addWidget(self.student_name)

        #  courses drop down list

        self.course_name = QComboBox()
        courses = ["Biology", "Math", "Astronomy", "Physics"]
        self.course_name.addItems(courses)
        self.course_name.setCurrentText(Course)
        layout.addWidget(self.course_name)

        #  mobile number

        self.mobile = QLineEdit(mobile)
        self.mobile.setPlaceholderText("Mobile")
        layout.addWidget(self.mobile)

        # update button
        button = QPushButton("Update")
        button.clicked.connect(self.update_student)
        layout.addWidget(button)

        self.setLayout(layout)

    def update_student(self):
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE students SET name = ?, course = ?, mobile = ? WHERE id = ?",
                       (self.student_name.text(),
                        self.course_name.itemText(self.course_name.currentIndex())
                        , self.mobile.text(),
                        self.student_id))
        connection.commit()
        cursor.close()
        connection.close()

        # Refresh the table
        window.load_data()


class DeleteDialog(QDialog):
    def __init__(self): # executed automatically
        super().__init__()
        self.setWindowTitle("Delete Student Data")

        layout = QGridLayout()

        confirmation = QLabel("are you sure you want to delete?")
        yes = QPushButton("Yes")
        no = QPushButton("No")

        layout.addWidget(confirmation, 0, 0, 1, 2)
        layout.addWidget(yes, 1, 0)
        layout.addWidget(no, 1, 1)
        self.setLayout(layout)
        yes.clicked.connect(self.delete_student)

    def delete_student(self):
        # get index of row which is selected which is selected
        index = window.table.currentRow()

        # from row get student name
        student_name = window.table.item(index, 1).text()
        # from row get id
        student_id = window.table.item(index, 0).text()
        # from row get mobile and course
        Course = window.table.item(index, 2).text()
        mobile = window.table.item(index, 3).text()

        connection = DatabaseConnection().connection()
        cursor = connection.cursor()

        cursor.execute("DELETE from students WHERE id = ?", (student_id,))
        connection.commit()
        cursor.close()
        connection.close()

        window.load_data()

        self.close()  # the dialog box closes

        # Creating confirmation message box
        # the purpose of a Q meesage box is to show prompts and messages
        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The record was deleted successfully")
        confirmation_widget.exec()


# New class for New window
class InsertDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Insert Student Data")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

        # Add student name
        self.student_name = QLineEdit()
        self.student_name.setPlaceholderText("Name")
        layout.addWidget(self.student_name)

        # Add courses drop down list
        self.course_name = QComboBox()
        courses = ["Biology", "Math", "Astronomy", "Physics"]
        self.course_name.addItems(courses)
        layout.addWidget(self.course_name)

        # add mobile number
        self.mobile = QLineEdit()
        self.mobile.setPlaceholderText("Mobile")
        layout.addWidget(self.mobile)

        # add  submit button
        button = QPushButton("Register")
        button.clicked.connect(self.add_student)
        layout.addWidget(button)

        self.setLayout(layout)

    def add_student(self):
        name = self.student_name.text()
        course = self.course_name.itemText(self.course_name.currentIndex())  # for comboboxes
        mobile = self.mobile.text()
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO students (name , course , mobile) VALUES (?, ?, ?)",
                       (name, course, mobile))

        connection.commit()  # for sql

        connection.close()
        window.load_data()  # to refresh our window


class SearchDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Search Student Record")
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

        # Search student name
        self.student_name = QLineEdit()
        self.student_name.setPlaceholderText("Name")
        layout.addWidget(self.student_name)

        # add  search button
        button = QPushButton("Register")
        button.clicked.connect(self.search)
        layout.addWidget(button)
        self.setLayout(layout)

    def search(self):
        name = self.student_name.text()
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()

        result = cursor.execute("SELECT * FROM students WHERE name = ?", (name,))
        # we write (name , ) as we need a comma for python to understand its a tuple
        rows = list(result)
        # rows = list of tuples

        items = window.table.findItems(name, Qt.MatchFlag.MatchFixedString)
        for item in items:
            window.table.item(item.row(), 1).setSelected(True)
            # item.row() gives the index of the row which has item
            # , 1 is to specify the column
            # thus we are selecting a cell with row= item.row() and column = 1 (here)


        connection.close()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
window.load_exam_schedule()
window.load_not_scheduled()
sys.exit(app.exec())