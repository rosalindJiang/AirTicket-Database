from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from datetime import datetime
from general import get_db_connection, sqlsyntax


# Create Blueprint
airline_staff_bp = Blueprint('airline_staff', __name__)


def is_valid_staff(cursor, staff_username, airline_name=None):
    query = "SELECT * FROM airline_staff WHERE username = %s"
    query_params = [staff_username]

    if airline_name:
        query += " AND airline_name = %s"
        query_params.append(airline_name)

    cursor.execute(query, tuple(query_params))
    return cursor.fetchone() is not None


def is_duplicate_permission(cursor, staff_username, permission_type):
    query = "SELECT username FROM permission WHERE username = %s AND permission_type = %s"
    cursor.execute(query, (staff_username, permission_type))
    return cursor.fetchone() is not None


def insert_permission(cursor, staff_username, permission_type):
    ins = "INSERT INTO permission VALUES (%s, %s)"
    cursor.execute(ins, (staff_username, permission_type))


def get_upcoming_flights(cursor, airline_name):
    query = "SELECT flight_num, airplane_id, airline_name, departure_airport, arrival_airport, departure_time, arrival_time, price\
             FROM flight\
             WHERE airline_name = %s AND departure_time BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)"
    cursor.execute(query, (airline_name,))
    return cursor.fetchall()


def get_airline_name(cursor, username):
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone()['airline_name']


def get_revenue_last_month(cursor, airline_name):
    error = None

    r_month_cus, r_month_agent = None, None

    # revenue from customer last month
    query = "SELECT SUM(price) as revenue_cus FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE airline_name = %s AND booking_agent_id IS NULL  \
            AND purchase_date BETWEEN DATE_ADD(LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 2 MONTH)), INTERVAL 1 DAY) and LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 1 MONTH)) "
    cursor.execute(query, (airline_name,))
    result = cursor.fetchone()
    if result:
        r_month_cus = result['revenue_cus']

    # revenue from agent last month
    query1 = "SELECT SUM(price)*0.9 as revenue_agent FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE airline_name = %s AND booking_agent_id IS NOT NULL  \
            AND purchase_date BETWEEN DATE_ADD(LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 2 MONTH)), INTERVAL 1 DAY) and LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 1 MONTH)) "
    cursor.execute(query1, (airline_name,))
    result1 = cursor.fetchone()
    if result1:
        r_month_agent = result1['revenue_agent']

    if r_month_cus is None and r_month_agent is None:
        error = f"{airline_name} no revenue from customer and agent in the last month"

    return r_month_cus, r_month_agent, error


def get_revenue_last_year(cursor, airline_name):
    error = None

    r_year_cus, r_year_agent = None, None

    # revenue from customer last year
    query2 = "SELECT SUM(price) as revenue_cus FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE airline_name = %s AND booking_agent_id IS NULL  \
            AND YEAR(purchase_date) = YEAR(CURDATE())-1"
    cursor.execute(query2, (airline_name,))
    result2 = cursor.fetchone()
    if result2:
        r_year_cus = result2['revenue_cus']

    # revenue from agent last year
    query3 = "SELECT SUM(price)*0.9 as revenue_agent FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE airline_name = %s AND booking_agent_id IS NOT NULL  \
            AND YEAR(purchase_date) = YEAR(CURDATE())-1"
    cursor.execute(query3, (airline_name,))
    result3 = cursor.fetchone()
    if result3:
        r_year_agent = result3['revenue_agent']

    if r_year_cus is None and r_year_agent is None:
        error = f"{airline_name} no revenue from customer and agent in the last year"

    return r_year_cus, r_year_agent, error


def has_admin_permission(cursor, username):
    query = "SELECT * FROM permission WHERE username = %s"
    cursor.execute(query, (username,))
    permissions = cursor.fetchall()

    for permission in permissions:
        if permission['permission_type'] == 'Admin':
            return True

    return False


def get_permissions(cursor, username):
    query = "SELECT * FROM permission WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchall()


def check_user_permissions(cursor, username):
    # Check whether the user has admin or operator permissions
    query = "SELECT * FROM permission WHERE username = %s"
    cursor.execute(query, (username,))
    permissions = cursor.fetchall()

    admin = False
    operator = False

    for permission in permissions:
        if permission["permission_type"] == "Admin":
            admin = True
        elif permission["permission_type"] == "Operator":
            operator = True

    return admin, operator


def get_flight_numbers(cursor, airline_name):
    # Get a list of flight numbers associated with the airline
    query = "SELECT flight_num FROM flight WHERE airline_name = %s"
    cursor.execute(query, (airline_name,))
    flight_numbers = [row["flight_num"] for row in cursor.fetchall()]
    return flight_numbers


