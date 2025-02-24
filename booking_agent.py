from flask import Blueprint, render_template, request, session, flash
from general import get_db_connection


# Create Blueprint
booking_agent_bp = Blueprint('booking_agent', __name__)

## functions used

# Fetches airport names for a given city or airport from the database
def get_airports_from_city_or_airport(input_value, cursor):
    # Query to check both city and airport name
    query = """
    SELECT airport_name 
    FROM airport 
    WHERE airport_city = %s OR airport_name = %s
    """

    cursor.execute(query, (input_value, input_value))
    return [row['airport_name'] for row in cursor.fetchall()]

# Fetches the airlines that the booking agent works for
def get_airlines_for_agent(cursor, email):
    query = "SELECT airline_name FROM booking_agent_work_for WHERE email = %s"
    cursor.execute(query, (email,))
    data = cursor.fetchall()
    
    if data:
        airline_names = [row['airline_name'] for row in data]
        return airline_names
    else:
        raise Exception("The agent doesn't work for any airlines")

# Check flight validation
def validate_flight(cursor, airline_name, flight_num, airline_for_agent):
    query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND status = 'Upcoming'"
    cursor.execute(query, (airline_name, flight_num))
    data = cursor.fetchall()
    
    if not data or airline_name not in airline_for_agent:
        raise Exception("The flight doesn't exist or is not available for this agent")

# Check booking agent validation
def validate_booking_agent(cursor, email):
    query = "SELECT booking_agent_id FROM booking_agent WHERE email = %s"
    cursor.execute(query, (email,))
    data = cursor.fetchone()
    
    if data:
        return data['booking_agent_id']
    else:
        raise Exception("The booking agent doesn't exist")

# Check customer validation
def validate_customer(cursor, customer_email):
    query = "SELECT * FROM customer WHERE email = %s"
    cursor.execute(query, (customer_email,))
    data = cursor.fetchone()
    
    if not data:
        raise Exception("The customer hasn't registered yet")

# Check flight date validation
def validate_flight_date(cursor, airline_name, flight_num):
    query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND departure_time < CURDATE()"
    cursor.execute(query, (airline_name, flight_num))
    data = cursor.fetchall()
    
    if data:
        raise Exception("The flight is not in the upcoming status")

def insert_ticket(cursor, airline_name, flight_num):
    query = "SELECT MAX(ticket_id) FROM ticket"
    cursor.execute(query)
    data = cursor.fetchone()
    
    new_ticket_id = data['MAX(ticket_id)'] + 1

    query = "INSERT INTO ticket VALUES (%s, %s, %s)"
    cursor.execute(query, (new_ticket_id, airline_name, flight_num))
    
    return new_ticket_id

def insert_purchase(cursor, ticket_id, customer_email, booking_agent):
    query = "INSERT INTO purchases VALUES (%s, %s, %s, CURDATE())"
    cursor.execute(query, (ticket_id, customer_email, booking_agent))



@booking_agent_bp.route('/booking_agent_register')
def booking_agent_register():
    return render_template('booking_agent_register.html')


@booking_agent_bp.route('/booking_agent_login')
def booking_agent_login():
    return render_template('booking_agent_login.html')


@booking_agent_bp.route('/booking_agent_login_check', methods=['GET', 'POST'])
def booking_agent_login_check():
    if 'email' in request.form and 'psw' in request.form:
        email = request.form['email']
        password = request.form['psw']

        conn = get_db_connection()
        cursor = conn.cursor()
        query = 'SELECT * FROM booking_agent WHERE email = %s and password = md5(%s)'
        cursor.execute(query, (email, password))
        data = cursor.fetchone()
        error = None

        if data:
            query1 = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN booking_agent JOIN flight USING (flight_num) WHERE booking_agent.email = %s AND flight.status ='Upcoming'"
            cursor.execute(query1, (email))
            data1 = cursor.fetchall()
            query2 = "SELECT airline_name FROM booking_agent_work_for WHERE email = %s"
            cursor.execute(query2, (email))
            data2 = cursor.fetchall()
            cursor.close()
            session['email'] = email
            return render_template('booking_agent_home.html', flights=data1, email=email, airlines_work_for=data2)
        else:
            error = 'Invalid login or username'
            return render_template('booking_agent_login.html', error=error)
    else:
        session.clear()
        return render_template('404.html')


