import json
import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QColor
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLineEdit, QPushButton, QComboBox, QMainWindow, \
    QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QToolBar, QStatusBar, QMessageBox

import sys
from backend import schedule_course,deschedule_course,update_analysis,current_analysis,possible_slots,detailed_analysis,analysis_excel_writer

from database import clear_exam_schedule_table,clear_course_slot_db,initialize_exam_schedule_table\
    ,populate_course_table,csv_to_db ,clear_student_enrollment_data
from initialization_backend import clear_exam_scheduling_data,first_draft,initialize_scheduling
import os

db_filepath="Data.db"
csv_filepath="input.csv"
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
        self.setMinimumSize(1100, 900)  # min window size
        self.showMaximized()

        """ Variables """
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()
        cursor.execute("SELECT sublist_size FROM constraints")
        row = cursor.fetchone()
        sublist_size = row[0]


        settings_menu_item = self.menuBar().addMenu("&Settings")
        database_menu_item = self.menuBar().addMenu("&Database")
        about_menu_item = self.menuBar().addMenu("&About")
        help_menu_item = self.menuBar().addMenu("&Help")


        control_database_action = QAction( "Control", self)
        control_database_action.triggered.connect(self.database)
        database_menu_item.addAction(control_database_action)

        constraints_change_action = QAction( "Change Constraints", self)
        constraints_change_action.triggered.connect(self.constraints)
        settings_menu_item.addAction(constraints_change_action)

        about_action = QAction("About", self)
        about_menu_item.addAction(about_action)
        about_action.triggered.connect(self.about)

        setup_action = QAction("Setup", self)
        help_menu_item.addAction(setup_action)
        setup_action.triggered.connect(self.setup)
        window_action = QAction("Tables of Main Window", self)
        help_menu_item.addAction(window_action)
        window_action.triggered.connect(self.help_window)



        """IF THE HELP ITEM DIDNT SHOW 
        about_action.setMenuRole(QAction.MenuRole.NoRole)
        """


        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.table1 = QTableWidget()
        self.table1.setColumnCount(3)
        self.table1.setHorizontalHeaderLabels(("SLOT", "COURSES", "TOTAL STUDENTS"))
        self.table1.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")

        # Set width for a particular column
        self.table1.setColumnWidth(1, 1400)  # Set the width of the second column
        self.table1.setColumnWidth(2, 160)

        self.table1.verticalHeader().setVisible(False)
        # this disables the by default index column that appears in the table
        #self.setCentralWidget(self.table1)  # special for Q main window



        self.table2 = QTableWidget()
        self.table2.setColumnCount(sublist_size)
        self.table2.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
        self.table2.verticalHeader().setVisible(False)

        self.table5 = QTableWidget()
        self.table5.setColumnCount(1)
        self.table5.setHorizontalHeaderLabels(("NA",))
        self.table5.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
        self.table5.verticalHeader().setVisible(False)
        self.table5.setFixedWidth(120)

        """ analysis table"""
        self.table3 = QTableWidget()
        self.table3.setColumnCount(5)
        self.table3.setHorizontalHeaderLabels(("Day","ab","bc","ac","abc"))
        self.table3.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")


        self.table3.verticalHeader().setVisible(False)


        """possible table"""

        self.table4 = QTableWidget()
        self.table4.setColumnCount(1)

        self.table4.setHorizontalHeaderLabels(("Possibility",))
        self.table4.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
        self.table4.setFixedWidth(120)

        self.table4.verticalHeader().setVisible(False)

        swap_slot_button = QPushButton("Swap Slots")
        swap_slot_button.clicked.connect(self.deschedule)

        swap_day_button = QPushButton("Swap Days")
        swap_day_button.clicked.connect(self.deschedule)

        detailed_analysis_button = QPushButton("Get Detailed Analysis")
        detailed_analysis_button.clicked.connect(self.detailed_analysis)


        """"""""""2 rows 9 column idea , row column rowspan colspan"""""""""

        """self.table1.setFixedHeight(480)
        self.table2.setFixedHeight(400)
        self.table3.setFixedHeight(400)
        self.table4.setFixedHeight(400)
        self.table5.setFixedHeight(400)"""

        layout = QGridLayout(central_widget)
        layout.addWidget(self.table1,1,1,1,9)
        layout.addWidget(self.table4, 2, 1, 1, 1)
        layout.addWidget(self.table2,2,2,1,4)
        layout.addWidget(self.table5, 2, 6, 1, 1)
        layout.addWidget(self.table3,2,7,1,3)
        layout.addWidget(swap_slot_button,3,7,1,1)
        layout.addWidget(swap_day_button,3,8,1,1)
        layout.addWidget(detailed_analysis_button,3,9,1,1)


        # create a toolbar and add toolbar elements
        # By default in toolbar icons are used if QIcons elemnt is present
        """toolbar = QToolBar()
        toolbar.setMovable(True)
        self.addToolBar(toolbar)

        toolbar.addWidget(swap_day_button)
        toolbar.addWidget(swap_slot_button)"""

        # Create stautus bar

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # detect a cell click
        self.table2.cellClicked.connect(self.cell_clicked_table2)
        self.table1.cellClicked.connect(self.cell_clicked_table1)
        self.table5.cellClicked.connect(self.cell_clicked_table5)

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
                item = QTableWidgetItem(str(data))

                item.setBackground(QColor("antiquewhite"))
                item.setForeground(QColor("black"))  # Set text color to purple



                self.table1.setItem(row_number, column_number, item)

                # setItem is used to populate the empty row with data
        connection.close()
    def load_not_scheduled(self):
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()

        """Table 2 ( NON NA courses ) """
        cursor.execute("SELECT course_code FROM not_scheduled where NA_flag = 0")
        rows = cursor.fetchall()
        not_scheduled_course_list = []
        for tple in rows:
            not_scheduled_course_list.append(tple[0])

        not_scheduled_course_list.reverse()

        cursor.execute("SELECT sublist_size FROM constraints")
        row = cursor.fetchone()
        sublist_size = row[0]

        self.table2.setColumnCount(sublist_size)
        # Use a list comprehension to create sublists
        result = [not_scheduled_course_list[i:i + sublist_size] for i in
                  range(0, len(not_scheduled_course_list), sublist_size)]

        self.table2.setRowCount(0)
        # This command resets the table , thus whenever u run the program you wont get duplicate data
        for row_number, row_data in enumerate(result):
            self.table2.insertRow(row_number)
            # This inserts an empty row in the window
            for column_number, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                item.setBackground(QColor("lightcyan"))
                item.setForeground(QColor("black"))  # Set text color to purple

                self.table2.setItem(row_number, column_number, item)

                # setItem is used to populate the empty row with data


        """ Table 5 ( NA courses )"""
        cursor.execute("SELECT course_code FROM not_scheduled where NA_flag = 1")
        rows = cursor.fetchall()
        not_scheduled_course_list = []
        for tple in rows:
            not_scheduled_course_list.append(tple[0])

        not_scheduled_course_list.reverse()

        result = [not_scheduled_course_list[i:i + 1] for i in
                  range(0, len(not_scheduled_course_list), 1)]

        self.table5.setRowCount(0)
        # This command resets the table , thus whenever u run the program you wont get duplicate data
        for row_number, row_data in enumerate(result):
            self.table5.insertRow(row_number)
            # This inserts an empty row in the window
            for column_number, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                item.setBackground(QColor("lightgrey"))
                item.setForeground(QColor("black"))  # Set text color to purple

                self.table5.setItem(row_number, column_number, item)

        connection.close()

    def load_analysis(self):
        connection = DatabaseConnection().connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM analysis")
        rows = cursor.fetchall()
        result=[]
        for tple in rows:
            result.append([tple[0],len(json.loads(tple[1])),len(json.loads(tple[2])),len(json.loads(tple[3])),len(json.loads(tple[4]))])



        self.table3.setRowCount(0)
        # This command resets the table , thus whenever u run the program you wont get duplicate data
        for row_number, row_data in enumerate(result):
            self.table3.insertRow(row_number)
            # This inserts an empty row in the window
            for column_number, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))

                item.setBackground(QColor("lightcyan"))
                item.setForeground(QColor("black"))  # Set text color to purple


                # row_data is a tuple where each element of tuple is a column item
                self.table3.setItem(row_number, column_number, item)
                # setItem is used to populate the empty row with data
        connection.close()

    def cell_clicked_table1(self):
        Deschedule_button = QPushButton("Deschedule Course")
        Deschedule_button.clicked.connect(self.deschedule)

        alternate1_button = QPushButton("Find Alternate Slot")
        alternate1_button.clicked.connect(self.alternate_table1)



        # the below steps were taken to avoid duplication of buttons when we click on multiple cells
        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(Deschedule_button)
        self.statusbar.addWidget(alternate1_button)

    def cell_clicked_table2(self):
        Schedule_button = QPushButton("Schedule Course")
        Schedule_button.clicked.connect(self.schedule)

        delete_button = QPushButton("Remove Course")
        delete_button.clicked.connect(self.NA_shift_1)

        display_button = QPushButton("Change Display")
        display_button.clicked.connect(self.change_display)

        # the below steps were taken to avoid duplication of buttons when we click on multiple cells
        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(Schedule_button)

        self.statusbar.addWidget(delete_button)
        self.statusbar.addWidget(display_button)

        """Code to display possible slots"""
        try:
            selected_row = self.table2.currentRow()
            selected_column = self.table2.currentColumn()


            self.selected_code = self.table2.item(selected_row, selected_column).text()



            value = possible_slots(db_filepath=db_filepath, course=self.selected_code)
            if value:
                result=[[self.selected_code]]
                for slot in value:
                    result.append([slot])

                self.table4.setRowCount(0)
                # This command resets the table , thus whenever u run the program you wont get duplicate data
                for row_number, row_data in enumerate(result):
                    self.table4.insertRow(row_number)
                    # This inserts an empty row in the window
                    for column_number, data in enumerate(row_data):
                        item = QTableWidgetItem(str(data))
                        light_green = QColor(200, 255, 200)
                        item.setBackground(light_green)
                        item.setForeground(QColor("black"))  # Set text color to purple

                        self.table4.setItem(row_number, column_number, item)
                        # row_data is a tuple where each element of tuple is a column item

            else:
                result = [[self.selected_code],["None"]]

                self.table4.setRowCount(0)
                # This command resets the table , thus whenever u run the program you wont get duplicate data
                for row_number, row_data in enumerate(result):
                    self.table4.insertRow(row_number)
                    # This inserts an empty row in the window
                    for column_number, data in enumerate(row_data):
                        item = QTableWidgetItem(str(data))
                        light_red = QColor(255, 200, 200)
                        item.setBackground(light_red)
                        item.setForeground(QColor("black"))  # Set text color to purple

                        # row_data is a tuple where each element of tuple is a column item
                        self.table4.setItem(row_number, column_number, item)
                        # row_data is a tuple where each element of tuple is a column item


        except AttributeError:
            self.table4.setRowCount(0)

    def cell_clicked_table5(self):
        shift_button = QPushButton("Conduct Exam")
        shift_button.clicked.connect(self.NA_shift_0)



        # the below steps were taken to avoid duplication of buttons when we click on multiple cells
        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        self.statusbar.addWidget(shift_button)

    def detailed_analysis(self):
        detailed_set=detailed_analysis(db_filepath=db_filepath)
        analysis_excel_writer(detailed_set=detailed_set)
        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The detailed analysis (excel file) can be found in Reports folder")
        confirmation_widget.exec()


    def NA_shift_0(self):
        try:
            index = window.table5.currentRow()
            course = window.table5.item(index, 0).text()
            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            cursor.execute(f"UPDATE not_scheduled SET NA_flag = ? WHERE course_code = ?", (0,course))

            connection.commit()
            connection.close()
            window.load_not_scheduled()
        except AttributeError:
            pass
    def NA_shift_1(self):
        try:
            index = window.table2.currentRow()
            column=window.table2.currentColumn()
            course = window.table2.item(index, column).text()
            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            cursor.execute(f"UPDATE not_scheduled SET NA_flag = ? WHERE course_code = ?", (1,course))

            connection.commit()
            connection.close()
            window.load_not_scheduled()
        except AttributeError:
            pass
    def change_display(self):
        self.sublist_dialog = QDialog()
        self.sublist_dialog.setMinimumSize(300, 200)
        self.sublist_dialog.setWindowTitle("Confirmation")
        self.sublist_dialog.setMinimumSize(550, 400)
        layout = QVBoxLayout()

        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM constraints")
        rows = cursor.fetchall()
        self.days = rows[0][0]
        self.slots = rows[0][1]
        self.max_capacity = rows[0][2]
        sublist_size = rows[0][3]

        connection.close()

        label4 = QLabel("Set number of columns in Table 2:")
        label4.setStyleSheet("font-weight: bold;")
        label4.setFixedHeight(20)
        layout.addWidget(label4)

        self.t2c = QLineEdit(str(sublist_size))
        self.t2c.setPlaceholderText("Table 2 columns")
        layout.addWidget(self.t2c)

        button = QPushButton("Apply")
        button.clicked.connect(self.apply_sublist)
        layout.addWidget(button)

        button2 = QPushButton("Cancel")
        button2.clicked.connect(self.sublist_dialog.close)
        layout.addWidget(button2)

        self.sublist_dialog.setLayout(layout)
        self.sublist_dialog.exec()

    def apply_sublist(self):

        try:
            if int(self.t2c.text()) > 0:
                connection = sqlite3.connect(db_filepath)
                cursor = connection.cursor()
                cursor.execute("DELETE FROM constraints")
                new_row = [(self.days, self.slots, self.max_capacity, int(self.t2c.text())), ]
                cursor.executemany("INSERT INTO constraints VALUES(?,?,?,?)", new_row)

                connection.commit()
                connection.close()

                self.sublist_dialog.close()

                window.load_not_scheduled()
                confirmation_widget = QMessageBox()
                confirmation_widget.setWindowTitle("Success")
                confirmation_widget.setText("The constraints changed successfully")
                confirmation_widget.exec()
            else:
                confirmation_widget = QMessageBox()
                confirmation_widget.setWindowTitle("Error")
                confirmation_widget.setText("Kindly enter a number > 0")
                confirmation_widget.exec()

        except ValueError:
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error")
            confirmation_widget.setText("Kindly enter valid integer")
            confirmation_widget.exec()

    def schedule(self):
        schedule_dialog = ScheduleDialog()
        schedule_dialog.exec()

    def deschedule(self):
        deschedule_dialog = DescheduleDialog()
        deschedule_dialog.exec()

    def database(self):
        database_dialog = DatabaseDialog()
        database_dialog.exec()

    def constraints(self):
        constraints_dialog = ConstraintsDialog()
        constraints_dialog.exec()

    def alternate_table1(self):
        alternate_dialog = Alternate1Dialog()
        alternate_dialog.exec()

    def about(self):
        dialog = AboutDialog()
        dialog.exec()

    def setup(self):
        dialog = SetupDialog()
        dialog.exec()

    def help_window(self):
        dialog = HelpWindowDialog()
        dialog.exec()