def update_flight_status(cursor, flight_number, new_status):
    # Update the status of a flight
    query = "UPDATE flight SET status = %s WHERE flight_num = %s"
    cursor.execute(query, (new_status, flight_number))


def airplane_exists(cursor, airline_name, airplane_id):
    # Check if an airplane already exists for the airline
    query = "SELECT * FROM airplane WHERE airline_name = %s AND airplane_id = %s"
    cursor.execute(query, (airline_name, airplane_id))
    return cursor.fetchone() is not None


def insert_airplane(cursor, airline_name, airplane_id, seats):
    # Insert a new airplane for the airline
    query = "INSERT INTO airplane (airline_name, airplane_id, seats) VALUES (%s, %s, %s)"
    cursor.execute(query, (airline_name, airplane_id, seats))


def airport_exists(cursor, airport_name):
    # Check if an airport already exists
    query = "SELECT * FROM airport WHERE airport_name = %s"
    cursor.execute(query, (airport_name,))
    return cursor.fetchone() is not None


def insert_airport(cursor, airport_name, airport_city):
    # Insert a new airport
    query = "INSERT INTO airport (airport_name, airport_city) VALUES (%s, %s)"
    cursor.execute(query, (airport_name, airport_city))


def get_top_booking_agents(cursor, username, time_period):
    query = """
            SELECT 
                MAX(booking_agent.email) AS email, 
                booking_agent.booking_agent_id, 
                COUNT(t.ticket_id) AS ticket
            FROM 
                booking_agent
                JOIN purchases ON booking_agent.booking_agent_id = purchases.booking_agent_id
                JOIN ticket AS t ON purchases.ticket_id = t.ticket_id
                JOIN airline_staff ON t.airline_name = airline_staff.airline_name
            WHERE 
                airline_staff.username = %s
                AND purchases.purchase_date >= DATE_SUB(NOW(), INTERVAL %s MONTH )
            GROUP BY 
                booking_agent.booking_agent_id
            ORDER BY 
                ticket DESC
            LIMIT 5;
            """
    cursor.execute(query, (username,time_period))
    return cursor.fetchall()


def get_top_booking_agents_by_commission(cursor, username, time_period):
    # Get the top booking agents based on commission earned within a specified time period
    query = """
        SELECT MAX(booking_agent.email), booking_agent.booking_agent_id, SUM(flight.price) * 0.1 AS commission
        FROM booking_agent
        JOIN purchases ON booking_agent.booking_agent_id = purchases.booking_agent_id
        JOIN ticket AS t ON purchases.ticket_id = t.ticket_id
        JOIN flight ON t.flight_num = flight.flight_num
        JOIN airline_staff ON flight.airline_name = airline_staff.airline_name
        WHERE airline_staff.username = %s
        AND purchases.purchase_date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
        GROUP BY booking_agent.booking_agent_id
        ORDER BY commission DESC
        LIMIT 5
    """
    cursor.execute(query, (username, time_period))
    return cursor.fetchall()


def get_airline_name(cursor, username):
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    return result['airline_name'] if result else None


def search_flights_by_dates(cursor, airline_name, start_date, end_date):
    query = "SELECT flight_num, airplane_id, airline_name, departure_airport, arrival_airport, departure_time, arrival_time, price \
             FROM flight WHERE airline_name = %s AND departure_time >= %s AND arrival_time <= %s"
    cursor.execute(query, (airline_name, start_date, end_date))
    flights = cursor.fetchall()
    return flights


def search_flights_by_location(cursor, airline_name, depart, arrive):
    depart_airports = get_airports_from_city(cursor, depart)
    arrive_airports = get_airports_from_city(cursor, arrive)

    query = "SELECT * FROM flight WHERE airline_name = %s AND departure_airport IN %s AND arrival_airport IN %s"
    cursor.execute(query, (airline_name, tuple(depart_airports), tuple(arrive_airports)))
    flights = cursor.fetchall()
    return flights


def search_flights_by_both(cursor, airline_name, start_date, end_date, depart, arrive):
    depart_airports = get_airports_from_city(cursor, depart)
    arrive_airports = get_airports_from_city(cursor, arrive)

    query = "SELECT * FROM flight WHERE airline_name = %s AND departure_time >= %s AND arrival_time <= %s \
             AND departure_airport IN %s AND arrival_airport IN %s"
    cursor.execute(query, (airline_name, start_date, end_date, tuple(depart_airports), tuple(arrive_airports)))
    flights = cursor.fetchall()
    return flights


