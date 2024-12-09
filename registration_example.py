#!/usr/bin/env python3

'''A template for a simple app that interfaces with a database on the class server.
This program is complicated by the fact that the class database server is behind a firewall and we are not allowed to
connect directly to the MySQL server running on it. As a workaround, we set up an ssh tunnel (this is the purpose
of the DatabaseTunnel class) and then connect through that. In a more normal database application setting (in
particular if you are writing a database app that connects to a server running on the same computer) you would not
have to bother with the tunnel and could just connect directly.'''

import mysql.connector
import time
import os.path
from db_tunnel import DatabaseTunnel

# Default connection information (can be overridden with command-line arguments)
# Change these as needed for your app. (You should create a token for your database and use its username
# and password here.)
DB_NAME = "crv0425_registration"
DB_USER = "token_dfac"
DB_PASSWORD = "JHJKqAL7sJj_Asec"

# SQL queries/statements that will be used in this program (replace these with the queries/statements needed
# by your program)
SIGN_IN = """
    SELECT name
    FROM Student
    WHERE id = %s
"""

# Use "%s" as a placeholder for where you will need to insert values (e.g., user input)
ADD_NEW_STUDENT = """
    INSERT INTO Student VALUES (%s, %s)
"""

SHOW_REGISTERED = """
    SELECT Enroll.course_prefix, Enroll.course_number, Course.title
    FROM Enroll
    INNER JOIN Course on Enroll.course_prefix = Course.prefix and Enroll.course_number = Course.number
    WHERE Enroll.student_id = (
            SELECT id
            FROM Student
            WHERE name = %s
    )
"""

CREDIT_TOTAL = """
    SELECT SUM(Course.maxCredits)
    FROM Enroll
    INNER JOIN Course on Enroll.course_prefix = Course.prefix and Enroll.course_number = Course.number
    WHERE Enroll.student_id = (
            SELECT id
            FROM Student
            WHERE name = %s
        )
"""

CLASS_SEARCH = """
    SELECT Course.prefix, Course.number, Course.title
    FROM Course
    WHERE Course.title LIKE %s
"""

ADD_CLASS = """
    INSERT INTO Enroll VALUES (%s, %s, %s)
"""

DROP_CLASS = """
    DELETE FROM Enroll
    WHERE Enroll.student_id = %s
    AND Enroll.course_prefix = %s
    AND Enroll.course_number = %s
"""