class ConstraintsDialog(QDialog):
    def __init__(self):
        try:
            super().__init__()

            self.setWindowTitle("Change Constraints")
            self.setMinimumSize(300,300)

            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM constraints")
            rows = cursor.fetchall()
            self.fetched_days = rows[0][0]
            self.fetched_slots = rows[0][1] #isme slots change karna hi nai hai
            self.fetched_max_capacity = rows[0][2]

            self.sublist_size = rows[0][3] #isme sublist change karna hi nai hai
            layout = QGridLayout()  # places widgets only vertically stacked as opposed to grid #

            label1 = QLabel("Days:")
            label1.setFixedHeight(20)


            self.days = QLineEdit(str(self.fetched_days))
            self.days.setPlaceholderText("Days")


            label3 = QLabel("Max Capacity:")
            label3.setFixedHeight(20)


            self.capacity = QLineEdit(str(self.fetched_max_capacity))
            self.capacity.setPlaceholderText("Max Capacity")


            # update button
            button = QPushButton("Apply")
            button.clicked.connect(self.apply)
            button.setFixedHeight(25)

            button2 = QPushButton("Cancel")
            button2.clicked.connect(self.close)
            button2.setFixedHeight(25)

            warning_label=QLabel("Warning: If constraints other than max capacity are changed ,\n"
                                 "the exam schedule will reset to the first draft and ,\n"
                                 "you will lose your progress.")
            warning_label.setStyleSheet("background-color: lightyellow; border: 2px solid DarkYellow;")

            """Adding Widgets"""
            layout.addWidget(label1,1,1)
            layout.addWidget(self.days,1,2)
            layout.addWidget(label3,3,1)
            layout.addWidget(self.capacity,3,2)
            layout.addWidget(button,5,1,2,2)
            layout.addWidget(button2,7,1,2,2)
            layout.addWidget(warning_label,9,1,2,2)

            self.setLayout(layout)
        except AttributeError: # attribute error for invalid q line edit input
            pass


    def apply(self):

        try:
            self.close()
            days=int(self.days.text())
            slots=int(self.fetched_slots) # not changing
            max_capacity=int(self.capacity.text())
            t2c=int(self.sublist_size) # not changing
            if days >0 and max_capacity > 0 and t2c >0 :
                connection = sqlite3.connect(db_filepath)
                cursor = connection.cursor()

                cursor.execute("DELETE FROM constraints")
                new_row = [(days,slots,max_capacity,t2c),]
                cursor.executemany("INSERT INTO constraints VALUES(?,?,?,?)", new_row)

                connection.commit()
                connection.close()

                """ Changed constraints database """
                if self.fetched_days != days or self.fetched_max_capacity != max_capacity:
                    clear_exam_schedule_table(db_filepath=db_filepath)  # clean wipe
                    initialize_exam_schedule_table(db_filepath=db_filepath)  # initialization ( [] , [] )
                    content = initialize_scheduling(db_filepath=db_filepath)
                    first_draft(db_filepath=db_filepath,
                                content=content)  # first draft filled in exam_schedule table (used along with initialize scheduling)
                    update_analysis(db_filepath=db_filepath)
                    window.load_analysis()
                    window.load_not_scheduled()
                    window.load_exam_schedule()


                confirmation_widget = QMessageBox()
                confirmation_widget.setWindowTitle("Success")
                confirmation_widget.setText("The constraints changed successfully")
                confirmation_widget.exec()
            else:
                confirmation_widget = QMessageBox()
                confirmation_widget.setWindowTitle("Error")
                confirmation_widget.setText("Kindly enter valid numbers > 0")
                confirmation_widget.exec()

        except ValueError: # int check
            confirmation_widget = QMessageBox()
            confirmation_widget.setWindowTitle("Error")
            confirmation_widget.setText("Kindly enter valid integer")
            confirmation_widget.exec()



class DatabaseDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Database Controls")
        self.setMinimumSize(500,500)

        layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #


        # update button
        button1 = QPushButton("Restore First Draft")
        button2 = QPushButton("Input Changed/Setup")
        button3 = QPushButton("Clean Wipe")
        note_label = QLabel("Note:\n\n"
                            "1)Clean Wipe will clear the entire database\n\n"
                            "2)After Clean Wipe is used you must use Input Changed/Setup \n"
                            "  to get data into database.\n\n"
                            "3)Restore First Draft will recreate the first draft of exam time table using special algorithm\n"
                            "  this option only works when data is present in database. ")
        note_label.setFixedHeight(200)
        note_label.setStyleSheet("background-color: lightyellow; border: 2px solid DarkYellow;")

        button1.clicked.connect(self.restore)
        button2.clicked.connect(self.input_changed)
        button3.clicked.connect(self.clean_wipe)

        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)
        layout.addWidget(note_label)

        self.setLayout(layout)
    def message_box(self):
        self.close()  # the dialog box closes

        # Creating confirmation message box
        # the purpose of a Q meesage box is to show prompts and messages
        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The action was executed successfully")
        confirmation_widget.exec()
    def restore(self):
        # below to be used to just restore to the first draft ( reset )
        clear_exam_scheduling_data(db_filepath)  # exam _schedule table empty but initialized ( [], [])
        content = initialize_scheduling(db_filepath=db_filepath)
        first_draft(db_filepath=db_filepath,content=content)  # first draft filled in exam_schedule table (used along with initialize scheduling)
        update_analysis(db_filepath=db_filepath)
        window.load_analysis()
        window.load_not_scheduled()
        window.load_exam_schedule()
        self.message_box()

    def input_changed(self):
        # below vale used when spreadsheet ( input ) changed
        clear_exam_scheduling_data(db_filepath)
        clear_student_enrollment_data(db_filepath)
        clear_course_slot_db(db_filepath)  # course_data and slot_data table emptied
        csv_to_db(csv_filepath, db_filepath)  # for spreadsheet csv to student enrollment table fill
        populate_course_table(db_filepath)  # student enrollment data se course_data table fill hoga then usse slot data filled
        initialize_exam_schedule_table(db_filepath)
        content = initialize_scheduling(db_filepath=db_filepath)
        first_draft(db_filepath=db_filepath,content=content)  # first draft filled in exam_schedule table (used along with initialize scheduling)
        update_analysis(db_filepath=db_filepath)
        window.load_analysis()
        window.load_not_scheduled()
        window.load_exam_schedule()
        self.message_box()
    def clean_wipe(self):
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM analysis")
        cursor.execute("DELETE FROM constraints")

        new_row = [(5, 3, 700, 5)]
        cursor.executemany("INSERT INTO constraints VALUES(?,?,?,?)", new_row)

        cursor.execute("DELETE FROM course_data")
        cursor.execute("DELETE FROM exam_schedule")
        cursor.execute("DELETE FROM not_scheduled")
        cursor.execute("DELETE FROM slot_data")

        new_rows = []
        alphabets = "ABCDEFGHIJKLM"
        for alphabet in alphabets:
            new_rows.append((f"{alphabet}1", "[]"))
            new_rows.append((f"{alphabet}2", "[]"))
            new_rows.append((f"{alphabet}3", "[]"))
        new_rows.append((f"BLANK", "[]"))
        new_rows.append((f"NA", "[]"))
        cursor.executemany("INSERT INTO slot_data VALUES(?,?)", new_rows)

        cursor.execute("DELETE FROM student_enrollment_data")


        connection.commit()
        connection.close()
        window.load_analysis()
        window.load_not_scheduled()
        window.load_exam_schedule()
        window.table4.setRowCount(0)
        self.message_box()
