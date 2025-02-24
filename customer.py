from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from datetime import datetime
import pymysql.cursors
from general import get_db_connection, sqlsyntax


# Create Blueprint
customer_bp = Blueprint('customer', __name__)

## functions used
# Function to search all flights by dates
def search_all_by_dates(conn, start_date, end_date):
    cursor = conn.cursor()
    
    query = "SELECT * FROM flight WHERE departure_time >= %s AND arrival_time <= %s AND status = 'Upcoming'"
    cursor.execute(query, (start_date, end_date))
    flights = cursor.fetchall()
    
    cursor.close()
    
    return flights

# Function to search all flights by location
def search_all_by_location(conn, depart, arrive):
    cursor = conn.cursor()
    
    query_depart_airport = "SELECT airport_name FROM airport WHERE airport_city = %s"
    cursor.execute(query_depart_airport, (depart,))
    depart_airport_data = cursor.fetchall()
    
    if depart_airport_data:
        depart_airport = [airport['airport_name'] for airport in depart_airport_data]
    else:
        depart_airport = [depart]

    depart_airport_str = "('" + "','".join(depart_airport) + "')"

    query_arrive_airport = "SELECT airport_name FROM airport WHERE airport_city = %s"
    cursor.execute(query_arrive_airport, (arrive,))
    arrive_airport_data = cursor.fetchall()
    
    if arrive_airport_data:
        arrive_airport = [airport['airport_name'] for airport in arrive_airport_data]
    else:
        arrive_airport = [arrive]

    arrive_airport_str = "('" + "','".join(arrive_airport) + "')"

    query_flights = "SELECT * FROM flight WHERE departure_airport IN " + depart_airport_str + " AND arrival_airport IN " + arrive_airport_str + " AND status = 'Upcoming'"
    cursor.execute(query_flights)
    flights = cursor.fetchall()
    
    cursor.close()
    
    return flights

# Function to search all flights by dates
def search_all_by_dates_and_location(conn, start_date, end_date, depart, arrive):
    cursor = conn.cursor()
    
    query_depart_airport = "SELECT airport_name FROM airport WHERE airport_city = %s"
    cursor.execute(query_depart_airport, (depart,))
    depart_airport_data = cursor.fetchall()
    
    if depart_airport_data:
        depart_airport = [airport['airport_name'] for airport in depart_airport_data]
    else:
        depart_airport = [depart]

    depart_airport_str = "('" + "','".join(depart_airport) + "')"

    query_arrive_airport = "SELECT airport_name FROM airport WHERE airport_city = %s"
    cursor.execute(query_arrive_airport, (arrive,))
    arrive_airport_data = cursor.fetchall()
    
    if arrive_airport_data:
        arrive_airport = [airport['airport_name'] for airport in arrive_airport_data]
    else:
        arrive_airport = [arrive]

    arrive_airport_str = "('" + "','".join(arrive_airport) + "')"

    query_flights = "SELECT * FROM flight WHERE departure_time >= %s AND arrival_time <= %s AND status = 'Upcoming' AND departure_airport IN " + depart_airport_str + " AND arrival_airport IN " + arrive_airport_str
    cursor.execute(query_flights, (start_date, end_date))
    flights = cursor.fetchall()
    
    cursor.close()
    
    return flights



# Function to search one's flights by dates
def search_flights_by_dates(cursor, email, start_date, end_date):
    query = """
        SELECT *
        FROM flight
        NATURAL JOIN ticket
        NATURAL JOIN purchases
        WHERE customer_email = %s
        AND departure_time >= %s
        AND arrival_time <= %s
        AND status = 'Upcoming'
    """
    cursor.execute(query, (email, start_date, end_date))
    return cursor.fetchall()