@booking_agent_bp.route('/booking_agent_register_check', methods=['POST'])
def booking_agent_register_check():
    email = request.form['email']
    password = request.form['password']
    booking_agent_id = request.form['B_ID']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the email already exists
    query_email = 'SELECT * FROM booking_agent WHERE email = %s'
    cursor.execute(query_email, (email,))
    data_email = cursor.fetchone()

    # Check if the booking agent ID already exists
    query_id = 'SELECT * FROM booking_agent WHERE booking_agent_id = %s'
    cursor.execute(query_id, (booking_agent_id,))
    data_id = cursor.fetchone()

    if data_email and data_id:
        # If both email and booking agent ID exist, return an error
        error = "This user already exists: Invalid Email and Booking Agent ID"
        return render_template('booking_agent_register.html', error=error)
    elif data_email:
        # If only email exists, return an error
        error = "This user already exists: Invalid Email"
        return render_template('booking_agent_register.html', error=error)
    elif data_id:
        # If only booking agent ID exists, return an error
        error = "This user already exists: Invalid Booking Agent ID"
        return render_template('booking_agent_register.html', error=error)
    else:
        # Insert the new booking agent into the database
        ins = "INSERT INTO booking_agent VALUES (%s, md5(%s), %s)"
        cursor.execute(ins, (email, password, booking_agent_id))
        conn.commit()
        cursor.close()
        flash("You have successfully registered")
        return render_template('booking_agent_login.html')