def get_airports_from_city(cursor, city):
    query = "SELECT airport_name FROM airport WHERE airport_city = %s"
    cursor.execute(query, (city,))
    airports = [row['airport_name'] for row in cursor.fetchall()]
    if not airports:
        airports = [city]  
    return airports


def render_permission_error():
    return render_template("airline_staff_view.html", admin=None, operator=None, data=None,
                           error='Sorry you do not have the permission to create flights or change flight status')


def get_airline_info(cursor, username):
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if not result:
        return None, None, None, None

    airline_name = result['airline_name']

    airplane_id_query = "SELECT airplane_id FROM airplane WHERE airline_name = %s"
    cursor.execute(airplane_id_query, (airline_name,))
    airplane_ids = [row['airplane_id'] for row in cursor.fetchall()]

    flight_num_query = "SELECT flight_num FROM flight WHERE airline_name = %s"
    cursor.execute(flight_num_query, (airline_name,))
    flight_nums = [row['flight_num'] for row in cursor.fetchall()]

    airport_query = "SELECT airport_name FROM airport"
    cursor.execute(airport_query)
    airports = [row['airport_name'] for row in cursor.fetchall()]

    return airline_name, airplane_ids, flight_nums, airports


def check_user_permissions(cursor, username):
    query = "SELECT * FROM permission WHERE username = %s"
    cursor.execute(query, (username,))
    permissions = cursor.fetchall()

    admin = False
    operator = False

    for permission in permissions:
        if permission["permission_type"] == "Admin":
            admin = True
        elif permission["permission_type"] == "Operator":
            operator = True

    return admin, operator


def is_valid_flight_input(departure_date, arrival_date, departure_airport, arrival_airport, flight_number):
    try:
        datetime.strptime(departure_date, '%Y-%m-%d')
        datetime.strptime(arrival_date, '%Y-%m-%d')
    except ValueError:
        return False

    return departure_date < arrival_date and departure_airport != arrival_airport and flight_number


def flight_number_exists(cursor, airline_name, flight_number):
    query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s"
    cursor.execute(query, (airline_name, flight_number))
    return cursor.fetchone() is not None


def insert_flight(cursor, airline_name, flight_number, departure_airport,departure_date, departure_time,
                  arrival_airport,arrival_date, arrival_time, price, status, airplane_id):
    ins = "INSERT INTO flight VALUES (\'{}\', \'{}\', \'{}\', \'{},{}\', \'{}\', \'{}, {}\', \'{}\', \'{}\', \'{}\')"
    cursor.execute(
        ins.format(airline_name, flight_number, departure_airport, departure_date, departure_time, arrival_airport,
                   arrival_date, arrival_time, price, status, airplane_id))


def get_total_tickets_last_month(cursor, username):
    query0 = "SELECT COUNT(ticket_id) as ticket FROM ticket NATURAL JOIN purchases NATURAL JOIN airline_staff WHERE username = %s \
             AND purchase_date BETWEEN DATE_ADD(LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 2 MONTH)), INTERVAL 1 DAY) and LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 1 MONTH))"
    cursor.execute(query0, (username,))
    data = cursor.fetchone()

    if data['ticket'] is None:
        return 1, 'No tickets Sold in the last month'

    tot_month = data['ticket']
    return tot_month, None


def get_total_tickets_last_year(cursor, username):
    query0 = "SELECT COUNT(ticket_id) as ticket FROM ticket NATURAL JOIN purchases NATURAL JOIN airline_staff WHERE username = %s \
             AND YEAR(purchase_date) = YEAR(CURDATE())-1"
    cursor.execute(query0, (username,))
    data = cursor.fetchone()

    if data['ticket'] is None:
        return 1, [], 'No tickets Sold in the last year'

    tot_year = data['ticket']

    t_each_month = []
    month_name = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
    for i in range(1, 13):
        query3 = "SELECT COUNT(ticket_id) as ticket FROM ticket NATURAL JOIN purchases NATURAL JOIN airline_staff WHERE username = %s \
                  AND YEAR(purchase_date) = YEAR(CURDATE())-1 AND MONTH(purchase_date) = %s"
        cursor.execute(query3, (username, i))
        data1 = {}
        data1['Month'] = month_name[i - 1]
        data1['Tickets'] = cursor.fetchone()['ticket']
        t_each_month.append(data1)

    return tot_year, t_each_month, None


