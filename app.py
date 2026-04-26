# Shdan Alserhan ID#100087560
# CSCE 45203 Project
# Kindly note that I used my free late days for this submission


# This is my main application program
# Kindly see report for required testing

from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
from mysql.connector import IntegrityError
from tabulate import tabulate
import os

# Initialize Flask app, serving static files from 'static' folder
# I used this for the logo addition
app = Flask(__name__, static_folder='static')

# Open DB
# I used the sams funcs as the prev assignment
def open_database(hostname, user_name, mysql_pw, database_name):
    global conn
    conn = mysql.connector.connect(
        host=hostname,
        user=user_name,
        password=mysql_pw,
        database=database_name
    )
    global cursor
    cursor = conn.cursor()

def printFormat(result):
    header = []
    for cd in cursor.description:
        header.append(cd[0])
    print('')
    print('Query Result:')
    print('')
    print(tabulate(result, headers=header))

def executeSelect(query):
    cursor.execute(query)
    printFormat(cursor.fetchall())

def insert(table, values):
    query = "INSERT into " + table + " values (" + values + ")" + ';'
    cursor.execute(query)
    conn.commit()

def executeUpdate(query):
    cursor.execute(query)
    conn.commit()

def close_db():
    cursor.close()
    conn.close()

# This is my username and password to access MYSQL
mysql_username = 'alserhan'
mysql_password = 'keiKeep3'

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME'),
        use_pure=True,
        ssl_disabled=False,
    )

# Here, I am establishing my app routes
MENU_ROUTES = {
    '1': 'add_artist',
    '2': 'add_concert',
    '3': 'add_customer',
    '4': 'add_ticket',
    '5': 'view_concerts_by_city',
    '6': 'view_concerts_by_artist',
    '7': 'view_customer_spending',
    '8': 'view_top_artists',
    '9': 'rewards',
}

# Default homepage
@app.route('/')
def home():
    return redirect('/db_website')

# In the homepage, the user can choose how to use the database via a dropdown
# They can also simply see the dara tables as is, if they wish
@app.route('/db_website', methods=['GET', 'POST'])
def db_website():
    if request.method == 'POST':
        action = request.form.get('action')
        user_choice = request.form.get('user_choice')

        if action == 'menu_choice':
            target = MENU_ROUTES.get(user_choice)
            if target:
                return redirect(url_for(target))
            return redirect('/db_website')

        # simply display all tables of choice
        elif action == 'display_artists':
            table_name = 'ARTIST'
            query = 'SELECT * FROM ARTIST'
        elif action == 'display_concerts':
            table_name = 'CONCERT'
            query = 'SELECT * FROM CONCERT'
        elif action == 'display_customers':
            table_name = 'CUSTOMER'
            query = 'SELECT * FROM CUSTOMER'
        elif action == 'display_tickets':
            table_name = 'TICKET'
            query = 'SELECT * FROM TICKET'
        else:
            return render_template('display_table.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        cursor.close()
        conn.close()
        return render_template('display_table.html',table_name=table_name,column_names=column_names,rows=rows)
    return render_template('db_website.html')

# Add new artist to ARTIST table
@app.route('/add_artist', methods=['GET', 'POST'])
def add_artist():
    error = None
    if request.method == 'POST':
        # get the name and genre of the artist the user wants to add
        artist_name = request.form.get('name', '').strip().title()
        genre       = request.form.get('genre', '').strip().title()

        # make sure the user doesnt leave anything blank
        if not artist_name or not genre:
            error = "Name and genre are required to add an artist!"
            return render_template('add_artist.html', error=error)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # I also wanted to take case sensitivity into account which is why I used LOWER
            cursor.execute(
                "SELECT ARTIST_ID FROM ARTIST WHERE LOWER(ARTIST_NAME) = LOWER(%s)",
                (artist_name,),
            )
            # also, make sure that the artist doesnt already exist
            if cursor.fetchone():
                error = f"An artist named '{artist_name}' already exists."
                return render_template('add_artist.html', error=error)
            
            # here, I used the same approach as the prev assignment where I automatically assign the ID by adding one to the max existing ID
            cursor.execute("SELECT COALESCE(MAX(ARTIST_ID), 0) + 1 FROM ARTIST")
            artist_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO ARTIST (ARTIST_ID, ARTIST_NAME, GENRE) VALUES (%s, %s, %s)",
                (artist_id, artist_name, genre),
            )
            conn.commit()
            # check for any data integrity eror and raise error accordingly
        except IntegrityError as e:
            error = f"Could not add artist: {e.msg}"
            return render_template('add_artist.html', error=error)
        finally:
            cursor.close()
            conn.close()
        # also, to make this more user friendly, I wanted users to be able to see a success message upon successful addition
        return render_template( 'add_success.html',message=f"Artist '{artist_name}' was added successfully!",table_name='ARTIST',)
    return render_template('add_artist.html', error=error)