@booking_agent_bp.route('/booking_agent_home')
def booking_agent_home():
    if session.get('email'):
        email = session['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        query1 = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN booking_agent JOIN flight USING (flight_num) WHERE booking_agent.email = %s AND flight.status ='Upcoming'"
        cursor.execute(query1, (email))
        data1 = cursor.fetchall()
        query2 = "SELECT airline_name FROM booking_agent_work_for WHERE email = %s"
        cursor.execute(query2, (email))
        data2 = cursor.fetchall()
        cursor.close()
        return render_template('booking_agent_home.html', flights=data1, email=email, airlines_work_for=data2)
    else:
        session.clear()
        return render_template('404.html')


@booking_agent_bp.route("/booking_agent_view")
def booking_agent_view():
    return render_template("booking_agent_view.html")


@booking_agent_bp.route("/booking_agent_view_search", methods=['GET', 'POST'])
def booking_agent_view_search():
    if 'way' not in request.form:
        return render_template("booking_agent_view.html", error='Please specify a way to select')

    email = session['email']
    way = request.form['way']
    no_flight = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN \
                        booking_agent JOIN flight USING (flight_num) WHERE booking_agent.email = %s"
        params = [email]

        if way in ['dates', 'both']:
            start_date = request.form['start_date' if way == 'dates' else 'start_date1']
            end_date = request.form['end_date' if way == 'dates' else 'end_date1']
            query += " AND departure_time >= %s AND arrival_time <= %s"
            params.extend([start_date, end_date])

        if way in ['location', 'both']:
            depart_city = request.form['depart_city_or_airport' if way == 'location' else 'depart_city_or_airport1']
            arrive_city = request.form['arrive_city_or_airport' if way == 'location' else 'arrive_city_or_airport1']
            depart_airports = get_airports_from_city_or_airport(depart_city, cursor)
            arrive_airports = get_airports_from_city_or_airport(arrive_city, cursor)
            
            query += " AND departure_airport IN %s AND arrival_airport IN %s"
            params.extend([tuple(depart_airports), tuple(arrive_airports)])

        cursor.execute(query, tuple(params))
        flights = cursor.fetchall()

        if not flights:
            no_flight = 1

    except Exception as e:
        return render_template("booking_agent_view.html", error=str(e))
    finally:
        cursor.close()
        conn.close()

    return render_template("booking_agent_view.html", flights=flights, no_flight=no_flight)


@booking_agent_bp.route('/booking_agent_search_purchase')
def booking_agent_search_purchase():
    if session.get('email'):
        email = session['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        query1 = "SELECT airline_name FROM booking_agent_work_for WHERE email = %s"
        cursor.execute(query1, (email))
        data1 = cursor.fetchall()

        if data1:
            airline = []
            for i in data1:
                airline.append(i['airline_name'])

            airline_for_agent = "('" + "','".join(airline) + "')"
            query2 = "SELECT flight_num FROM flight WHERE airline_name IN " + airline_for_agent
            cursor.execute(query2)
            data2 = cursor.fetchall()
        else:
            data2 = None
        cursor.close()
        return render_template('booking_agent_search_purchase.html', airlines_work_for=data1, flights_for_airlines=data2)
    else:
        session.clear()
        return render_template('404.html')


def sqlsyntax(x):
    if "'" not in x:
        return x
    new = ''
    for i in x:
        if i == "'":
            new += "''"
        else:
            new += i
    return new


@booking_agent_bp.route('/booking_agent_search', methods=['POST'])
def booking_agent_search():
    if session.get('email') and 'way' in request.form:
        way = request.form['way']
        conn = get_db_connection()
        cursor = conn.cursor()
        no_flight = None

        email = session['email']
        query4 = "SELECT airline_name FROM booking_agent_work_for WHERE email = %s"
        cursor.execute(query4, (email))
        data4 = cursor.fetchall()

        if (data4):
            airline = []
            for i in data4:
                airline.append(i['airline_name'])

            airline_for_agent = "('" + "','".join(airline) + "')"
            query5 = "SELECT flight_num FROM flight WHERE airline_name IN " + airline_for_agent
            cursor.execute(query5)
            data5 = cursor.fetchall()
        else:
            data5 = None

        # Search by dates
        if way == 'dates':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            query1 = "SELECT * FROM flight WHERE departure_time >= %s AND arrival_time <= %s AND status = 'Upcoming'"
            cursor.execute(query1, (start_date, end_date))
            flights = cursor.fetchall()
            if not (flights):
                no_flight = 1
            return render_template("booking_agent_search_purchase.html", flights=flights, no_flight=no_flight, airlines_work_for=data4, flights_for_airlines = data5)

        # Search by location
        elif way == 'location':
            depart0 = request.form['depart_city_or_airport']
            arrive0 = request.form['arrive_city_or_airport']
            depart = sqlsyntax(depart0)
            arrive = sqlsyntax(arrive0)

            cursor = conn.cursor()
            query1 = "SELECT airport_name FROM airport WHERE airport_city = %s"
            cursor.execute(query1, (depart))
            data1 = cursor.fetchall()

            if (data1):
                if len(data1) == 1:
                    depart_airport = [data1[0]['airport_name']]
                else:
                    depart_airport = []

                    for airport in data1:
                        depart_airport.append(airport['airport_name'])
            else:
                depart_airport = [depart]

            depart_airport_str = "('" + "','".join(depart_airport) + "')"

            query2 = "SELECT airport_name FROM airport WHERE airport_city = %s"
            cursor.execute(query2, (arrive))
            data2 = cursor.fetchall()
            if (data2):
                if len(data2) == 1:
                    arrive_airport = [data2[0]['airport_name']]
                else:
                    arrive_airport = []
                    for i in data2:
                        arrive_airport.append(i['airport_name'])
            else:
                arrive_airport = [arrive]

            arrive_airport_str = "('" + "','".join(arrive_airport) + "')"

            query3 = "SELECT * FROM flight WHERE departure_airport IN " + depart_airport_str + " AND arrival_airport IN " + arrive_airport_str + " AND status = 'Upcoming'"
            cursor.execute(query3)
            flights = cursor.fetchall()
            cursor.close()
            if not (flights):
                no_flight = 1
            return render_template("booking_agent_search_purchase.html", flights=flights, no_flight=no_flight, airlines_work_for=data4, flights_for_airlines = data5)
        
        # Search by location and dates
        elif way == 'both':
            start_date = request.form['start_date1']
            end_date = request.form['end_date1']
            depart0 = request.form['depart_city_or_airport1']
            arrive0 = request.form['arrive_city_or_airport1']
            depart = sqlsyntax(depart0)
            arrive = sqlsyntax(arrive0)

            cursor = conn.cursor()
            query1 = "SELECT airport_name FROM airport WHERE airport_city = %s"
            cursor.execute(query1, (depart))
            data1 = cursor.fetchall()


            if (data1):
                if len(data1) == 1:
                    depart_airport = [data1[0]['airport_name']]
                else:
                    depart_airport = []
                    for airport in data1:
                        depart_airport.append(airport['airport_name'])
            else:
                depart_airport = [depart]

            depart_airport_str = "('" + "','".join(depart_airport) + "')"

            query2 = "SELECT airport_name FROM airport WHERE airport_city = %s"
            cursor.execute(query2, (arrive))
            data2 = cursor.fetchall()
            if (data2):
                if len(data2) == 1:
                    arrive_airport = [data2[0]['airport_name']]
                else:
                    arrive_airport = []
                    for i in data2:
                        arrive_airport.append(i['airport_name'])
            else:
                arrive_airport = [arrive]

            arrive_airport_str = "('" + "','".join(arrive_airport) + "')"

            query3 = "SELECT * FROM flight WHERE departure_time >= %s AND arrival_time <= %s AND status = 'Upcoming' AND departure_airport IN " + depart_airport_str + " AND arrival_airport IN " + arrive_airport_str
            cursor.execute(query3, (start_date, end_date))
            flights = cursor.fetchall()
            cursor.close()
            if not (flights):
                no_flight = 1
            return render_template("booking_agent_search_purchase.html", flights=flights, no_flight=no_flight, airlines_work_for=data4, flights_for_airlines = data5)

        else:
            error = 'Please specify a way to select'
            return render_template("booking_agent_search_purchase.html", error=error)
    else:
        session.clear()
        return render_template('404.html')


@booking_agent_bp.route('/booking_agent_purchase', methods=['GET', 'POST'])
def booking_agent_purchase():
    if session.get('email') and 'customer_email' in request.form:
        email = session['email']
        airline_name = request.form.get("airline_name")
        flight_num = request.form.get("flight_number")
        customer_email = request.form['customer_email']
        conn = get_db_connection()
        cursor = conn.cursor()

        query0 = "SELECT airline_name FROM booking_agent_work_for WHERE email = %s"
        cursor.execute(query0, (email))
        data0 = cursor.fetchall()
        if (data0):
            airline = []
            for i in data0:
                airline.append(i['airline_name'])

            airline_for_agent = "('" + "','".join(airline) + "')"
            
            query4 = "SELECT flight_num FROM flight WHERE airline_name IN " + airline_for_agent
            cursor.execute(query4)
            data4 = cursor.fetchall()

        # Validate flight
        query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s"
        cursor.execute(query, (airline_name, flight_num))
        data = cursor.fetchall()
        if not (data):
            error0 = "The flight doesn't exist or it is not in upcoming status, please try again"
            return render_template ('booking_agent_search_purchase.html', error1 = error0, airlines_work_for=data0, flights_for_airlines=data4)

        # Validate booking agent
        query1 = "SELECT booking_agent_id FROM booking_agent WHERE email = %s"
        cursor.execute(query1, (email))
        data1 = cursor.fetchone()
        booking_agent = data1['booking_agent_id'] 

        # Validate customer
        query2 = "SELECT * FROM customer WHERE email = %s"
        cursor.execute(query2, (customer_email))
        data2 = cursor.fetchone()
        if not (data2):
            error1 = "The customer hasn't registered yet"
            return render_template('booking_agent_search_purchase.html', error1=error1, airlines_work_for=data0, flights_for_airlines=data4)

        # Validate Flight Date
        query5 = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND departure_time < CURDATE()"
        cursor.execute(query5, (airline_name, flight_num))
        data5 = cursor.fetchall()
        if (data5):
            error2 = "The flight is not in the upcoming status"
            return render_template('booking_agent_search_purchase.html', error2=error2, airlines_work_for=data0, flights_for_airlines=data4)

        # Set New Ticket ID
        query3 = "SELECT max(ticket_id) FROM ticket"
        cursor.execute(query3)
        data3 = cursor.fetchone()
        new_ticket_id = data3['max(ticket_id)']+1

        # Insert a new ticket
        ins1 = "INSERT INTO ticket VALUES (%s, %s, %s)"
        cursor.execute(ins1, (new_ticket_id, airline_name, flight_num))

        # Insert a new purchase
        ins2 = "INSERT INTO purchases VALUES (%s, %s, %s, CURDATE())"
        cursor.execute(ins2, (new_ticket_id, customer_email, booking_agent))
        conn.commit()
        cursor.close()
        message1 = 'Purchase Successfully!'
        return render_template('booking_agent_search_purchase.html', message = message1, airlines_work_for=data0, flights_for_airlines=data4)
    else:
        session.clear()
        return render_template('404.html')




@booking_agent_bp.route('/booking_agent_commission')
def booking_agent_commission():
    if not session.get('email'):
        session.clear()
        return render_template('404.html')

    email = session['email']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE email = %s", (email,))
        booking_agent_data = cursor.fetchone()
        booking_agent_id = booking_agent_data['booking_agent_id']
        # Calculate commission data
        cursor.execute(
            "SELECT sum(price) * 0.1 AS total_comm, avg(price) * 0.1 AS avg_comm, count(ticket_id) AS total_tickets FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE booking_agent_id = %s AND purchase_date BETWEEN DATE_ADD(NOW(), INTERVAL -30 DAY) AND NOW()",
            (booking_agent_id,))
        commission_data = cursor.fetchone()
        cursor.close()
        return render_template('booking_agent_commission.html', total_comm=commission_data['total_comm'],
                               avg_comm=commission_data['avg_comm'],
                               total_tickets=commission_data['total_tickets'])

    except Exception as e:
        return render_template('booking_agent_commission.html', error=str(e))
    finally:
        conn.close()



@booking_agent_bp.route('/booking_agent_commission_date', methods=['GET', 'POST'])
def booking_agent_commission_date():
    if session.get('email'):
        email = session['email']
        conn = get_db_connection()
        cursor = conn.cursor()


        query1 = "SELECT booking_agent_id FROM booking_agent WHERE email = %s"
        cursor.execute(query1, (email))
        data1 = cursor.fetchone()
        booking_agent = data1['booking_agent_id'] 

        query2 = "SELECT sum(price)*0.1, avg(price)*0.1, count(ticket_id) FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE booking_agent_id = %s AND purchase_date between DATE_ADD(NOW(), INTERVAL -'30' DAY) and NOW()"
        cursor.execute(query2, (booking_agent))
        data2 = cursor.fetchone()
        total_comm, avg_comm, total_tickets = data2['sum(price)*0.1'], data2['avg(price)*0.1'], data2['count(ticket_id)']

        start = request.form['start_date']
        end = request.form['end_date']
        query3 = "SELECT sum(price)*0.1, avg(price)*0.1, count(ticket_id) FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE booking_agent_id = %s AND purchase_date >= %s AND purchase_date <= %s"
        cursor.execute(query3, (booking_agent, start, end))
        data3 = cursor.fetchone()

        total_comm1, avg_comm1, total_tickets1 = data3['sum(price)*0.1'], data3['avg(price)*0.1'], data3['count(ticket_id)']
        return render_template('booking_agent_commission.html', total_comm = total_comm, avg_comm = avg_comm, total_tickets = total_tickets, comm = data3,
                                   total_comm1 = total_comm1, avg_comm1 = avg_comm1, total_tickets1 = total_tickets1, start = start, end = end)
    else:
        session.clear()
        return render_template('404.html')



@booking_agent_bp.route('/booking_agent_top_customer')
def booking_agent_top_customer():
    if not session.get('email'):
        session.clear()
        return render_template('404.html')

    email = session['email']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT booking_agent_id FROM booking_agent WHERE email = %s", (email,))
        booking_agent_data = cursor.fetchone()
        booking_agent_id = booking_agent_data['booking_agent_id']

        # Top 5 customers by ticket count
        cursor.execute(
            "SELECT customer_email AS Customer, count(ticket_id) AS Tickets FROM purchases WHERE booking_agent_id = %s AND purchase_date BETWEEN DATE_ADD(LAST_DAY(DATE_ADD(CURDATE(), INTERVAL -7 MONTH)), INTERVAL 1 DAY) AND LAST_DAY(DATE_ADD(CURDATE(), INTERVAL -1 MONTH)) GROUP BY customer_email ORDER BY Tickets DESC LIMIT 5",
            (booking_agent_id,))
        top_ticket = cursor.fetchall()

        # Top 5 customers by commission
        cursor.execute(
            "SELECT customer_email AS Customer, sum(price) * 0.1 AS Commission FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE booking_agent_id = %s AND YEAR(purchase_date) = YEAR(CURDATE()) - 1 GROUP BY customer_email ORDER BY Commission DESC LIMIT 5",
            (booking_agent_id,))
        top_commission = cursor.fetchall()

        # show a bar chart showing the top 5 customers by ticket count with 5 customers in x-axis and number of tickets in y-axis

        # show a bar chart showing the top 5 customers by commission with 5 customers in x-axis and commission in y-axis

        return render_template('booking_agent_top_customer.html', top_ticket=top_ticket,
                               top_commission=top_commission)

    except Exception as e:
        return render_template('booking_agent_top_customer.html', error=str(e))
    finally:
        cursor.close()
        conn.close()