def get_total_tickets_in_date_range(cursor, username, start_date, end_date):
    query0 = "SELECT COUNT(ticket_id) as ticket FROM ticket NATURAL JOIN purchases NATURAL JOIN airline_staff WHERE username = %s \
             AND purchase_date BETWEEN %s AND %s"
    cursor.execute(query0, (username, start_date, end_date))
    data = cursor.fetchone()

    if data['ticket'] is None:
        return 1, [], 'No tickets Sold during {} and {}'.format(start_date, end_date)

    tot_date = data['ticket']

    t_date_each_month = []
    query4 = "SELECT COUNT(ticket_id) as ticket, YEAR(purchase_date) as year, MONTH(purchase_date) as month \
              FROM ticket NATURAL JOIN purchases NATURAL JOIN airline_staff WHERE username = %s \
              AND purchase_date BETWEEN %s AND %s GROUP BY MONTH(purchase_date), YEAR(purchase_date)"
    cursor.execute(query4, (username, start_date, end_date))
    tot_date_each_month = cursor.fetchall()

    for i in tot_date_each_month:
        data = {}
        data['Month'] = '{}-{:02d}'.format(i['year'], i['month'])
        data['Tickets'] = i['ticket']
        t_date_each_month.append(data)

    return tot_date, t_date_each_month, None

def get_top_destination_cities(cursor):
    query1 = ("SELECT airport_city as destination, COUNT(ticket_id)\
            FROM purchases NATURAL JOIN ticket NATURAL JOIN flight as t, airport\
            WHERE t.arrival_airport = airport.airport_name AND purchase_date between DATE_ADD(LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 4 MONTH)), INTERVAL 1 DAY) and LAST_DAY(DATE_ADD(CURDATE(), INTERVAL - 1 MONTH)) \
            GROUP BY airport_city\
            ORDER BY COUNT(ticket_id) DESC\
            LIMIT 3")
    cursor.execute(query1)
    city_3m = cursor.fetchall()

    query2 = "SELECT airport_city as destination, COUNT(ticket_id)\
            FROM purchases NATURAL JOIN ticket NATURAL JOIN flight as t, airport\
            WHERE t.arrival_airport = airport.airport_name AND YEAR(purchase_date) = YEAR(CURDATE())-1\
            GROUP BY airport_city\
            ORDER BY COUNT(ticket_id) DESC\
            LIMIT 3"
    cursor.execute(query2)
    city_12m = cursor.fetchall()

    return city_3m, city_12m

def get_frequent_customer(cursor, username):
    query = "SELECT customer_email , COUNT(customer_email) as ticket\
            FROM purchases NATURAL JOIN ticket as t, airline_staff\
            WHERE airline_staff.username = %s AND airline_staff.airline_name = t.airline_name AND YEAR(purchase_date) = YEAR(CURDATE())-1\
            GROUP BY customer_email \
            ORDER BY COUNT(customer_email) DESC"
    cursor.execute(query, (username,))
    frequent_customer = cursor.fetchall()

    if frequent_customer:
        max_ticket_count = frequent_customer[0]['ticket']
        frequent_cus = [customer for customer in frequent_customer if customer['ticket'] == max_ticket_count]
        error1 = None
    else:
        frequent_cus = []
        error1 = 'Sorry, no tickets were bought in the last year'

    return frequent_cus, error1


def get_customer_flight_details(cursor, username, customer_email):
    query = "SELECT * FROM customer WHERE email = %s"
    cursor.execute(query, (customer_email,))
    customer_data = cursor.fetchall()

    if not customer_data:
        error = "The customer hasn't registered yet"
        return error, None, None

    query = "SELECT * FROM purchases NATURAL JOIN ticket as t JOIN flight USING(flight_num), airline_staff\
                WHERE airline_staff.username = %s AND airline_staff.airline_name = t.airline_name AND customer_email = %s"
    cursor.execute(query, (username, customer_email))
    customer_flight = cursor.fetchall()

    if not customer_flight:
        error2 = "No tickets were bought by this customer in the past year"
    else:
        error2 = None

    return None, error2, customer_flight



@airline_staff_bp.route('/staff_register')
def airline_staff_register():
    return render_template('airline_staff_register.html')


@airline_staff_bp.route('/staff_login')
def airline_staff_login():
    return render_template('airline_staff_login.html')


@airline_staff_bp.route('/aloginAuth', methods=['POST'])
def airline_staff_login_check():
    username = request.form['username']
    password = request.form['psw']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM airline_staff WHERE username = %s AND password = md5(%s)'
    cursor.execute(query, (username, password))
    data = cursor.fetchone()

    if data:
        airline_name = get_airline_name(cursor, username)
        flights = get_upcoming_flights(cursor, airline_name)

        session['username'] = username
        cursor.close()
        return render_template('airline_staff_home.html', flights=flights, airline_name=airline_name)
    else:
        error = 'Invalid username or password'
        cursor.close()
        return render_template('airline_staff_login.html', error=error)