# Add concert to CONCERT table
# Very sismilar to add_artist above
@app.route('/add_concert', methods=['GET', 'POST'])
def add_concert():
    error = None
    if request.method == 'POST':
        # Get concert info from user
        artist_name = request.form.get('name', '').strip().title()
        venue_name  = request.form.get('venue_name', '').strip().title()
        city        = request.form.get('city', '').strip().title()
        concert_day = request.form.get('concert_day', '').strip()

        # make sure the user doesnt leave anything blank
        # I asked for artist name as that is more intuitive for an outside user to know
        if not artist_name or not venue_name or not city or not concert_day:
            error = ("Artist name, venue name, city, and day are all required to add a concert to the Concert table!")
            return render_template('add_concert.html', error=error)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # account for case sensitivity
            cursor.execute(
                "SELECT ARTIST_ID FROM ARTIST WHERE LOWER(ARTIST_NAME) = LOWER(%s)",
                (artist_name,),
            )
            result = cursor.fetchone()

            # make sure the artist exists first
            if result is None:
                error = (f"An artist named '{artist_name}' does not exist. You need to add the artist first! Please go back to the homepage or try another artist.")
                return render_template('add_concert.html', error=error)

            artist_id = result[0]

            # here, I used the same approach as the prev assignment where I automatically assign the ID by adding one to the max existing ID
            cursor.execute("SELECT COALESCE(MAX(CONCERT_ID), 0) + 1 FROM CONCERT")
            concert_id = cursor.fetchone()[0]

            cursor.execute(
                """INSERT INTO CONCERT
                   (CONCERT_ID, ARTIST_ID, VENUE_NAME, CITY, CONCERT_DAY)
                   VALUES (%s, %s, %s, %s, %s)""",
                (concert_id, artist_id, venue_name, city, concert_day),
            )
            conn.commit()
        # check for any data integrity eror and raise error accordingly
        except IntegrityError as e:
            error = f"Could not add concert: {e.msg}"
            return render_template('add_concert.html', error=error)
        finally:
            cursor.close()
            conn.close()

        # display success msg
        return render_template('add_success.html',message=f"Concert {concert_id} for '{artist_name}' at {venue_name} ({city}) on {concert_day} was added successfully!", table_name='CONCERT',)
    return render_template('add_concert.html', error=error)

# Add new customer to CUSTOMER table
@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    error = None
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip().title()

        # make sure the user doesnt leave anything blank
        if not customer_name:
            error = "Customer name is required to add a customer to the Customer table!"
            return render_template('add_customer.html', error=error)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # here, I used the same approach as the prev assignment where I automatically assign the ID by adding one to the max existing ID
            cursor.execute("SELECT COALESCE(MAX(CUSTOMER_ID), 0) + 1 FROM CUSTOMER")
            customer_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO CUSTOMER (CUSTOMER_ID, CUSTOMER_NAME) VALUES (%s, %s)",
                (customer_id, customer_name),
            )
            conn.commit()
        # same as prev funcs
        except IntegrityError as e:
            error = f"Could not add customer: {e.msg}"
            return render_template('add_customer.html', error=error)
        finally:
            cursor.close()
            conn.close()

        return render_template('add_success.html',message=f"Customer '{customer_name}' was added successfully!",table_name='CUSTOMER',)

    return render_template('add_customer.html', error=error)

