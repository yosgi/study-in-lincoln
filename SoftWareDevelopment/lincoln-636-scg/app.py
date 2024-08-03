from flask import Flask, render_template, request, redirect, url_for
import re
from datetime import datetime, date, timedelta
import mysql.connector
from mysql.connector import FieldType
import connect

# Initialize the Flask application
app = Flask(__name__)

# Global variables for database connection and cursor
dbconn = None
connection = None

# Function to get a database cursor
def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(
        user=connect.dbuser, 
        password=connect.dbpass, 
        host=connect.dbhost, 
        database=connect.dbname, 
        autocommit=True
    )
    dbconn = connection.cursor()
    return dbconn

@app.route("/")
def home():
    # Render the welcome page
    return render_template("welcome.html")

@app.route("/listbooks")
def listbooks():
    # Fetch and display all books
    connection = getCursor()
    connection.execute("SELECT * FROM books;")
    bookList = connection.fetchall()
    return render_template("booklist.html", booklist=bookList)

@app.route("/campers", methods=['GET', 'POST'])
def campers():
    if request.method == "GET":
        # Render date picker for campers
        return render_template("datepickercamper.html", currentdate=datetime.now().date())
    else:
        # Fetch and display campers for the selected date
        campDate = request.form.get('campdate')
        cursor = getCursor()
        cursor.execute("""
            SELECT customers.customer_id, customers.firstname, customers.familyname, customers.email, customers.phone, 
                   bookings.site, bookings.booking_date, bookings.occupancy 
            FROM bookings 
            JOIN sites ON bookings.site = sites.site_id 
            INNER JOIN customers ON bookings.customer = customers.customer_id 
            WHERE bookings.booking_date = %s;
        """, (campDate,))
        camperList = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template("camperlist.html", camperlist=camperList)

@app.route("/booking", methods=['GET', 'POST'])
def booking():
    if request.method == "GET":
        # Render date picker for booking
        return render_template("datepicker.html", currentdate=datetime.now().date())
    else:
        # Process booking information
        bookingNights = request.form.get('bookingnights')
        bookingDate = request.form.get('bookingdate')
        occupancy = request.form.get('occupancy')
        firstNight = date.fromisoformat(bookingDate)
        lastNight = firstNight + timedelta(days=int(bookingNights))

        # Fetch customers and available sites
        connection = getCursor()
        connection.execute("SELECT * FROM customers;")
        customerList = connection.fetchall()
        connection.execute("""
            SELECT * FROM sites 
            WHERE occupancy >= %s 
              AND site_id NOT IN (
                SELECT site FROM bookings 
                WHERE booking_date BETWEEN %s AND %s
            );
        """, (occupancy, firstNight, lastNight))
        siteList = connection.fetchall()
        return render_template("bookingform.html", customerlist=customerList, bookingdate=bookingDate, sitelist=siteList, bookingnights=bookingNights, occupancy=occupancy)
    
@app.route("/booking/add", methods=['POST'])
def makebooking():
    # Retrieve form data
    bookingDate = request.form.get('bookingdate')
    bookingNights = request.form.get('bookingnights')
    occupancy = request.form.get('occupancy')
    customer_id = request.form.get('customer')
    site_id = request.form.get('site')

    # Validate form data
    if not bookingDate:
        return "Booking date is required", 400
    if not bookingNights:
        return "Number of booking nights is required", 400
    if not customer_id:
        return "Customer ID is required", 400
    if not site_id:
        return "Site ID is required", 400

    # Convert bookingNights to integer
    try:
        bookingNights = int(bookingNights)
    except ValueError:
        return "Invalid number of booking nights", 400

    # Convert occupancy to integer
    try:
        occupancy = int(occupancy)
    except ValueError:
        occupancy = 0

    # Convert bookingDate to date object
    try:
        firstNight = date.fromisoformat(bookingDate)
    except ValueError:
        return "Invalid booking date format", 400

    cursor = getCursor()

    try:
        # Check for each night in the booking period
        for day in range(bookingNights):
            currentNight = firstNight + timedelta(days=day)

            # Check if the customer already has a booking on the current night
            cursor.execute(
                "SELECT COUNT(*) FROM bookings WHERE customer = %s AND booking_date = %s",
                (customer_id, currentNight)
            )
            customer_booking_count = cursor.fetchone()[0]

            if customer_booking_count > 0:
                return render_template('error.html', message=f"Customer {customer_id} already has a booking on {currentNight}.")

            # Check if the site is already fully booked on the current night
            cursor.execute(
                "SELECT SUM(occupancy) FROM bookings WHERE site = %s AND booking_date = %s",
                (site_id, currentNight)
            )
            total_occupancy = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT occupancy FROM sites WHERE site_id = %s",
                (site_id,)
            )
            site_capacity = cursor.fetchone()[0]

            if total_occupancy + occupancy > site_capacity:
                return render_template('error.html', message=f"Site {site_id} cannot accommodate {occupancy} more people on {currentNight}.")

        # Insert booking for each night
        for day in range(bookingNights):
            currentNight = firstNight + timedelta(days=day)
            cursor.execute(
                "INSERT INTO bookings (site, customer, booking_date, occupancy) VALUES (%s, %s, %s, %s);",
                (site_id, customer_id, currentNight, occupancy)
            )
        connection.commit()
    except mysql.connector.Error as err:
        connection.rollback()
        return render_template('error.html', message=f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('success', message='Booking added successfully!', customer_id=customer_id))