class ScheduleDialog(QDialog):
    def __init__(self):
        super().__init__()


        try:
            self.setWindowTitle("Schedule Course")
            self.setFixedWidth(300)
            self.setFixedHeight(300)

            layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

            # Widgets
            # course code
            selected_row=window.table2.currentRow()
            selected_column=window.table2.currentColumn()


            self.selected_code=window.table2.item(selected_row,selected_column).text()


            label = QLabel(f"Course : {self.selected_code}")
            label.setStyleSheet("font-weight: bold;")
            label.setFixedHeight(20)
            layout.addWidget(label)

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

        except AttributeError:
            pass




    def Schedule(self):
        self.exam_slot = self.slot.itemText(self.slot.currentIndex())
        self.course = self.selected_code
        was = current_analysis(db_filepath=db_filepath)
        value=schedule_course(db_filepath=db_filepath,exam_slot=self.exam_slot,course=self.course)


        if value == 1 :


            update_analysis(db_filepath=db_filepath)
            will_be = current_analysis(db_filepath=db_filepath)

            deschedule_course(db_filepath=db_filepath, exam_slot=self.exam_slot, course=self.course)
            self.close()  # the dialog box closes
            """analysis dialog box"""
            day = int(self.exam_slot[0])


            self.dialog_box = QDialog()
            self.dialog_box.setMinimumSize(300, 200)
            self.dialog_box.setWindowTitle("Confirmation")
            self.dialog_box.setMinimumSize(550,400)
            layout = QVBoxLayout()


            self.dialog_box.table1 = QTableWidget()
            self.dialog_box.table1.setColumnCount(5)
            self.dialog_box.table1.setHorizontalHeaderLabels(("Day","ab","bc","ac","abc"))
            self.dialog_box.table1.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
            self.dialog_box.table1.verticalHeader().setVisible(False)
            self.dialog_box.table1.setRowCount(0)



            display=[]
            display.append(was[day-1])

            for row_number, row_data in enumerate(display):

                self.dialog_box.table1.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.dialog_box.table1.setItem(row_number, column_number, QTableWidgetItem(str(data)))

            self.dialog_box.table2 = QTableWidget()
            self.dialog_box.table2.setColumnCount(5)
            self.dialog_box.table2.setHorizontalHeaderLabels(("Day", "ab", "bc", "ac", "abc"))
            self.dialog_box.table2.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
            self.dialog_box.table2.verticalHeader().setVisible(False)
            self.dialog_box.table2.setRowCount(0)

            display = []
            display.append(will_be[day - 1])
            for row_number, row_data in enumerate(display):

                self.dialog_box.table2.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.dialog_box.table2.setItem(row_number, column_number, QTableWidgetItem(str(data)))

            note_label = QLabel("Note:\n\n"
                                "1)The first table shows the current analysis\n"
                                f"2)The second table shows the analysis which would occur if {self.course} is scheduled in {self.exam_slot} slot")
            note_label.setFixedHeight(100)
            note_label.setStyleSheet("background-color: lightyellow; border: 2px solid DarkYellow;")


            layout.addWidget(self.dialog_box.table1)
            layout.addWidget(self.dialog_box.table2)
            layout.addWidget(note_label)

            button1 = QPushButton("Apply")
            button1.clicked.connect(self.apply)  # Fix: Connect to the close method without parentheses
            layout.addWidget(button1)

            button2 = QPushButton("Cancel")
            button2.clicked.connect(self.cancel)  # Fix: Connect to the close method without parentheses
            layout.addWidget(button2)

            self.dialog_box.setLayout(layout)

            self.dialog_box.exec()



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
            #self.close()  # the dialog box closes
            self.value=value
            self.allow_dialog=QDialog()
            self.allow_dialog.setMinimumSize(300, 200)
            self.allow_dialog.setWindowTitle("Capacity Exceeded")
            self.allow_dialog.setMinimumSize(550, 400)
            layout = QVBoxLayout()

            label=QLabel(f"The course could not be scheduled as the specified capacity was exceeded\n"
                                        f"Resultant capacity on scheduling would be = {self.value}\n\n"
                         f"Note: If max capacity is incremented , submit course for scheduling again.")
            layout.addWidget(label)
            button1 = QPushButton(f"Increase  Max Capacity to {self.value}")
            button1.clicked.connect(self.increase_capacity)
            layout.addWidget(button1)
            button2 = QPushButton("Close")
            button2.clicked.connect(self.allow_dialog.close)
            layout.addWidget(button2)

            self.allow_dialog.setLayout(layout)
            self.allow_dialog.exec()

        else : # clash list
            self.close()  # the dialog box closes
            dialog_box = QDialog()
            dialog_box.setMinimumSize(300, 200)
            dialog_box.setWindowTitle("Error: Conflict (Clash)")

            layout = QVBoxLayout()

            dialog_box.table = QTableWidget()
            dialog_box.table.setColumnCount(2)
            dialog_box.table.setHorizontalHeaderLabels(("Course", "Students"))
            dialog_box.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
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

    def apply(self):
        self.dialog_box.close()
        schedule_course(db_filepath=db_filepath, exam_slot=self.exam_slot, course=self.course)

        window.load_exam_schedule()
        window.load_not_scheduled()

        window.load_analysis()

        # Creating confirmation message box
        # the purpose of a Q meesage box is to show prompts and messages
        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The course was scheduled successfully")
        confirmation_widget.exec()

    def cancel(self):
        self.dialog_box.close()
        window.load_not_scheduled()
        update_analysis(db_filepath=db_filepath)

        window.load_analysis()

    def increase_capacity(self):
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM constraints")
        rows = cursor.fetchall()
        days = rows[0][0]
        slots = rows[0][1]
        max_capacity = self.value # increased capacity

        t2c = rows[0][3]  # isme sublist change karna hi nai hai

        cursor.execute("DELETE FROM constraints")
        new_row = [(days, slots, max_capacity, t2c), ]
        cursor.executemany("INSERT INTO constraints VALUES(?,?,?,?)", new_row)

        connection.commit()
        connection.close()
        self.allow_dialog.close()
        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText(f"Max Capacity has been incremented to {self.value}")
        confirmation_widget.exec()