# Authenticates the register of airline_staff
@airline_staff_bp.route('/airline_staff_register_check', methods=['GET', 'POST'])
def airline_staff_register_check():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['f_name']
    last_name = request.form['l_name']
    date_of_birth = request.form['DOB']
    airline_name = request.form['a_name']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(query, (username))
    
    data = cursor.fetchone()
   
    error = None
    if (data):
        error = "This user already exists"
        return render_template('airline_staff_register.html', error=error)

    query = "SELECT airline_name FROM airline WHERE airline_name = %s"
    cursor.execute(query, (airline_name))

    data = cursor.fetchone()
    error = None

    if (data):
        ins = 'INSERT INTO airline_staff VALUES (%s, md5(%s), %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, first_name, last_name, date_of_birth, airline_name))
        conn.commit()
        cursor.close()
        flash("You have succesfully registered")
        return render_template('airline_staff_login.html')
    else:
        error1 = ("This airline doesn't exist")
        return render_template('airline_staff_register.html', error=error1)


@airline_staff_bp.route('/airline_staff_home')
def airline_staff_home():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    # Find the airline name
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username))
    airline_name = cursor.fetchone()['airline_name']

    query = "SELECT flight_num, airplane_id, airline_name, departure_airport, arrival_airport, departure_time, arrival_time, price\
            FROM flight WHERE airline_name = %s AND departure_time BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)"
    cursor.execute(query, (airline_name))
    flights = cursor.fetchall()

    cursor.close()
    return render_template('airline_staff_home.html', flights=flights, airline_name=airline_name)


@airline_staff_bp.route("/airline_staff_view")
def airline_staff_view():
    return render_template("airline_staff_view.html")


@airline_staff_bp.route("/airline_staff_view_search", methods=['GET', 'POST'])
def airline_staff_view_search():
    username = session['username']
    way = request.form.get('way')
    conn = get_db_connection()
    cursor = conn.cursor()
    no_flight = None
    airline_name = get_airline_name(cursor, username)

    if airline_name is None:
        return render_permission_error()

    if way == 'dates':
        start_date, end_date = request.form['start_date'], request.form['end_date']
        flights = search_flights_by_dates(cursor, airline_name, start_date, end_date)
    elif way == 'location':
        depart, arrive = sqlsyntax(request.form['depart_city_or_airport']), sqlsyntax(
            request.form['arrive_city_or_airport'])
        flights = search_flights_by_location(cursor, airline_name, depart, arrive)
    elif way == 'both':
        start_date, end_date = request.form['start_date1'], request.form['end_date1']
        depart, arrive = sqlsyntax(request.form['depart_city_or_airport1']), sqlsyntax(
            request.form['arrive_city_or_airport1'])
        flights = search_flights_by_both(cursor, airline_name, start_date, end_date, depart, arrive)
    else:
        return render_template("airline_staff_view.html", error='Please specify a way to select')

    return render_template("airline_staff_view.html", flights=flights, no_flight=no_flight, airline_name=airline_name)


@airline_staff_bp.route("/airline_staff_search_customer_flight", methods=['GET', 'POST'])
def airline_staff_search_customer_flight():
    username = session['username']
    flight_num = request.form['flight_num']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find the airline name
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username))
    airline_name = cursor.fetchone()['airline_name']

    # Check whether flight_number is valid
    query1 = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s"
    cursor.execute(query1, (airline_name, flight_num))
    data = cursor.fetchall()

    if not (data):
        error1 = "Invalid flight number. Please try again"
        return render_template('airline_staff_view.html', error1=error1)

    query2 = "SELECT customer_email, ticket_id FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE airline_name = %s ANd flight_num = %s"
    cursor.execute(query2, (airline_name, flight_num))
    customer = cursor.fetchall()

    cursor.close()
    return render_template('airline_staff_view.html', customer=customer)


@airline_staff_bp.route("/airline_staff_create_flight_change_status", methods=['GET', 'POST'])
def airline_staff_create_flight_change_status():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    airline_name, airplane_id, flight_num, airport = get_airline_info(cursor, username)

    if airline_name is None:
        error = 'Sorry you do not have the permission to create flights or change flight status'
        return render_template("airline_staff_create_flight_change_status.html", admin=None, operator=None, data=None, error=error)

    admin, operator = check_user_permissions(cursor, username)
    data = get_permissions(cursor, username)
    return render_template("airline_staff_create_flight_change_status.html", admin=admin, operator=operator, data=data,
                           airplane_id=airplane_id, airport=airport, flight_num=flight_num)