# If you change the name of this class (and you should) you also need to change it in main() near the bottom
class DatabaseApp:
    '''A simple Python application that interfaces with a database.'''

    def __init__(self, dbHost, dbPort, dbName, dbUser, dbPassword):
        self.dbHost, self.dbPort = dbHost, dbPort
        self.dbName = dbName
        self.dbUser, self.dbPassword = dbUser, dbPassword

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.dbHost, port=self.dbPort, database=self.dbName,
            user=self.dbUser, password=self.dbPassword,
            use_pure=True,
            autocommit=True,
        )
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def runApp(self):
        # The main loop of your program
        # Take user input here, then call methods that you write below to perform whatever
        # queries/tasks your program needs.
        id = input("Enter student id: ")
        student = self.signIn(id)

        while True:
            self.showStudentCourses(student)

            print("\nWhat would you like to do?")
            print("     S) Search for a course")
            print("     A) Add a course")
            print("     D) Drop a course")
            print("     Q) Quit")

            selection = input("\n==> ")

            if selection == "S":
                keyword = input("Enter a keyword to search for: ")
                self.searchForClassByKeyword(keyword)

            if selection == "A":
                course = input("Enter a prefix and number to add (e.g. CMPT 307): ")
                course = course.split()
                prefix = course[0]
                number = course[1]
                self.addClass(id, prefix, number)

            if selection == "D":
                course = input("Enter a prefix and number to add (e.g. CMPT 307): ")
                course = course.split()
                prefix = course[0]
                number = course[1]
                self.dropClass(id, prefix, number)
            if selection == "Q":
                break

    # Add one method here for each database operation your app will perform, then call them from runApp() above

    # An example of a method that runs a query
    # This query searches for student by id. If id is not found new student is added to the system.
    def signIn(self, id):
        # Execute the query
        self.cursor.execute(SIGN_IN, (id,))

        student = None
        for (name,) in self.cursor:
            student = name

        if student is None:
            proceed = input("I don't know a student with that ID! Should I add one? (y/n) ")
            if proceed == 'y':
                name = input("What is this student's name? ")
                self.createNewStudent(id, name)
            if proceed == 'n':
                restart = input("Would you like to quit? (y/n) ")
                if restart == 'y':
                    exit()
                if restart == 'n':
                    print("Program will restart...\n")
                    time.sleep(1)
                    self.runApp()

        else:
            print(f"Welcome, {name}")
            return name

    # An example of a method that inserts a new row

    def showStudentCourses(self, name):
        print("\nClasses you are registered for:")
        self.cursor.execute(SHOW_REGISTERED, (name,))

        for (course_prefix, course_number, title) in self.cursor:
            print(f"    {course_prefix} {course_number} {title}")
        self.getTotalStudentCredits(name)

    def getTotalStudentCredits(self, name):
        self.cursor.execute(CREDIT_TOTAL, (name,))
        total = None
        for (total,) in self.cursor:
            number = total

        if total is None:
            number = 0.0
            print("     (No registered courses)")
        print(f"{number} total credits")

    def searchForClassByKeyword(self, keyword):
        keyword = f"%{keyword}%"
        self.cursor.execute(CLASS_SEARCH, (keyword,))
        for (prefix, number, title) in self.cursor:
            print(f" {prefix} {number} {title}")

    def createNewStudent(self, id, name):
        self.cursor.execute(ADD_NEW_STUDENT, (id, name))


    def addClass(self, id, prefix, number):
        self.cursor.execute(ADD_CLASS, (id, prefix, number))

    def dropClass(self, id, prefix, number):
        self.cursor.execute(DROP_CLASS, (id, prefix, number))


def main():
    import sys
    '''Entry point of the application. Uses command-line parameters to override database connection settings, then invokes runApp().'''
    # Default connection parameters (can be overridden on command line)
    params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }

    needToPrintHelp = False

    # Parse command-line arguments, overriding values in params
    i = 1
    while i < len(sys.argv) and not needToPrintHelp:
        arg = sys.argv[i]
        isLast = (i + 1 == len(sys.argv))

        if arg in ("-h", "-help"):
            needToPrintHelp = True
            break

        elif arg in ("-dbname", "-user", "-password"):
            if isLast:
                needToPrintHelp = True
            else:
                params[arg[1:]] = sys.argv[i + 1]
                i += 1

        else:
            print("Unrecognized option: " + arg, file=sys.stderr)
            needToPrintHelp = True

        i += 1

    # If help was requested, print it and exit
    if needToPrintHelp:
        printHelp()
        return

    try:
        with \
                DatabaseTunnel() as tunnel, \
                DatabaseApp(
                    dbHost='localhost', dbPort=tunnel.getForwardedPort(),
                    dbName=params['dbname'],
                    dbUser=params['user'], dbPassword=params['password']
                ) as app:

            try:
                app.runApp()
            except mysql.connector.Error as err:
                print("\n\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", file=sys.stderr)
                print("SQL error when running database app!\n", file=sys.stderr)
                print(err, file=sys.stderr)
                print("\n\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", file=sys.stderr)

    except mysql.connector.Error as err:
        print("Error communicating with the database (see full message below).", file=sys.stderr)
        print(err, file=sys.stderr)
        print("\nParameters used to connect to the database:", file=sys.stderr)
        print(f"\tDatabase name: {params['dbname']}\n\tUser: {params['user']}\n\tPassword: {params['password']}",
              file=sys.stderr)
        print("""
(Did you install mysql-connector-python and sshtunnel with pip3/pip?)
(Are the username and password correct?)""", file=sys.stderr)


def printHelp():
    print(f'''
Accepted command-line arguments:
    -help, -h          display this help text
    -dbname <text>     override name of database to connect to
                       (default: {DB_NAME})
    -user <text>       override database user
                       (default: {DB_USER})
    -password <text>   override database password
    ''')


if __name__ == "__main__":
    main()
