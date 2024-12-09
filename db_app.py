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
import colorama
from colorama import Fore

# Default connection information (can be overridden with command-line arguments)
# Change these as needed for your app. (You should create a token for your database and use its username
# and password here.)
DB_NAME = "lrw0404_airport"
DB_USER = "token_14b5"
DB_PASSWORD = "doxK4vIzoGSgPP7k"

# SQL queries/statements that will be used in this program (replace these with the queries/statements needed
# by your program)
QUERY_ALL_TRIPS = """
    SELECT id, date, departure_time, departure_airport, arrival_airport, flight_duration
    FROM Trips
"""
# Use "%s" as a placeholder for where you will need to insert values (e.g., user input)
ADD_NEW_AIRLINE = """
    INSERT INTO Airline (name) VALUES (%s)
"""

ADD_NEW_TRIP = """INSERT INTO Trips (date, departure_time, arrival_time, plane_tail_number, airline_id, 
departure_airport, arrival_airport, distance, flight_duration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) """

ADD_NEW_AIPORT = """
    INSERT INTO Airports VALUES (%s, %s, %s)
"""
ADD_NEW_AIRPLANE = """
    INSERT INTO Planes VALUES (%s, %s, %s, %s)
"""
ADD_NEW_OWNERS = """
    INSERT INTO Owners VALUES (%s, %s, %s)
"""
DELETE_TRIP = """
    DELETE FROM Trips WHERE id = %s
"""
FIND_AIRLINE_ID = """
    SELECT id FROM Airline WHERE name LIKE %s
"""
LONGEST_FLIGHT = """
    SELECT max_flight_table.departure_airport, id, date, max_flight_table.max_flight_duration , arrival_airport FROM Trips
     INNER JOIN (
			SELECT departure_airport, MAX(flight_duration) as max_flight_duration
            FROM Trips
            Group BY departure_airport
            ) AS max_flight_table on Trips.departure_airport = max_flight_table.departure_airport
            AND max_flight_table.max_flight_duration = Trips.flight_duration 
"""
AIRLINE_CODE = """
    SELECT code FROM Airline WHERE name LIKE %s
"""

AIRPORTS_CODE = """
    SELECT code FROM Airports WHERE code LIKE %s
"""
FIND_TAILNUMBER = """
    SELECT tail_number FROM Planes WHERE tail_number LIKE %s
"""