@airline_staff_bp.route("/airline_staff_create_flight", methods=['GET', 'POST'])
def airline_staff_create_flight():
    username = session['username']
    flight_number = request.form['f_n']
    departure_date = request.form['depar_date']
    arrival_date = request.form['arr_date']
    airplane_id = request.form['airp_id']
    arrival_airport = request.form['arrival_airport']
    departure_airport = request.form['depar_airport']
    status = request.form['status']
    price = request.form['price']
    departure_time = request.form['departure_time']
    arrival_time = request.form['arrival_time']
    conn = get_db_connection()
    cursor = conn.cursor()

    airline_name, _, _, airport = get_airline_info(cursor, username)

    if airline_name is None:
        error = 'Sorry you do not have the permission to create flights or change flight status'
        return render_template("airline_staff_create_flight_change_status.html", admin=None, operator=None, airplane_id=None,
                               airport=None, error=error)

    admin, operator = check_user_permissions(cursor, username)

    if not airplane_id or not airport:
        error_msg = 'Failed to create flight. Invalid airplane or airport data.'
        return render_template('airline_staff_create_flight_change_status.html', admin=admin, operator=operator, airplane_id=None,
                               airport=airport, error=error_msg)

    if not is_valid_flight_input(departure_date, arrival_date, departure_airport, arrival_airport, flight_number):
        error_msg = 'Failed to create flight. Invalid input data.'
        return render_template('airline_staff_create_flight_change_status.html', admin=admin, operator=operator, airplane_id=None,
                               airport=airport, error=error_msg)

    if flight_number_exists(cursor, airline_name, flight_number):
        error_msg = 'Failed to create flight. Flight number already exists.'
        return render_template('airline_staff_create_flight_change_status.html', admin=admin, operator=operator, airplane_id=None,
                               airport=airport, error=error_msg)

    # Insert the flight into the database
    insert_flight(cursor, airline_name, flight_number, departure_airport,departure_date, departure_time,
                  arrival_airport,arrival_date, arrival_time, price, status, airplane_id)
    conn.commit()
    cursor.close()

    success_msg = "You have successfully created a new flight."
    return render_template('airline_staff_create_flight_change_status.html', admin=admin, operator=operator, airplane_id=None,
                           airport=airport, success_msg=success_msg)


@airline_staff_bp.route("/airline_staff_change_status", methods=["GET", "POST"])
def airline_staff_change_status():
    username = session["username"]
    flight_number = request.form["flight_number"]
    new_status = request.form["newstatus"]
    conn = get_db_connection()
    cursor = conn.cursor()

    admin, operator = check_user_permissions(cursor, username)
    if admin:
        airline_name = get_airline_name(cursor, username)
        flight_numbers = get_flight_numbers(cursor, airline_name)
        if int(flight_number) not in flight_numbers:
            flash("Invalid flight number.")
        else:
            update_flight_status(cursor, flight_number, new_status)
            conn.commit()
            flash("Flight status updated successfully.")
    else:
        flash("You do not have permission to update flight status.")

    cursor.close()
    return redirect(url_for("airline_staff.airline_staff_create_flight_change_status"))

@airline_staff_bp.route("/airline_staff_add_airplane_airport")
def airline_staff_add_airplane_airport():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check whether Admin
    query = "SELECT * FROM permission WHERE username = %s"
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()

    if not (data):
        error = 'Sorry, you do not have the permission to add airplane or airport' # This person do not have any permission
        return render_template("airline_staff_add_airplane_airport.html", error=error, data=None)
    else:
        per = []
        for i in data:
            per.append(i['permission_type'])
        if 'Admin' not in per: # This person is not admin
            error = 'Sorry, you do not have the permission to add airplane or airport'
            return render_template("airline_staff_add_airplane_airport.html", error=error, data = None)

    return render_template("airline_staff_add_airplane_airport.html", data = data)



@airline_staff_bp.route("/airline_staff_add_airplane", methods=["POST"])
def airline_staff_add_airplane():
    username = session["username"]
    airplane_id = request.form["airplane"]
    seats = request.form["seats"]
    conn = get_db_connection()
    cursor = conn.cursor()

    admin, operator = check_user_permissions(cursor, username)

    if admin:
        airline_name = get_airline_name(cursor, username)

        if airplane_exists(cursor, airline_name, airplane_id):
            flash("This airplane already exists.")
        else:
            insert_airplane(cursor, airline_name, airplane_id, seats)
            conn.commit()
            flash("Airplane added successfully.")
    else:
        flash("You do not have permission to add an airplane.")

    cursor.close()
    return redirect(url_for("airline_staff.airline_staff_add_airplane_airport"))