# Add ticket to TICKET table
@app.route('/add_ticket', methods=['GET', 'POST'])
def add_ticket():
    error = None

    # Get concerts and customers so the form can show them as dropdowns
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.CONCERT_ID, a.ARTIST_NAME, c.VENUE_NAME, c.CITY, c.CONCERT_DAY
            FROM CONCERT c JOIN ARTIST a ON c.ARTIST_ID = a.ARTIST_ID
            ORDER BY c.CONCERT_DAY
        """)
        concerts = cursor.fetchall()

        cursor.execute(
            "SELECT CUSTOMER_ID, CUSTOMER_NAME FROM CUSTOMER ORDER BY CUSTOMER_NAME"
        )
        customers = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if request.method == 'POST':
        concert_id  = request.form.get('concert_id', '').strip()
        customer_id = request.form.get('customer_id', '').strip()
        seat_number = request.form.get('seat_number', '').strip().upper()
        price       = request.form.get('price', '').strip()

        # Make sure everything is filled in
        if not concert_id or not customer_id or not seat_number or not price:
            error = ("Concert, customer, seat number, and price are all required "
                     "to add a ticket to the Ticket table!")
            return render_template('add_ticket.html', error=error,concerts=concerts, customers=customers)

        # Validate price is a positive number
        try:
            price_value = float(price)
            if price_value <= 0:
                error = "Price must be greater than 0."
                return render_template('add_ticket.html', error=error,concerts=concerts, customers=customers)
        except ValueError:
            error = "Price must be a valid number.)."
            return render_template('add_ticket.html', error=error,concerts=concerts, customers=customers)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check whether this seat is already taken for this concert
            cursor.execute(
                """SELECT TICKET_ID FROM TICKET
                   WHERE CONCERT_ID = %s AND UPPER(SEAT_NUMBER) = UPPER(%s)""",
                (concert_id, seat_number),
            )
            if cursor.fetchone():
                error = (f"Seat '{seat_number}' is already taken for that concert. Please choose a different seat.")
                return render_template('add_ticket.html', error=error, concerts=concerts, customers=customers)

            # Compute next TICKET_ID
            cursor.execute("SELECT COALESCE(MAX(TICKET_ID), 0) + 1 FROM TICKET")
            ticket_id = cursor.fetchone()[0]

            # Insert into TICKET
            cursor.execute(
                """INSERT INTO TICKET
                   (TICKET_ID, CONCERT_ID, CUSTOMER_ID, SEAT_NUMBER, PRICE)
                   VALUES (%s, %s, %s, %s, %s)""",
                (ticket_id, concert_id, customer_id, seat_number, price_value),
            )
            conn.commit()
        
        # same as before
        except IntegrityError as e:
            error = f"Could not add ticket: {e.msg}"
            return render_template('add_ticket.html', error=error, concerts=concerts, customers=customers)
        finally:
            cursor.close()
            conn.close()
        return render_template('add_success.html',message=(f"Ticket {ticket_id} (seat {seat_number}, ${price_value:.2f}) was added successfully!"),table_name='TICKET',)
    return render_template('add_ticket.html', error=error, concerts=concerts, customers=customers)

# View all concerts or concerts by city
@app.route('/view_concerts_by_city', methods=['GET', 'POST'])
def view_concerts_by_city():
    rows = None
    column_names = None
    city = None
    searched = False

    # Get cities for the dropdown
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT CITY FROM CONCERT ORDER BY CITY")
        cities = [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

    if request.method == 'POST':
        searched = True
        city = request.form.get('city', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if city:
                cursor.execute("""
                    SELECT CONCERT_ID, ARTIST_ID, VENUE_NAME, CITY, CONCERT_DAY
                    FROM CONCERT
                    WHERE CITY = %s
                    ORDER BY CONCERT_DAY
                """, (city,))
            else:
                cursor.execute("""
                    SELECT CONCERT_ID, ARTIST_ID, VENUE_NAME, CITY, CONCERT_DAY
                    FROM CONCERT
                    ORDER BY CONCERT_DAY
                """)
            rows = cursor.fetchall()
            column_names = [d[0] for d in cursor.description]
        finally:
            cursor.close()
            conn.close()
    return render_template('view_concerts_by_city.html',cities=cities,rows=rows,column_names=column_names,city=city,searched=searched)

# View concerts by artist
@app.route('/view_concerts_by_artist', methods=['GET', 'POST'])
def view_concerts_by_artist():
    rows = None
    column_names = None
    selected_artist_id = None
    selected_artist_name = None
    searched = False

    # Get the artist list for the dropdown
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT ARTIST_ID, ARTIST_NAME FROM ARTIST ORDER BY ARTIST_NAME"
        )
        artists = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if request.method == 'POST':
        searched = True
        selected_artist_id = request.form.get('artist_id', '').strip()

        if not selected_artist_id:
            return render_template('view_concerts_by_artist.html',artists=artists,error="Please select an artist.")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT a.ARTIST_NAME, c.VENUE_NAME, c.CITY, c.CONCERT_DAY
                FROM CONCERT c JOIN ARTIST a ON c.ARTIST_ID = a.ARTIST_ID
                WHERE c.ARTIST_ID = %s
                ORDER BY c.CONCERT_DAY
            """, (selected_artist_id,))
            rows = cursor.fetchall()
            column_names = [d[0] for d in cursor.description]

            # Grab the artist name for the results 
            cursor.execute(
                "SELECT ARTIST_NAME FROM ARTIST WHERE ARTIST_ID = %s",
                (selected_artist_id,),
            )
            result = cursor.fetchone()
            selected_artist_name = result[0] if result else None
        finally:
            cursor.close()
            conn.close()

    return render_template('view_concerts_by_artist.html',artists=artists,rows=rows,column_names=column_names,selected_artist_id=selected_artist_id,selected_artist_name=selected_artist_name,searched=searched)