# Function to search one's flights by location
def search_flights_by_location(cursor, email, depart_airports, arrive_airports):
    depart_airport_str = "('" + "','".join(depart_airports) + "')"
    arrive_airport_str = "('" + "','".join(arrive_airports) + "')"

    query = """
        SELECT *
        FROM flight
        NATURAL JOIN ticket
        NATURAL JOIN purchases
        WHERE customer_email = %s
        AND status = 'Upcoming'
        AND departure_airport IN {}
        AND arrival_airport IN {}
    """.format(depart_airport_str, arrive_airport_str)

    cursor.execute(query, (email,))
    return cursor.fetchall()


# Function to search one's flights by dates and location
def search_flights_by_dates_and_location(cursor, email, start_date, end_date, depart_airports, arrive_airports):
    depart_airport_str = "('" + "','".join(depart_airports) + "')"
    arrive_airport_str = "('" + "','".join(arrive_airports) + "')"

    query = """
        SELECT *
        FROM flight
        NATURAL JOIN ticket
        NATURAL JOIN purchases
        WHERE customer_email = %s
        AND departure_time >= %s
        AND arrival_time <= %s
        AND status = 'Upcoming'
        AND departure_airport IN {}
        AND arrival_airport IN {}
    """.format(depart_airport_str, arrive_airport_str)

    cursor.execute(query, (email, start_date, end_date))
    return cursor.fetchall()

# Common function to retrieve airport names
def get_airports_from_city_or_airport(input_value, cursor):
    # Query to check both city and airport name
    query = """
    SELECT airport_name 
    FROM airport 
    WHERE airport_city = %s OR airport_name = %s
    """

    cursor.execute(query, (input_value, input_value))
    return [row['airport_name'] for row in cursor.fetchall()]


# Common function to retrieve airlines
def get_airlines(cursor):
    query = "SELECT airline_name FROM airline"
    cursor.execute(query)
    return cursor.fetchall()


# Common function to retrieve flight numbers
def get_flight_numbers(cursor):
    query = "SELECT flight_num FROM flight"
    cursor.execute(query)
    return cursor.fetchall()


# Common function to validate flight
def validate_flight(cursor, airline_name, flight_num):
    query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s"
    cursor.execute(query, (airline_name, flight_num))
    return cursor.fetchone()


# Common function to check if the flight is upcoming
def is_upcoming_flight(cursor, airline_name, flight_num):
    query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND departure_time >= CURDATE()"
    cursor.execute(query, (airline_name, flight_num))
    return cursor.fetchone()


# Common function to get a new ticket ID
def get_new_ticket_id(cursor):
    query = "SELECT max(ticket_id) FROM ticket"
    cursor.execute(query)
    data = cursor.fetchone()
    return data['max(ticket_id)'] + 1


# Handle monthly spending
def handle_monthly_spending(cursor, email):
    query = """
        SELECT SUM(price) as spending, MONTH(CURDATE())-1 as month
        FROM ticket
        NATURAL JOIN purchases
        NATURAL JOIN flight
        WHERE customer_email = %s
        AND purchase_date BETWEEN DATE_ADD(LAST_DAY(DATE_ADD(CURDATE(), INTERVAL -2 MONTH)), INTERVAL 1 DAY)
        AND LAST_DAY(DATE_ADD(CURDATE(), INTERVAL -1 MONTH))
    """
    cursor.execute(query, (email,))
    result = cursor.fetchone()

    if result['spending'] is not None:
        return render_template("customer_spending.html", tot_month=result['spending'], time_way='month')

    error = 'No Spending in the last month'
    return render_template("customer_spending.html", error1=error, time_way='month')


# Handle yearly spending
def handle_yearly_spending(cursor, email):
    query_total = """
        SELECT SUM(price) as spending
        FROM ticket
        NATURAL JOIN purchases
        NATURAL JOIN flight
        WHERE customer_email = %s
        AND YEAR(purchase_date) = YEAR(CURDATE()) - 1
    """
    cursor.execute(query_total, (email,))
    tot_year = cursor.fetchone()['spending']

    if tot_year is None:
        error = 'No Spending in the last year'
        return render_template("customer_spending.html", error2=error, time_way='year')

    query_monthly = """
        SELECT SUM(price) as spending, YEAR(purchase_date) as year, MONTH(purchase_date) as month
        FROM ticket
        NATURAL JOIN purchases
        NATURAL JOIN flight
        WHERE customer_email = %s
        AND YEAR(purchase_date) = YEAR(CURDATE()) - 1
        GROUP BY MONTH(purchase_date), YEAR(purchase_date)
    """
    cursor.execute(query_monthly, (email,))
    monthly_data = cursor.fetchall()

    t_each_month = [{'Month': f"{data['year']}-{data['month']:02}", 'Spending': data['spending'] or 0}
                    for data in monthly_data]

    return render_template("customer_spending.html", tot_year=tot_year, t_each_month=t_each_month, time_way='year')


