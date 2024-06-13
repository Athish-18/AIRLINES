from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

app.secret_key = "supersecretkey"

DATABASE = 'airline.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS pdata (
        custno INTEGER PRIMARY KEY,
        custname TEXT,
        addr TEXT,
        email TEXT,
        jrdate DATE,
        source TEXT,
        destination TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tkt (
        custno INTEGER,
        tkt_tot INTEGER,
        lug_tot INTEGER,
        g_tot INTEGER,
        FOREIGN KEY (custno) REFERENCES pdata (custno)
    )''')
    conn.commit()
    conn.close()

init_db()

def send_email(to_email, subject, body):
    from_email = "cathishk@gmail.com"
    password = "kyzt jgwz udpl hfjp"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    server.send_message(msg)
    server.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_customer():
    custno = request.form['custno']
    name = request.form['name']
    addr = request.form['addr']
    email = request.form['email']
    jr_date = request.form['jrdate']
    source = request.form['source']
    destination = request.form['destination']
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO pdata (custno, custname, addr, email, jrdate, source, destination) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (custno, name, addr, email, jr_date, source, destination))
        conn.commit()
        
        cursor.execute("SELECT * FROM pdata WHERE custno = ?", (custno,))
        customer_data = cursor.fetchone()
        conn.close()
        
        # Send email
        subject = "Thank you for registering with us!"
        body = f"Dear {name},\n\nThank you for registering with our airline service. Below are the details you provided:\n\n"
        body += f"Customer Number: {customer_data[0]}\n"
        body += f"Name: {customer_data[1]}\n"
        body += f"Address: {customer_data[2]}\n"
        body += f"Email: {customer_data[3]}\n"
        body += f"Date of Journey: {customer_data[4]}\n"
        body += f"Source: {customer_data[5]}\n"
        body += f"Destination: {customer_data[6]}\n\n"
        body += "Sincerely,\nThe Airline Team"
        
        send_email(email, subject, body)
        
        flash("Customer data inserted successfully and email sent.", "success")
    except sqlite3.IntegrityError as e:
        flash("Customer number already exists. Please use a different number.", "error")
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    
    return redirect(url_for('index'))

@app.route('/calculate', methods=['POST'])
def calculate_ticket_price():
    try:
        cno = int(request.form['custno_calc'])
        class_type = int(request.form['class_type'])
        num_passengers = int(request.form['passengers'])
        luggage_weight = int(request.form['luggage'])

        ticket_price = 0
        if class_type == 1:
            ticket_price = 6000 * num_passengers
        elif class_type == 2:
            ticket_price = 4000 * num_passengers
        elif class_type == 3:
            ticket_price = 2000 * num_passengers

        luggage_charge = luggage_weight * 100
        total_price = ticket_price + luggage_charge

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO tkt (custno, tkt_tot, lug_tot, g_tot) 
                          VALUES (?, ?, ?, ?)''', 
                       (cno, ticket_price, luggage_charge, total_price))
        conn.commit()
        conn.close()

        flash(f"Ticket details inserted successfully. Total Price: {total_price}", "success")
    except sqlite3.IntegrityError:
        flash("Customer number does not exist. Please register first.", "error")
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    
    return redirect(url_for('index'))

@app.route('/display_customer', methods=['POST'])
def display_customer_details():
    custno = request.form['custno_display']
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''SELECT pdata.custno, pdata.custname, pdata.addr, pdata.source, pdata.destination, 
                                 tkt.tkt_tot, tkt.lug_tot, tkt.g_tot 
                          FROM pdata 
                          INNER JOIN tkt ON pdata.custno = tkt.custno 
                          WHERE tkt.custno = ?''', (custno,))
        customer_details = cursor.fetchall()
        conn.close()
        return render_template('index.html', customer_details=customer_details)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('index'))

@app.route('/display_all')
def display_all_details():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''SELECT pdata.custno, pdata.custname, pdata.addr, pdata.source, pdata.destination, 
                                 tkt.tkt_tot, tkt.lug_tot, tkt.g_tot 
                          FROM pdata 
                          INNER JOIN tkt ON pdata.custno = tkt.custno''')
        all_details = cursor.fetchall()
        conn.close()
        return render_template('index.html', all_details=all_details)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('index'))
    
@app.route('/cancel_ticket', methods=['POST'])
def cancel_ticket():
    custno = request.form['custno_cancel']
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM tkt WHERE custno = ?''', (custno,))
        conn.commit()
        conn.close()
        flash("Ticket canceled successfully.", "success")
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