class DescheduleDialog(QDialog):
    def __init__(self):
        try:
            super().__init__()

            self.setWindowTitle("Deschedule Course")
            self.setFixedWidth(300)
            self.setFixedHeight(300)

            index = window.table1.currentRow()
            self.slot = window.table1.item(index, 0).text()
            courses_string = window.table1.item(index, 1).text()
            layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

            label= QLabel(f"Slot : {self.slot}")
            label.setStyleSheet("font-weight: bold;")

            layout.addWidget(label)
            label.setFixedHeight(20)

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
        except AttributeError:
            pass

    def Deschedule(self):
        self.course = self.courses.itemText(self.courses.currentIndex())
        self.exam_slot=self.slot
        was=current_analysis(db_filepath)
        value = deschedule_course(db_filepath=db_filepath, exam_slot=self.exam_slot, course=self.course)

        if value == 1:
            update_analysis(db_filepath=db_filepath)
            will_be = current_analysis(db_filepath=db_filepath)
            schedule_course(db_filepath=db_filepath, exam_slot=self.exam_slot, course=self.course)
            self.close()  # the dialog box closes
            """analysis dialog box"""
            day = int(self.exam_slot[0])

            self.dialog_box = QDialog()
            self.dialog_box.setMinimumSize(300, 200)
            self.dialog_box.setWindowTitle("Confirmation")
            self.dialog_box.setMinimumSize(550,400)
            layout = QVBoxLayout()

            self.dialog_box.table1 = QTableWidget()
            self.dialog_box.table1.setColumnCount(5)
            self.dialog_box.table1.setHorizontalHeaderLabels(("Day", "ab", "bc", "ac", "abc"))
            self.dialog_box.table1.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
            self.dialog_box.table1.verticalHeader().setVisible(False)
            self.dialog_box.table1.setRowCount(0)

            display = []
            display.append(was[day - 1])

            for row_number, row_data in enumerate(display):

                self.dialog_box.table1.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.dialog_box.table1.setItem(row_number, column_number, QTableWidgetItem(str(data)))

            self.dialog_box.table2 = QTableWidget()
            self.dialog_box.table2.setColumnCount(5)
            self.dialog_box.table2.setHorizontalHeaderLabels(("Day", "ab", "bc", "ac", "abc"))
            self.dialog_box.table2.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; color: black; font-weight: bold }")
            self.dialog_box.table2.verticalHeader().setVisible(False)
            self.dialog_box.table2.setRowCount(0)

            display = []
            display.append(will_be[day - 1])
            for row_number, row_data in enumerate(display):

                self.dialog_box.table2.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.dialog_box.table2.setItem(row_number, column_number, QTableWidgetItem(str(data)))

            note_label = QLabel("Note:\n\n"
                                "1)The first table shows the current analysis\n"
                                f"2)The second table shows the analysis which would occur if {self.course} is descheduled from {self.exam_slot} slot")
            note_label.setFixedHeight(100)
            note_label.setStyleSheet("background-color: lightyellow; border: 2px solid DarkYellow;")

            layout.addWidget(self.dialog_box.table1)
            layout.addWidget(self.dialog_box.table2)
            layout.addWidget(note_label)

            button1 = QPushButton("Apply")
            button1.clicked.connect(self.apply)  # Fix: Connect to the close method without parentheses
            layout.addWidget(button1)

            button2 = QPushButton("Cancel")
            button2.clicked.connect(self.cancel)  # Fix: Connect to the close method without parentheses
            layout.addWidget(button2)

            self.dialog_box.setLayout(layout)

            self.dialog_box.exec()


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

    def apply(self):
        self.dialog_box.close()
        deschedule_course(db_filepath=db_filepath, exam_slot=self.exam_slot, course=self.course)
        window.load_exam_schedule()
        window.load_not_scheduled()

        window.load_analysis()

        # Creating confirmation message box
        # the purpose of a Q meesage box is to show prompts and messages
        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("The course was descheduled successfully")
        confirmation_widget.exec()

    def cancel(self):
        self.dialog_box.close()
        schedule_course(db_filepath=db_filepath, exam_slot=self.exam_slot, course=self.course)
        update_analysis(db_filepath=db_filepath)

        window.load_analysis()