# View total spending per customer
@app.route('/view_customer_spending', methods=['GET', 'POST'])
def view_customer_spending():
    rows = None
    column_names = None
    selected_customer_id = None
    searched = False

    # Load customer list for dropdown
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT CUSTOMER_ID, CUSTOMER_NAME FROM CUSTOMER ORDER BY CUSTOMER_NAME"
        )
        customers = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if request.method == 'POST':
        searched = True
        selected_customer_id = request.form.get('customer_id', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if selected_customer_id:
                # Filter by specific customer
                cursor.execute("""
                    SELECT c.CUSTOMER_ID, c.CUSTOMER_NAME,
                           COALESCE(SUM(t.PRICE), 0) AS TOTAL_SPENT
                    FROM CUSTOMER c LEFT JOIN TICKET t
                         ON c.CUSTOMER_ID = t.CUSTOMER_ID
                    WHERE c.CUSTOMER_ID = %s
                    GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME
                """, (selected_customer_id,))
            else:
                # Show all customers
                cursor.execute("""
                    SELECT c.CUSTOMER_ID, c.CUSTOMER_NAME,
                           COALESCE(SUM(t.PRICE), 0) AS TOTAL_SPENT
                    FROM CUSTOMER c LEFT JOIN TICKET t
                         ON c.CUSTOMER_ID = t.CUSTOMER_ID
                    GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME
                    ORDER BY TOTAL_SPENT DESC
                """)
            rows = cursor.fetchall()
            column_names = [d[0] for d in cursor.description]
        finally:
            cursor.close()
            conn.close()
    return render_template('view_customer_spending.html', customers=customers,rows=rows,column_names=column_names,selected_customer_id=selected_customer_id,searched=searched)

# Find the top 3 artists whose concerts generated the highest total ticket revenue
@app.route('/view_top_artists')
def view_top_artists():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT a.ARTIST_NAME, SUM(t.PRICE) AS TOTAL_REVENUE
            FROM ARTIST a
            JOIN CONCERT c ON a.ARTIST_ID = c.ARTIST_ID
            JOIN TICKET  t ON c.CONCERT_ID = t.CONCERT_ID
            GROUP BY a.ARTIST_ID, a.ARTIST_NAME
            ORDER BY TOTAL_REVENUE DESC
            LIMIT 3
        """)
        rows = cursor.fetchall()
        column_names = [d[0] for d in cursor.description]
    finally:
        cursor.close()
        conn.close()

    return render_template('view_top_artists.html',rows=rows,column_names=column_names)

# This is the bonus complex function that allows for rewards
# It shows eligible customers (total spending > $500) who don't have a voucher yet, customers who already have an unredeemed voucher, or lets the user issue or redeem vouchers
@app.route('/rewards', methods=['GET', 'POST'])
def rewards():
    message = None
    error = None

    if request.method == 'POST':
        action = request.form.get('action')
        customer_id = request.form.get('customer_id')

        if action == 'issue':
            # Issue a voucher to a qualifying customer
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                # Verify customer is actually eligible and has no active voucher
                cursor.execute("""
                    SELECT c.CUSTOMER_NAME, COALESCE(SUM(t.PRICE), 0) AS total
                    FROM CUSTOMER c LEFT JOIN TICKET t
                         ON c.CUSTOMER_ID = t.CUSTOMER_ID
                    WHERE c.CUSTOMER_ID = %s
                    GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME
                """, (customer_id,))
                result = cursor.fetchone()

                if not result:
                    error = "Customer not found."
                else:
                    cust_name, total = result
                    if total <= 500:
                        error = (f"{cust_name} has only spent ${total:.2f}. Customers must spend more than $500 to qualify.")
                    else:
                        # Check for existing unredeemed voucher
                        cursor.execute("""
                            SELECT REWARD_ID FROM REWARD
                            WHERE CUSTOMER_ID = %s AND REDEEMED_TICKET_ID IS NULL
                        """, (customer_id,))
                        if cursor.fetchone():
                            error = f"{cust_name} already has an unredeemed voucher."
                        else:
                            cursor.execute("""
                                INSERT INTO REWARD
                                (CUSTOMER_ID, AMOUNT_AT_ISSUE, ISSUED_DATE)
                                VALUES (%s, %s, CURDATE())
                            """, (customer_id, total))
                            conn.commit()
                            message = (f"Reward voucher issued to {cust_name}! They can now redeem it for any concert.")
            except IntegrityError as e:
                error = f"Could not issue reward: {e.msg}"
            finally:
                cursor.close()
                conn.close()

        elif action == 'redeem':
            # Redeem voucher by creating a $0 ticket and linking it to the voucher
            reward_id  = request.form.get('reward_id')
            concert_id = request.form.get('concert_id')
            seat_number = request.form.get('seat_number', '').strip().upper()

            if not reward_id or not concert_id or not seat_number:
                error = "Reward, concert, and seat number are all required."
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    # Verify the voucher exists and is unredeemed
                    cursor.execute("""
                        SELECT CUSTOMER_ID FROM REWARD
                        WHERE REWARD_ID = %s AND REDEEMED_TICKET_ID IS NULL
                    """, (reward_id,))
                    voucher = cursor.fetchone()
                    if not voucher:
                        error = "That voucher doesn't exist or has already been redeemed."
                    else:
                        cust_id = voucher[0]

                        # Check seat isn't taken
                        cursor.execute("""
                            SELECT 1 FROM TICKET
                            WHERE CONCERT_ID = %s AND UPPER(SEAT_NUMBER) = UPPER(%s)
                        """, (concert_id, seat_number))
                        if cursor.fetchone():
                            error = f"Seat {seat_number} is already taken for that concert."
                        else:
                            # Issue "free" ticket
                            # To satisfy price check specified in the table defiinition, the price was set to  0.01 to satisfy CHECK > 0
                            cursor.execute("SELECT COALESCE(MAX(TICKET_ID), 0) + 1 FROM TICKET")
                            ticket_id = cursor.fetchone()[0]

                            cursor.execute("""
                                INSERT INTO TICKET
                                (TICKET_ID, CONCERT_ID, CUSTOMER_ID, SEAT_NUMBER, PRICE)
                                VALUES (%s, %s, %s, %s, 0.01)
                            """, (ticket_id, concert_id, cust_id, seat_number))

                            # Link the voucher to the ticket
                            cursor.execute("""
                                UPDATE REWARD
                                SET REDEEMED_TICKET_ID = %s, REDEEMED_DATE = CURDATE()
                                WHERE REWARD_ID = %s
                            """, (ticket_id, reward_id))

                            conn.commit()
                            message = (f"Voucher redeemed! Free ticket #{ticket_id} (seat {seat_number}) issued.")
                except IntegrityError as e:
                    error = f"Could not redeem voucher: {e.msg}"
                finally:
                    cursor.close()
                    conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Eligible customers (spent > $500) who don't have an unredeemed voucher yet
        cursor.execute("""
            SELECT c.CUSTOMER_ID, c.CUSTOMER_NAME, SUM(t.PRICE) AS TOTAL
            FROM CUSTOMER c
            JOIN TICKET t ON c.CUSTOMER_ID = t.CUSTOMER_ID
            WHERE c.CUSTOMER_ID NOT IN (
                SELECT CUSTOMER_ID FROM REWARD WHERE REDEEMED_TICKET_ID IS NULL
            )
            GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME
            HAVING SUM(t.PRICE) > 500
            ORDER BY TOTAL DESC
        """)
        eligible = cursor.fetchall()

        # Active (unredeemed) vouchers
        cursor.execute("""
            SELECT r.REWARD_ID, c.CUSTOMER_ID, c.CUSTOMER_NAME,
                   r.AMOUNT_AT_ISSUE, r.ISSUED_DATE
            FROM REWARD r JOIN CUSTOMER c ON r.CUSTOMER_ID = c.CUSTOMER_ID
            WHERE r.REDEEMED_TICKET_ID IS NULL
            ORDER BY r.ISSUED_DATE
        """)
        active_vouchers = cursor.fetchall()

        # Redeemed vouchers 
        cursor.execute("""
            SELECT r.REWARD_ID, c.CUSTOMER_NAME, a.ARTIST_NAME,
                   conc.VENUE_NAME, conc.CITY, conc.CONCERT_DAY,
                   t.SEAT_NUMBER, r.REDEEMED_DATE
            FROM REWARD r
            JOIN CUSTOMER c   ON r.CUSTOMER_ID = c.CUSTOMER_ID
            JOIN TICKET t     ON r.REDEEMED_TICKET_ID = t.TICKET_ID
            JOIN CONCERT conc ON t.CONCERT_ID = conc.CONCERT_ID
            JOIN ARTIST a     ON conc.ARTIST_ID = a.ARTIST_ID
            WHERE r.REDEEMED_TICKET_ID IS NOT NULL
            ORDER BY r.REDEEMED_DATE DESC
        """)
        redeemed_vouchers = cursor.fetchall()

        # Concerts dropdown for the redeem form
        cursor.execute("""
            SELECT c.CONCERT_ID, a.ARTIST_NAME, c.VENUE_NAME, c.CITY, c.CONCERT_DAY
            FROM CONCERT c JOIN ARTIST a ON c.ARTIST_ID = a.ARTIST_ID
            ORDER BY c.CONCERT_DAY
        """)
        concerts = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('rewards.html',message=message, error=error,eligible=eligible,active_vouchers=active_vouchers,redeemed_vouchers=redeemed_vouchers,concerts=concerts)

# main
def main():
    open_database('localhost', mysql_username, mysql_password, mysql_username)

if __name__ == '__main__':
    app.run(debug=True)