# Handle custom date range spending
def handle_custom_date_range(cursor, email):
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    query_total = """
        SELECT SUM(price) as spending
        FROM ticket
        NATURAL JOIN purchases
        NATURAL JOIN flight
        WHERE customer_email = %s
        AND purchase_date BETWEEN %s AND %s
    """
    cursor.execute(query_total, (email, start_date, end_date))
    tot_date = cursor.fetchone()['spending']

    if tot_date is None:
        error = f'No Spending between {start_date} and {end_date}'
        return render_template("customer_spending.html", error3=error, time_way='custom')

    query_monthly = """
        SELECT SUM(price) as spending, YEAR(purchase_date) as year, MONTH(purchase_date) as month
        FROM ticket
        NATURAL JOIN purchases
        NATURAL JOIN flight
        WHERE customer_email = %s
        AND purchase_date BETWEEN %s AND %s
        GROUP BY MONTH(purchase_date), YEAR(purchase_date)
    """
    cursor.execute(query_monthly, (email, start_date, end_date))
    monthly_data = cursor.fetchall()

    t_date_each_month = [{'Month': f"{data['year']}-{data['month']:02}", 'Spending': data['spending'] or 0}
                         for data in monthly_data]

    return render_template("customer_spending.html", tot_date=tot_date, t_date_each_month=t_date_each_month,
                           start_date=start_date, end_date=end_date, time_way='custom')

## functions

@customer_bp.route('/customer_login')
def customer_login():
    return render_template('customer_login.html')


@customer_bp.route('/customer_register')
def customer_register():
    return render_template('customer_register.html')



@customer_bp.route('/customer_login_check', methods=['GET', 'POST'])
def customer_login_check():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('psw')

        if email and password:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = 'SELECT * FROM customer WHERE email = %s and password = md5(%s)'
            cursor.execute(query, (email, password))
            data = cursor.fetchone()

            if data:
                session['email'] = email
                query = """
                    SELECT *
                    FROM flight
                    NATURAL JOIN ticket
                    NATURAL JOIN purchases
                    WHERE customer_email = %s
                    AND departure_time BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                """
                cursor.execute(query, (email,))
                flights = cursor.fetchall()

                return render_template('customer_home.html', email=email, flights=flights)
            else:
                error = 'Invalid login or username'
                return render_template('customer_login.html', error=error)

    session.clear()
    return render_template('404.html')


# Authenticates the registration of a customer
@customer_bp.route('/customer_register_check', methods=['POST'])
def customer_register_check():
    # Check if all required fields are present in the request form
    required_fields = [
        'email', 'name', 'password', 'building number', 'street',
        'city', 'state', 'phone number', 'passport number',
        'passport expiration date', 'passport country', 'date of birth'
    ]

    if all(field in request.form for field in required_fields):
        # Retrieve form data
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        building_number = request.form['building number']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        phone_number = request.form['phone number']
        passport_number = request.form['passport number']
        passport_expiration = request.form['passport expiration date']
        passport_country = request.form['passport country']
        date_of_birth = request.form['date of birth']

        # Check if the user with the same email already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        query = 'SELECT * FROM customer WHERE email = %s'
        cursor.execute(query, (email,))
        data = cursor.fetchone()
        error = None

        if data:
            error = "This user already exists"
            return render_template('customer_register.html', error=error)
        else:
            # Insert the new customer record into the database
            insert_query = 'INSERT INTO customer VALUES (%s, %s, md5(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            cursor.execute(insert_query, (
            email, name, password, building_number, street, city, state, phone_number, passport_number,
            passport_expiration, passport_country, date_of_birth))
            conn.commit()
            cursor.close()
            flash("You have successfully registered")
            return render_template('customer_login.html')
    else:
        session.clear()
        return render_template('404.html')


