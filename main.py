# Flask Web Application with MySQL Integration
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql
from general import general_bp
from airline_staff import airline_staff_bp
from customer import customer_bp
from booking_agent import booking_agent_bp
import secrets


# Web App Initialization with Configured MySQL Connection
class WebApp:
    def __init__(self):
        self.flask_app = Flask(__name__)
        self.flask_app.register_blueprint(general_bp)
        self.flask_app.register_blueprint(airline_staff_bp)
        self.flask_app.register_blueprint(customer_bp)
        self.flask_app.register_blueprint(booking_agent_bp)
        secret_key = secrets.token_hex(16)
        self.flask_app.secret_key = secret_key


    def run(self):
        self.flask_app.run()

# Creating WebApp instance
web_app_instance = WebApp()
web_app_instance.run()

