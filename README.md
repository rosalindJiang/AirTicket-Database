# AirTicket-Database

Highlight the advantages:
-The user-friendly page. Style and color.
-Within each role’s transition (staff, agent, customer): left bar on the user interface for them to swiftly shift from one to another instead of going to the homepage to do so.

By grouping the templates based on the entities or entities the files in this project primarily relate to:
General:
●Main.py
○Used for running
●General.py
○General functions that do not specify user identity
●Airline_staff.py
○Specific staff-related functions
●Booking_agent.py
○Specific agent-related functions
●Customer.py
○Specific customer-related functions

Airline Staff:
●Airline_staff_login.html
○Highlight: performed the hash by MySQL’s md5 function. If putting in code, in the backend database see complicated long code, concealing the initial code only known by the users.
●Airline_staff_home.html
○To generate homepages we adopted a bit of a special design and welcoming words for the airline staff.
○Integrating all components.
○The default of upcoming flights is also shown here.
●Airline_staff_view.html
○Correspond to admin req no.1
○Allows for selection to search the flight by date range, departure/Arrival location, and either option which is dates and locations.
●Airline_staff_create_flight_change_status.html
○Correspond to admin req no.2 and 3 in the prompt. Only the operator is allowed.
○The status change is between upcoming, in progress, and delayed. 
○Note that a small suggestion that our group has for the prompt is that it is quite complex in terms of status and sometimes self-contradicting. Here the underlying assumption that we adopted and used in our testing case is delayed as those flights happened, upcoming as those in the future, and in progress, which means we are now located in the beginning beginning, and ending times of the flight. 
●Airline_staff_add_airplane_airport.html
○Corresponds to admin req no.4 and 5 in the prompt.
○As the most powerful entity, We assume the staff adds a new airplane based on relevant information, which now the website according to the prompt, only allows users with "admin" permission to perform this action.
○Add new airport is the same, only to be done with admin to prevent unauthorized users or staff from doing so. There is also the concern for adding airports into the system for the airline they work for, so we recognize the airline where the staff work upon login and enable them to do so.
●Airline_staff_view_booking_agent.html.
○Correspond to admin req no.6
○No.1. Top 5 booking agents by sales for the past month.
○No.2. Top 5 booking agents by sales for the past year.
○No.3. Top 5 booking agents by commission for the past year.
●Airline_staff_view_customer.html
○Correspond to admin req no.7
○No.1. See the most frequent customer within the last year.
○No.2. Search for a certain customer's flight.
●Airline_staff_report.html
○Correspond to admin req no.8
○Total amounts of tickets sold based on range of dates/last year/last month etc. Month-wise tickets sold in a bar chart.
●Airline_staff_revenue.html
○Correspond to admin req no.9
○pie chart for showing the total amount of revenue earned from direct sales (without using a booking agent), and indirect sales (using a booking agent).
●Airline_staff_destination.html
○Correspond to admin req no.10
○Find the top 3 most popular destinations for the last 3 months.
○Find the top 3 most popular destinations for last year.
●Airline_staff_permission.html
○Correspond to admin req no.11
○Grant new permissions to other staff in the same airline only if admin.
●airline_staff_register.html
●Airline_staff_add_booking_agent.html
○Correspond to admin req no.12 in the prompt. Only the admin is allowed to do so.
●Airline_staff_revenue.html
○pie chart for showing the total amount of revenue earned from direct sales (without using a booking agent), and indirect sales (using a booking agent).
●Our form of log out is to go to the login page.

Booking Agent:
●Booking_agent_login.html
○Login page, same function as previously mentioned
●Booking_agent_register.html 
○Login page, same function as previously mentioned
●Booking_agent_home.html
○Same as previous
●Booking_agent_view.html
○Correspond to agent req no.1
○Allows for selection to search the flight by date range, departure/Arrival location, and either option which is dates and locations.
●Booking_agent_search_purchase.html
○Correspond to agent req no.2
○Searching supported in the previous specification
○Moreover, agents can also choose a flight and purchase a ticket for this flight
●Booking_agent_commission.html 
○The default view demonstrates the booking agent’s commission in the past 30 days, total, average, and tickets sold 
○Advanced search allows for specifying begin and end dates.
●Booking_agent_top_customer.html 
○Show top 5 customers, despite our testing there is only one customer, the bar chart is successfully shown in our previous testing regardless

Customer:
●Customer_home.html
○The login page, is the same as previous
●Customer_register.html
●Customer_search_purchase.html
○Correspond to customer req no.2, 3
○Searching supported for upcoming flights based on source city/airport name, destination city/airport name, and date.
○Customers can also choose a flight and purchase a ticket for this flight
●Customer_spending.html
○Correspond to customer req no.4
○Our setting allowed tracking spending in three ways, self specificing start and end dates, and then supporting last month’s and last year’s spending checks.
○Due to time constraints, we didn’t do the bar chart in this case.
●Customer_view.html
○Correspond to customer req no.3
○The customer chooses a flight and purchases a ticket for this flight