@app.route("/searchcustomers", methods=['GET', 'POST'])
def searchcustomers():
    if request.method == "POST":
        searchQuery = request.form.get('searchquery')
        if not searchQuery:
            return render_template("searchcustomers.html")
        return redirect(url_for('searchcustomers', searchquery=searchQuery, page=1))
    
    searchQuery = request.args.get('searchquery', '')
    if not searchQuery:
        return render_template("searchcustomers.html")
    
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of results per page

    cursor = getCursor()
    searchQueryWithWildcards = f"%{searchQuery}%"
    cursor.execute(
        "SELECT customer_id, firstname, familyname, email, phone FROM customers "
        "WHERE firstname LIKE %s OR familyname LIKE %s OR email LIKE %s "
        "LIMIT %s OFFSET %s",
        (searchQueryWithWildcards, searchQueryWithWildcards, searchQueryWithWildcards, per_page, (page - 1) * per_page)
    )
    customerList = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM customers WHERE firstname LIKE %s OR familyname LIKE %s OR email LIKE %s",
        (searchQueryWithWildcards, searchQueryWithWildcards, searchQueryWithWildcards)
    )
    total = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template("customerlist.html", customerlist=customerList, page=page, per_page=per_page, total=total, searchquery=searchQuery)

@app.route("/addcustomer", methods=['GET', 'POST'])
def addcustomer():
    if request.method == "GET":
        return render_template("add_or_edit_customer.html", action='addcustomer', customer=None)
    else:
        # Retrieve form data
        firstname = request.form.get('firstname')
        familyname = request.form.get('familyname')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Validate form data
        if not firstname or not familyname or not email or not phone:
            return render_template('error.html', message="All fields are required"), 400

        try:
            cursor = getCursor()
            # Insert new customer into database
            cursor.execute(
                "INSERT INTO customers (firstname, familyname, email, phone) VALUES (%s, %s, %s, %s);",
                (firstname, familyname, email, phone)
            )
            connection.commit()
            customer_id = cursor.lastrowid
        except mysql.connector.Error as err:
            connection.rollback()
            return render_template('error.html', message=f"Error: {err}"), 500
        except Exception as e:
            return render_template('error.html', message=f"Unexpected error: {e}"), 500
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception as e:
                return render_template('error.html', message=f"Error closing cursor or connection: {e}"), 500

        return redirect(url_for('success', message='Customer added successfully!', customer_id=customer_id))

@app.route("/editcustomer/<int:customer_id>", methods=['GET', 'POST'])
def editcustomer(customer_id):
    if request.method == "GET":
        cursor = getCursor()
        cursor.execute("SELECT customer_id, firstname, familyname, email, phone FROM customers WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        connection.close()

        if customer is None:
            return render_template('error.html', message="Customer not found"), 404

        customer = {
            'customer_id': customer[0],
            'firstname': customer[1],
            'familyname': customer[2],
            'email': customer[3],
            'phone': customer[4]
        }

        return render_template("add_or_edit_customer.html", action='editcustomer', customer=customer)
    else:
        # Retrieve form data
        firstname = request.form.get('firstname')
        familyname = request.form.get('familyname')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Validate form data
        if not firstname or not familyname or not email or not phone:
            return render_template('error.html', message="All fields are required"), 400

        try:
            cursor = getCursor()
            # Update customer information in database
            cursor.execute(
                "UPDATE customers SET firstname = %s, familyname = %s, email = %s, phone = %s WHERE customer_id = %s",
                (firstname, familyname, email, phone, customer_id)
            )
            connection.commit()
        except mysql.connector.Error as err:
            connection.rollback()
            return render_template('error.html', message=f"Error: {err}"), 500
        except Exception as e:
            return render_template('error.html', message=f"Unexpected error: {e}"), 500
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception as e:
                return render_template('error.html', message=f"Error closing cursor or connection: {e}"), 500

        return redirect(url_for('success', message='Customer updated successfully!', customer_id=customer_id))

@app.route("/success")
def success():
    # Display success message
    message = request.args.get('message', 'Operation completed successfully!')
    customer_id = request.args.get('customer_id')
    return render_template("success.html", message=message, customer_id=customer_id)

@app.route("/error")
def error():
    # Display error message
    message = request.args.get('message', 'An error occurred!')
    return render_template("error.html", message=message)

@app.route("/customer_report/<int:customer_id>")
def customer_report(customer_id):
    cursor = getCursor()

    # get customer information
    cursor.execute("SELECT firstname, familyname, email, phone FROM customers WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    
    if customer is None:
        cursor.close()
        connection.close()
        return render_template('error.html', message="Customer not found"), 404

    # calculate total nights
    cursor.execute("""
        SELECT COUNT(*) AS total_nights 
        FROM bookings 
        WHERE customer = %s
    """, (customer_id,))
    total_nights = cursor.fetchone()[0] or 0

    # calculate average occupancy
    cursor.execute("""
        SELECT SUM(occupancy) AS total_occupancy 
        FROM bookings 
        WHERE customer = %s
    """, (customer_id,))
    total_occupancy = cursor.fetchone()[0] or 0

    average_occupancy = total_occupancy / total_nights if total_nights > 0 else 0

    cursor.close()
    connection.close()

    return render_template(
        "customer_report.html",
        customer={
            'firstname': customer[0],
            'familyname': customer[1],
            'email': customer[2],
            'phone': customer[3]
        },
        total_nights=total_nights,
        average_occupancy=average_occupancy
    )
   
    pass