@customer_bp.route('/customer_home')
def customer_home():
    # Retrieve the customer's email from the session
    email = session.get('email')

    if email:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT *
            FROM flight
            NATURAL JOIN ticket
            NATURAL JOIN purchases
            WHERE customer_email = %s
            AND departure_time BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """
        cursor.execute(query, (email,))
        flights = cursor.fetchall()

        return render_template('customer_home.html', email=email, flights=flights)
    else:
        # Handle the case when the 'email' is not found in the session
        flash("Please log in to access this page")
        return render_template('customer_login.html')


@customer_bp.route('/customer_view')
def customer_view():
    return render_template('customer_view.html')


@customer_bp.route('/customer_view_search', methods=['GET', 'POST'])
def customer_view_search():
    if session.get('email') and 'way' in request.form:
        email = session['email']
        way = request.form['way']

        conn = get_db_connection()
        cursor = conn.cursor()
        no_flight = None

        # Search by dates
        if way == 'dates':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            flights = search_flights_by_dates(cursor, email, start_date, end_date)
            if not flights:
                no_flight = 1

        # Search by location
        elif way == 'location':
            depart_city = request.form['depart_city_or_airport']
            arrive_city = request.form['arrive_city_or_airport']
            depart_airports = get_airports_from_city_or_airport(depart_city, cursor)
            arrive_airports = get_airports_from_city_or_airport(arrive_city, cursor)
            flights = search_flights_by_location(cursor, email, depart_airports, arrive_airports)
            if not flights:
                no_flight = 1

        # Search by location and dates
        elif way == 'both':
            start_date = request.form['start_date1']
            end_date = request.form['end_date1']
            depart_city = request.form['depart_city_or_airport1']
            arrive_city = request.form['arrive_city_or_airport1']
            depart_airports = get_airports_from_city_or_airport(depart_city, cursor)
            arrive_airports = get_airports_from_city_or_airport(arrive_city, cursor)
            flights = search_flights_by_dates_and_location(cursor, email, start_date, end_date, depart_airports,
                                                           arrive_airports)
            if not flights:
                no_flight = 1

        # User did not specify a way
        else:
            error = 'Please specify a way to select'
            return render_template("customer_view.html", error=error)

        cursor.close()
        return render_template("customer_view.html", flights=flights, no_flight=no_flight)

    else:
        session.clear()
        return render_template('404.html')


@customer_bp.route('/customer_search_purchase')
def customer_search_purchase():
    if session.get('email'):
        email = session['email']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve a list of airline names
        query_airlines = "SELECT airline_name FROM airline"
        cursor.execute(query_airlines)
        airlines = cursor.fetchall()

        # Retrieve a list of flight numbers
        query_flight_numbers = "SELECT flight_num FROM flight"
        cursor.execute(query_flight_numbers)
        flight_numbers = cursor.fetchall()

        cursor.close()

        return render_template('customer_search_purchase.html', flight_numbers=flight_numbers, airlines=airlines)
    else:
        session.clear()
        return render_template('404.html')


@customer_bp.route('/customer_search', methods = ['GET','POST'])
def customer_search():
    if session.get('email') and 'way' in request.form:
        email = session['email']
        way = request.form['way']
        conn = get_db_connection()
        cursor = conn.cursor()
        no_flight = None

        airlines = get_airlines(cursor)
        flightsnum = get_flight_numbers(cursor)

        if way == 'dates':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            flights = search_all_by_dates(conn, start_date, end_date)
            
            if not flights:
                no_flight = 1
            
            return render_template("customer_search_purchase.html", flights=flights, no_flight=no_flight, flightsnum=flightsnum, airlines=airlines)

        elif way == 'location':
            depart = sqlsyntax(request.form['depart_city_or_airport'])
            arrive = sqlsyntax(request.form['arrive_city_or_airport'])
            
            flights = search_all_by_location(conn, depart, arrive)
            
            if not flights:
                no_flight = 1
            
            return render_template("customer_search_purchase.html", flights=flights, no_flight=no_flight, flightsnum=flightsnum, airlines=airlines)

        elif way == 'both':
            start_date = request.form['start_date1']
            end_date = request.form['end_date1']
            depart = sqlsyntax(request.form['depart_city_or_airport1'])
            arrive = sqlsyntax(request.form['arrive_city_or_airport1'])

            flights = search_all_by_location(conn, depart, arrive)
            
            if not flights:
                no_flight = 1
            
            return render_template("customer_search_purchase.html", flights=flights, no_flight=no_flight, flightsnum=flightsnum, airlines=airlines)

        else:
            error = 'Please specify a way to select'
            return render_template("customer_search_purchase.html", error=error)
    else:
        session.clear()
        return render_template('404.html')



@customer_bp.route('/customer_purchase', methods=['GET', 'POST'])
def customer_purchase():
    if session.get('email') and 'airline_name' in request.form and 'flight_number' in request.form:
        email = session['email']
        airline_name = request.form["airline_name"]
        flight_num = request.form["flight_number"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve airlines and flight numbers
        airlines = get_airlines(cursor)
        flightsnum = get_flight_numbers(cursor)

        # Validate flight
        flight = validate_flight(cursor, airline_name, flight_num)
        if not flight:
            error0 = "The flight doesn't exist or it is not in upcoming status, please try again"
            return render_template('customer_search_purchase.html', error0=error0, airlines=airlines, flightsnum=flightsnum)

        # Validate Flight Date
        if not is_upcoming_flight(cursor, airline_name, flight_num):
            error1 = "The flight is not in the upcoming status"
            return render_template('customer_search_purchase.html', error1=error1, airlines=airlines, flightsnum=flightsnum)

        # Set New Ticket ID
        new_ticket_id = get_new_ticket_id(cursor)

        # check the limit of ticket that cannot exeed the seat number of the airplane
        query = "SELECT * FROM flight natural join airplane WHERE airline_name = %s AND flight_num = %s"
        cursor.execute(query, (airline_name, flight_num))
        airplane = cursor.fetchone()
        query = "SELECT * FROM ticket WHERE airline_name = %s AND flight_num = %s"
        cursor.execute(query, (airline_name, flight_num))
        tickets = cursor.fetchall()
        if len(tickets) >= airplane['seats']:
            error2 = "The flight is full, please try another flight"
            return render_template('customer_search_purchase.html', error1=error2, airlines=airlines, flightsnum=flightsnum)
        
        # Insert a new ticket
        query = "INSERT INTO ticket VALUES (%s, %s, %s)"
        cursor.execute(query, (new_ticket_id, airline_name, flight_num))

        # Insert a new purchase
        query = "INSERT INTO purchases VALUES (%s, %s, %s, CURDATE())"
        cursor.execute(query, (new_ticket_id, email, None))

        conn.commit()
        cursor.close()
        message1 = 'Purchase Successfully!'
        return render_template('customer_search_purchase.html', message=message1, airlines=airlines, flightsnum=flightsnum)
    else:
        session.clear()
        return render_template('404.html')


@customer_bp.route('/customer_spending')
def customer_spending():
    return render_template('customer_spending.html')


@customer_bp.route('/customer_show_spending', methods=['GET', 'POST'])
def customer_show_spending():
    if session.get('email'):
        email = session['email']
        conn = get_db_connection()
        cursor = conn.cursor()
        time_way = request.form['time']

        if time_way == 'month':
            return handle_monthly_spending(cursor, email)

        elif time_way == 'year':
            return handle_yearly_spending(cursor, email)

        else:
            return handle_custom_date_range(cursor, email)

    else:
        session.clear()
        return render_template('404.html')