class Alternate1Dialog(QDialog):
    def __init__(self):
        try:
            super().__init__()

            self.setWindowTitle("Possible Alternate slots")
            self.setFixedWidth(300)
            self.setFixedHeight(300)

            index = window.table1.currentRow()
            self.slot = window.table1.item(index, 0).text()
            courses_string = window.table1.item(index, 1).text()
            layout = QVBoxLayout()  # places widgets only vertically stacked as opposed to grid #

            label= QLabel(f"Slot : {self.slot}")
            label.setStyleSheet("font-weight: bold;")

            layout.addWidget(label)
            label.setFixedHeight(20)

            #  courses drop down list

            self.courses = QComboBox()

            lst=courses_string.split(",")


            for i in range(len(lst)):
                lst[i] = lst[i].strip()


            self.courses.addItems(lst)

            layout.addWidget(self.courses)


            # update button
            button = QPushButton("Submit")
            button.clicked.connect(self.display_possible)
            layout.addWidget(button)

            button2 = QPushButton("Close")
            button2.clicked.connect(self.close)
            layout.addWidget(button2)

            self.setLayout(layout)
        except AttributeError:
            pass

    def display_possible(self):
        """Code to display possible slots"""
        try:
            self.course = self.courses.itemText(self.courses.currentIndex())
            value = possible_slots(db_filepath=db_filepath, course=self.course)


            if value:
                result = [[self.course]]
                for slot in value:
                    result.append([slot])

                window.table4.setRowCount(0)
                # This command resets the table , thus whenever u run the program you wont get duplicate data
                for row_number, row_data in enumerate(result):
                    window.table4.insertRow(row_number)
                    # This inserts an empty row in the window
                    for column_number, data in enumerate(row_data):
                        item = QTableWidgetItem(str(data))
                        light_green = QColor(200, 255, 200)
                        item.setBackground(light_green)
                        item.setForeground(QColor("black"))  # Set text color to purple

                        window.table4.setItem(row_number, column_number, item)

            else:
                result = [[self.course], ["None"]]

                window.table4.setRowCount(0)
                # This command resets the table , thus whenever u run the program you wont get duplicate data
                for row_number, row_data in enumerate(result):
                    window.table4.insertRow(row_number)
                    # This inserts an empty row in the window
                    for column_number, data in enumerate(row_data):
                        item = QTableWidgetItem(str(data))
                        light_red = QColor(255, 200, 200)
                        item.setBackground(light_red)
                        item.setForeground(QColor("black"))  # Set text color to purple

                        # row_data is a tuple where each element of tuple is a column item
                        window.table4.setItem(row_number, column_number, item)


        except IndexError:
            window.table4.setRowCount(0)


class AboutDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")

        content = "This Software was created to aid Office of Academic Affairs in scheduling the university exams of IIT Bhilai.\n\n" \
                  "'University_Exam_Scheduler' was developed by Shubham Yogesh Mahajan(12241730) of BTech CSE - IIT Bhilai.\n\n" \
                  "In case of any query you can reach out to the developer-\n" \
                  "Email:shubhamy@iitbhilai.ac.in\n" \
                  "Alternate Email:mahajanshubham54321@gmail.com\n" \
                  "Phone:+918879466601"

        self.setText(content)
        # self itself is the Mesage box instance

class SetupDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup Instructions")

        content = "# Setup \n" \
                  "The application folder will contain 2 files by default which should not be modified by the user -\n" \
                  "1)Exam_Scheduler (executable)\n" \
                  "2)Data.db (database file)\n\n" \
                  "The input of student data (input.csv) will be given by the intended user\n" \
                  "The excel file of data must have the following format:\n" \
                  "Roll Number;Course_Code;Slot;Instructor\n\n" \
                  "Note: The excel file Pawan Sir had sent to Shubham was of the correct and required format.\n" \
                  "Now make the following changes to the excel file:\n\n" \
                  "1) remove the words TUT and LAB and any () or - around them\n" \
                  "Note: slots of each course should be defined in the following way -\n " \
                  "[Alphabet] or [AlphabetNumber] or [AlphabetNumber,Number] or [[AlphabetNumber],[AlphabetNumber]]\n" \
                  "Example of possible slots = A ; A12 ; A12,B13,C2\n" \
                  "2) Save the excel file as UTF-8 comma delimited file in the application directory ,with the filename as 'input'\n" \
                  "3) run the executable by simply double clicking it.\n" \
                  "4) Go to Database>Control>click Input Changed/Setup\n" \
                  "5) The Setup is complete\n"

        self.setText(content)

class HelpWindowDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elements of Main Window")

        content = "The Main Window Consists of 4 Tables:\n\n" \
                  "1) Table 1 = Exam Schedule Table\n" \
                  "The table with headings 'slot','courses','total_students'\n" \
                  "This table contains the exam schedule\n" \
                  "A row like = 31 ; CS554 ; 127\n" \
                  "Would imply that CS554 will be conducted in the 3rd day's 1st slot and,\n" \
                  "The total number of students giving exam on 3rd day's 1st slot = 127\n\n" \
                  "2) Table 2 = Not Scheduled Table\n" \
                  "The table with numerical numbers as the headings\n" \
                  "This table contains all the courses which have not been scheduled for examination yet.\n\n" \
                  "3) Table 3 = Analysis Table\n" \
                  "The table with headings = 'Day','ab','bc','ac','abc'\n" \
                  "A row like = 2 ; 34 ; 27 ; 45 ; 19\n" \
                  "Would imply that on 2nd day,\n" \
                  "34 students are giving exam in the 1st and 2nd slot (ab) of the day\n" \
                  "27 students are giving exam in the 2nd and 3rd slot (bc) of the day\n" \
                  "45 students are giving exam in the 1st and 3rd slot (ac) of the day\n" \
                  "19 students are giving exam in the 1st 2nd and 3rd slot (abc) of the day\n\n" \
                  "4)Table 4 = Scheduling Possibilities Table\n" \
                  "When a course in table 2 is clicked then the scheduling possibilities of that course \n" \
                  "will be display in the table.\n" \
                  "If 23 is displayed in table 4 when course CS252 is clicked \n" \
                  "Then it implies that CS252 can be scheduled in the 2nd day's 3rd slot\n\n"

        self.setText(content)




if os.path.exists("Data.db") and os.path.exists("input.csv"):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.load_exam_schedule()
    window.load_not_scheduled()
    window.load_analysis()
    sys.exit(app.exec())
else:
    print("Required Files (input.csv and Data.db) NOT PRESENT")