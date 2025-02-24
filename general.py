from flask import Blueprint, render_template, request, session, redirect
import pymysql  # Import as needed

# Create a Blueprint named 'general_bp'
general_bp = Blueprint('general', __name__)


## functions used

# Fetches airport names for a given city or airport from the database
def get_airports(city_or_airport):
    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute query to fetch airport names
    cursor.execute("SELECT airport_name FROM airport WHERE airport_city = %s", (city_or_airport,))
    airports = cursor.fetchall()
    conn.close()

    # Return a list of airport names if found, else return the original city or airport
    return [airport['airport_name'] for airport in airports] if airports else [city_or_airport]


# Queries the database to retrieve flights based on departure and arrival airports, and date range
def query_flights(depart_airports, arrive_airports, start_date, end_date):
    # Prepare query strings for departure and arrival airports
    depart_airport_str = "('" + "','".join(depart_airports) + "')"
    arrive_airport_str = "('" + "','".join(arrive_airports) + "')"

    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    # Execute query to fetch flights matching the criteria
    query = ("SELECT * FROM flight WHERE DATE(departure_time) = %s AND DATE(arrival_time) = %s AND "
             "departure_airport IN " + depart_airport_str + " AND arrival_airport IN " + arrive_airport_str)
    cursor.execute(query, (start_date, end_date))
    flights = cursor.fetchall()
    conn.close()

    # Return the list of flights
    return flights


# Retrieves the status of a specific flight based on flight number and departure/arrival dates
def get_flight_status(flight_num, depart_date, arrive_date):
    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    # Execute query to fetch flight status
    query = ("SELECT airline_name, flight_num, airplane_id, status FROM flight "
             "WHERE flight_num = %s AND date(departure_time) = %s AND date(arrival_time) = %s")
    cursor.execute(query, (flight_num, depart_date, arrive_date))
    data = cursor.fetchall()
    conn.close()

    # Return flight status data
    return data


# Escapes single quotes in an SQL string to prevent SQL injection 
def sqlsyntax(x):
    return x.replace("'", "''")


# Establishes database connection
def get_db_connection():
    return pymysql.connect(host='localhost',
                           user='root',
                           password='',
                           db='final_project_3',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)


## functions


@general_bp.route('/')
def home_page():
    # Render the home page template
    return render_template('home_page.html')


@general_bp.route('/login')
def login():
    # Render the login page template
    return render_template('login.html')


@general_bp.route('/register')
def register():
    # Render the registration page template
    return render_template('register.html')


@general_bp.route('/flight')
def flight():
    # Render the flight information page template
    return render_template('flight.html')


@general_bp.route('/public_search_flight', methods=['GET', 'POST'])
def public_search_flight():
    # Retrieve departure and arrival dates, cities or airports from the request
    departure_date = request.form['departure_date']
    arrival_date = request.form['arrival_date']
    depart_city_or_airport = request.form['depart_city_or_airport']
    arrive_city_or_airport = request.form['arrive_city_or_airport']

    # Get lists of departure and arrival airports
    depart_airports = get_airports(depart_city_or_airport)
    arrive_airports = get_airports(arrive_city_or_airport)

    # Query flights based on the provided criteria
    flights = query_flights(depart_airports, arrive_airports, departure_date, arrival_date)
    return render_template("flight.html", flights=flights, no_flight=not flights)


@general_bp.route('/public_search_flight_status', methods=['GET', 'POST'])
def public_search_flight_status():
    # Retrieve flight number, departure, and arrival dates from the request
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    arrival_date = request.form['arrival_date']

    # Fetch flight status based on the given criteria
    flight_status = get_flight_status(flight_number, departure_date, arrival_date)
    return render_template('flight.html', flights_status=flight_status) if flight_status else render_template(
        'flight.html', error='Cannot find the flight!')


@general_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