@airline_staff_bp.route("/airline_staff_add_airport", methods=["POST"])
def airline_staff_add_airport():
    airport_name = request.form["airport"]
    airport_city = request.form["city"]
    conn = get_db_connection()
    cursor = conn.cursor()

    admin, operator = check_user_permissions(cursor, session["username"])

    if admin:
        if airport_exists(cursor, airport_name):
            flash("This airport already exists.")
        else:
            insert_airport(cursor, airport_name, airport_city)
            conn.commit()
            flash("Airport added successfully.")
    else:
        flash("You do not have permission to add an airport.")

    cursor.close()
    return redirect(url_for("airline_staff.airline_staff_add_airplane_airport"))


@airline_staff_bp.route('/airline_staff_view_booking_agent')
def airline_staff_view_booking_agent():
    username = session['username']
    print(username)
    conn = get_db_connection()
    cursor = conn.cursor()

    admin, operator = check_user_permissions(cursor, username)
    top_1m_ticket = get_top_booking_agents(cursor, username, "1")
    top_12m_ticket = get_top_booking_agents(cursor, username, "12")
    top_12m_commission = get_top_booking_agents_by_commission(cursor, username, "12")
    cursor.close()
    return render_template("airline_staff_view_booking_agent.html", top_1m_ticket=top_1m_ticket, top_12m_ticket=top_12m_ticket,
                           top_12m_commission=top_12m_commission)

    # cursor.close()
    # flash("You do not have permission to view booking agents.")
    # return redirect(url_for("airline_staff.airline_staff_home"))


@airline_staff_bp.route('/airline_staff_view_customer', methods=['GET', 'POST'])
def airline_staff_view_customer():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    frequent_customer, error1 = get_frequent_customer(cursor, username)

    return render_template("airline_staff_view_customer.html", frequent_customer=frequent_customer, error1=error1)


@airline_staff_bp.route('/airline_staff_view_customer_flight', methods=['GET', 'POST'])
def airline_staff_view_customer_flight():
    if session.get('username') and 'customer_email' in request.form:
        username = session['username']
        customer_email = request.form['customer_email']
        conn = get_db_connection()
        cursor = conn.cursor()

        frequent_customer, error1 = get_frequent_customer(cursor, username)
        error, error2, customer_flight = get_customer_flight_details(cursor, username, customer_email)

        return render_template("airline_staff_view_customer.html", frequent_customer=frequent_customer, customer_flight=customer_flight,
                               error=error, error1=error1, error2=error2)

    else:
        session.clear()
        return render_template('404.html')


@airline_staff_bp.route('/airline_staff_destination', methods=['GET', 'POST'])
def airline_staff_destination():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    city_3m, city_12m = get_top_destination_cities(cursor)

    return render_template("airline_staff_destination.html", city_3m=city_3m, city_12m=city_12m)





@airline_staff_bp.route('/airline_staff_report')
def airline_staff_report():
    return render_template("airline_staff_report.html")


@airline_staff_bp.route('/airline_staff_show_report', methods=['POST'])
def airline_staff_show_report():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    time_way = request.form['time']

    if time_way == 'month':
        tot_month, error = get_total_tickets_last_month(cursor, username)
        return render_template("airline_staff_report.html", tot_month=tot_month, time_way=time_way, error=error)

    elif time_way == 'year':
        tot_year, t_each_month, error = get_total_tickets_last_year(cursor, username)
        return render_template("airline_staff_report.html", tot_year=tot_year, t_each_month=t_each_month, error=error)

    else:
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        tot_date, t_date_each_month, error = get_total_tickets_in_date_range(cursor, username, start_date, end_date)
        return render_template("airline_staff_report.html", tot_date=tot_date, t_date_each_month=t_date_each_month, error=error,
                               start_date=start_date, end_date=end_date)


@airline_staff_bp.route('/airline_staff_revenue')
def airline_staff_revenue():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find the airline name
    query = "SELECT airline_name FROM airline_staff WHERE username = %s"
    cursor.execute(query, (username))
    airline_name = cursor.fetchone()['airline_name']

    cursor.close()
    return render_template("airline_staff_revenue.html", airline_name=airline_name)


@airline_staff_bp.route('/airline_staff_revenue_show', methods=['GET', 'POST'])
def airline_staff_revenue_show():
    if 'username' not in session:
        flash('You have to login to see the revenue', 'error')
        return redirect(url_for('login')) 

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    time = request.form['time']

    airline_name = get_airline_name(cursor, username)

    if time == 'month':
        r_month_cus, r_month_agent, error1 = get_revenue_last_month(cursor, airline_name)
        return render_template(
            "airline_staff_revenue.html",
            r_month_cus=r_month_cus,
            r_month_agent=r_month_agent,
            error1=error1
        )
    if time == 'year':
        r_year_cus, r_year_agent, error2 = get_revenue_last_year(cursor, airline_name)
        return render_template(
            "airline_staff_revenue.html",
            r_year_cus=r_year_cus,
            r_year_agent=r_year_agent,
            error2=error2
        )