SEARCH_BY_AIRLINE = """
    SELECT id, date, departure_time, departure_airport, arrival_airport
    FROM Trips
    WHERE airline_id = (
                SELECT id
                FROM Airline
                WHERE name LIKE %s
                )
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
        while True:
            print("\n")
            self.queryAllTrips()
            selection = input("\nPick from the following options: \n \n \t T) Create new trip \n \t A) Create new "
                              "airline \n \t P) Create new airplane \n \t K) Create new airport \n \t D) Delete trip "
                              "\n \t L) Filter by longest flight from an airport \n \t F) Search by airline \n \t Q) QUIT \n "
                              "\n ==> ")

            if selection == ('T' or 't'):
                self.addNewTrip()

            if selection == ('A' or 'a'):
                self.addNewAirline()

            if selection == ('P' or 'p'):
                self.addNewAirplane()

            if selection == ('K' or 'k'):
                self.addNewAirport()

            if selection == ('D' or 'd'):
                self.deleteTrip()

            if selection == ('L' or 'l'):
                self.longestFlight()

            if selection == ('F' or 'f'):
                self.searchByAirline()

            if selection == ('Q' or 'q'):
                print("")
                print("Resume own Navigation")
                break

    # Add one method here for each database operation your app will perform, then call them from runApp() above

    # An example of a method that runs a query
    def queryAllTrips(self):
        # Execute the query
        self.cursor.execute(QUERY_ALL_TRIPS)

        # Iterate over each row of the results
        print("ALL FLIGHTS:")
        for (id, date, departure_time, departure_airport, arrival_airport, flight_duration) in self.cursor:
            # Formatted strings (f"...") let you insert variables into strings by putting them in { }
            print(
                f"FLIGHT NUMBER: {id} DATE: {date} DEPARTURE TIME: {departure_time} DEPARTING AIRPORT: {departure_airport}, DESTINATION: {arrival_airport}, FLIGHT DURATION: {flight_duration} ")

    # An example of a method that inserts a new row
    def deleteTrip(self):
        flight = input("Please select the flight number of the trip you would like to delete (press c to cancel) ")

        if flight == ('c' or 'C'):
            return
        self.cursor.execute(DELETE_TRIP, (flight,))
        print(f"Flight {flight} has been deleted. ")

    def addNewTrip(self):
        date = input("What day will the flight take place in the form YYYY-MM-DD (press c to cancel) ")
        if date == ('c' or 'C'):
            return

        departure_time = input("When will the flight be departing in the form HH:MM:SS (press c to cancel) ")
        if departure_time == ('c' or 'C'):
            return

        arrival_time = input("When will the flight be arriving in the form HH:MM:SS (press c to cancel) ")
        if arrival_time == ('c' or 'C'):
            return

        plane_tail_number = input("Input the tail number of the plane (press c to cancel) ")
        if plane_tail_number == ('c' or 'C'):
            return
        number = None
        # QUERY THAT SEARCHES FOR INPUTED TAIL NUMBER
        self.cursor.execute(FIND_TAILNUMBER, (plane_tail_number,))
        for (tail,) in self.cursor:
            number = tail

        if number is None:
            new_plane = input("That tail number is not in the database. Press enter to proceed with creating a new "
                              "plane. (press c to cancel)")
            if new_plane == ('c' or 'C'):
                return
            else:
                self.addNewAirplane()

        name = None
        airline_name = input("Input the name of the airline (press c to cancel) ")
        # QUERY THAT SEARCHES FOR AIRLINE
        self.cursor.execute(FIND_AIRLINE_ID, (airline_name,))
        for (value,) in self.cursor:
            name = value

        if name is None:
            new_plane = input("That airline is not in the database. Press enter to proceed with creating a new "
                              "airline. (press c to cancel) ")
            if new_plane == ('c' or 'C'):
                return
            else:
                self.addNewAirplane()
                self.cursor.execute(ADD_NEW_AIRLINE, (airline_name,))
                for (value,) in self.cursor:
                    airline_name = value
        else:
            airline_name = value

        arrival = None
        arrival_airport = input("What will the destination airport be? Input the airport code (press c to cancel) ")
        # QUERY THAT SEARCHES FOR AIRPORT
        self.cursor.execute(AIRPORTS_CODE, (arrival_airport,))
        for (value,) in self.cursor:
            arrival = value

        if arrival is None:
            new_airport = input("That airport is not in the database. Press enter to proceed with creating a new "
                                "airport. (press c to cancel) ")
            if new_airport == ('c' or 'C'):
                return
            else:
                self.addNewAirport()

        departure = None
        departure_airport = input("What will the departure airport be? Input the airport code (press c to cancel) ")
        self.cursor.execute(AIRPORTS_CODE, (departure_airport,))
        for (value,) in self.cursor:
            departure = value

        if departure is None:
            new_airport = input("That airport is not in the database. Press enter to proceed with creating a new "
                                "airport. (press c to cancel) ")
            if new_airport == ('c' or 'C'):
                return
            else:
                self.addNewAirport()

        distance = input("What is the distance traveled in the flight? (press c to cancel) ")
        if distance == ('c' or 'C'):
            return

        duration = input("What is the duration of the flight in minutes? (press c to cancel) ")
        if duration == ('c' or 'C'):
            return

        # EXECUTE QUERY THAT INPUTS THE TRIP BASED ON PROVIDED INPUT
        self.cursor.execute(ADD_NEW_TRIP, (date, departure_time, arrival_time,
                                           plane_tail_number, airline_name, arrival_airport,
                                           departure_airport, distance, duration))

    def addNewAirline(self):
        airline = input("What Airline would you like to add? (press c to cancel) ")
        if airline == ('c' or 'C'):
            return
        self.cursor.execute(ADD_NEW_AIRLINE, (airline,))

    def addNewAirplane(self):
        tail_number = input("What is the tail number of the aircraft? (press c to cancel) ")
        if tail_number == ('c' or 'C'):
            return
        name = input("What is the name of the type of aircraft? (press c to cancel) ")
        if name == ('c' or 'C'):
            return
        people_capacity = input("What is the people capacity of the airplane? (press c to cancel) ")
        if people_capacity == ('c' or 'C'):
            return
        range = input("What is the range of the aircraft? (press c to cancel) ")
        if range == ('c' or 'C'):
            return
        partial = None
        total = 0

        owner = input("What is the name of the airline that owns the aircraft? ")
        if owner == ('c' or 'C'):
            return

        type = None
        # QUERY THAT RETRIVES THE ID OF THE AIRLINE BASED ON THE NAME
        self.cursor.execute(FIND_AIRLINE_ID, (owner,))
        for (id,) in self.cursor:
            type = id

        if type is None:
            new_owner = input("That airline is not in the database. Press enter to proceed with creating a new "
                              "airline. ")
            if new_owner == ('c' or 'C'):
                return
            else:
                self.addNewAirline()
                self.cursor.execute(FIND_AIRLINE_ID, (owner,))
                for (id,) in self.cursor:
                    owner = id
        else:
            owner = id
        self.cursor.execute(ADD_NEW_AIRPLANE, (tail_number, name, people_capacity, range))
        complete = input("Does this entity own the entire aircraft? [y/n] ")
        if complete == ("y" or "Y"):
            self.cursor.execute(ADD_NEW_OWNERS, (tail_number, owner, 100))
            return
        else:
            initial_percent = input("What percent does this entity own? ")
            final = int(initial_percent)
            self.cursor.execute(ADD_NEW_OWNERS, (tail_number, owner, initial_percent))
            while final != 100:
                owner = input("What is the next entity? ")
                type = None
                # QUERY THAT RETRIVES THE ID OF THE AIRLINE BASED ON THE NAME
                self.cursor.execute(FIND_AIRLINE_ID, (owner,))
                for (id,) in self.cursor:
                    type = id

                if type is None:
                    new_owner = input(
                        "That airline is not in the database. Press enter to proceed with creating a new "
                        "airline. ")
                    if new_owner == ('c' or 'C'):
                        break
                    else:
                        self.addNewAirline()
                        self.cursor.execute(FIND_AIRLINE_ID, (owner,))
                        for (id,) in self.cursor:
                            owner = id
                else:
                    owner = id
                percentage = input("What percent does this entity own? ")
                total += int(percentage)
                if total > 100:
                    print(f"The total percentage is greater than 100 please reenter previous percentage. Current "
                          f"total: {total - percentage}")
                    print("Prepare to reenter the entity")
                    time.sleep(3)
                    total -= int(percentage)
                else:
                    final += int(percentage)
                    self.cursor.execute(ADD_NEW_OWNERS, (tail_number, owner, percentage))

    def addNewAirport(self):
        airport = input("What's the name of airport would you like to add? (press c to cancel) ")
        if airport == ('c' or 'C'):
            return
        code = input("What is the airport code? (press c to cancel) ")
        if code == ('c' or 'C'):
            return
        location = input("Where is the airport located? (press c to cancel) ")
        if location == ('c' or 'C'):
            return

        self.cursor.execute(ADD_NEW_AIPORT, (code, airport, location))

    def longestFlight(self):
        self.cursor.execute(LONGEST_FLIGHT)
        print("\n")
        for (departure_airport, id, date, distance, arrival_airport) in self.cursor:
            print(
                f"FLIGHT: {id}, DATE: {date}, DEPARTING: {departure_airport}, DESTINATION: {arrival_airport}, DISTANCE: {distance}")
        time.sleep(4)

    def searchByAirline(self):
        airline = input("What airline are you looking for? ")

        self.cursor.execute(SEARCH_BY_AIRLINE, (airline,))
        company = None
        for (id, date, departure_time, departure_airport, arrival_airport) in self.cursor:
            company = id
            if company is None:
                print("That airline has no flights.")
            else:
                print(f"FLIGHT: {id} DATE: {date} DEPARTING: {departure_airport} DESTINATION: {arrival_airport}")
        time.sleep(4)


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