@airline_staff_bp.route('/airline_staff_permission', methods=['GET', 'POST'])
def airline_staff_permission():
    if 'username' not in session:
        flash('You have to login to give permission', 'error')
        return redirect(url_for('login'))  

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    if not has_admin_permission(cursor, username):
        error = 'Sorry, you do not have the right to give permission'
        return render_template("airline_staff_permission.html", error=error, data=None)

    permissions = get_permissions(cursor, username)

    return render_template("airline_staff_permission.html", data=permissions)


@airline_staff_bp.route('/airline_staff_permission_add', methods=['GET', 'POST'])
def airline_staff_permission_add():
    if 'username' not in session:
        flash('You have to login to add permission', 'error')
        return redirect(url_for('login'))  

    username = session['username']
    staff_username = request.form['staff_username']
    permission_type = request.form['permission_type']
    conn = get_db_connection()
    cursor = conn.cursor()

    if not is_valid_staff(cursor, staff_username):
        error = "This staff does not exist"
        return render_template("airline_staff_permission.html", error=error, data=None)

    airline_name = get_airline_name(cursor, username)

    if not is_valid_staff(cursor, staff_username, airline_name):
        error = "This staff does not work for your airline"
        return render_template("airline_staff_permission.html", error=error, data=None)

    if is_duplicate_permission(cursor, staff_username, permission_type):
        error = 'This staff already has this permission'
        return render_template("airline_staff_permission.html", error=error, data=None)

    insert_permission(cursor, staff_username, permission_type)
    conn.commit()
    cursor.close()

    message = 'Permission added successfully'

    return render_template("airline_staff_permission.html", data=message)


@airline_staff_bp.route('/airline_staff_add_booking_agent')
def airline_staff_add_booking_agent():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Combine queries to check permission and get airline name
        query = """
        SELECT p.permission_type, a.airline_name 
        FROM permission p
        LEFT JOIN airline_staff a ON p.username = a.username
        WHERE p.username = %s
        """
        cursor.execute(query, (username,))
        data = cursor.fetchall()

        # Check if data is empty or Admin permission is missing
        if not data or all(row['permission_type'] != 'Admin' for row in data):
            error = 'Sorry, you do not have the permission to add booking agent'
            return render_template("airline_staff_add_booking_agent.html", error=error, data=None)

        airline_name = data[0]['airline_name']
        print(airline_name)
        return render_template("airline_staff_add_booking_agent.html", data=data, airline=airline_name)
    except Exception as e:
        # Log the exception
        print(f"An error occurred: {e}")
        return render_template("error.html", error=str(e))
    finally:
        cursor.close()


@airline_staff_bp.route('/airline_staff_add_booking_agent_check', methods=['GET', 'POST'])
def airline_staff_add_booking_agent_check():
    username = session.get('username')
    if not username:
        flash("User session not found. Please log in again.", "error")
        return redirect(url_for('airline_staff.airline_staff_login'))

    booking_agent_email = request.form.get('booking_agent_email')
    if not booking_agent_email:
        flash("Booking agent email not provided.", "error")
        return redirect(url_for('airline_staff.airline_staff_add_booking_agent'))

    try:
        # to avoid writing close in each single return, we use "with"
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Combined query to check airline name and if the agent is already registered for that airline
            cursor.execute("""
                SELECT a.airline_name, b.email 
                FROM airline_staff a
                LEFT JOIN booking_agent_work_for b 
                ON a.airline_name = b.airline_name AND b.email = %s
                WHERE a.username = %s
                """, (booking_agent_email, username))

            result = cursor.fetchone()
            if not result or not result['airline_name']:
                flash("Airline staff not found.", "error")
                return redirect(url_for('airline_staff.airline_staff_add_booking_agent'))

            airline_name, existing_agent_email = result['airline_name'], result.get('email')
            if existing_agent_email:
                flash(f"This booking agent has already worked for {airline_name}.", "error")
                return redirect(url_for('airline_staff.airline_staff_add_booking_agent'))

            # Insert new booking agent for the airline
            cursor.execute("INSERT INTO booking_agent_work_for VALUES (%s, %s)", (booking_agent_email, airline_name))
            conn.commit()
            flash("This agent has been successfully added to the airline.", "success")

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    return render_template("airline_staff_add_booking_agent.html", data=None, airline=airline_name)
