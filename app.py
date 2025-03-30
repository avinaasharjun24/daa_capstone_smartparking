from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'parking_system'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM parking_slots ORDER BY id ASC")
    parking_slots = cur.fetchall()
    cur.execute("SELECT * FROM waiting_queue ORDER BY id ASC")
    waiting_queue = cur.fetchall()
    cur.close()
    return render_template('index.html', parking_slots=parking_slots, waiting_queue=waiting_queue)

@app.route('/park', methods=['POST'])
def park_vehicle():
    vehicle_number = request.form['vehicle_number'].strip()
    
    if not vehicle_number:
        flash('Vehicle number cannot be empty.', 'error')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()

    # Check for duplicates in parking_slots
    cur.execute("SELECT * FROM parking_slots WHERE vehicle_number = %s", (vehicle_number,))
    if cur.fetchone():
        flash('Vehicle number already parked.', 'error')
        cur.close()
        return redirect(url_for('index'))

    # Check for duplicates in waiting_queue
    cur.execute("SELECT * FROM waiting_queue WHERE vehicle_number = %s", (vehicle_number,))
    if cur.fetchone():
        flash('Vehicle number is already in the waiting queue.', 'error')
        cur.close()
        return redirect(url_for('index'))

    # Fetch parking_slots count
    cur.execute("SELECT COUNT(*) FROM parking_slots")
    parking_count = cur.fetchone()[0]

    if parking_count < 5:  # Assuming maximum parking slots is 5
        cur.execute("INSERT INTO parking_slots (vehicle_number) VALUES (%s)", (vehicle_number,))
        flash('Vehicle parked successfully in a parking slot!', 'success')
    else:
        cur.execute("INSERT INTO waiting_queue (vehicle_number) VALUES (%s)", (vehicle_number,))
        flash('Parking full! Vehicle added to the waiting queue.', 'info')

    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))

@app.route('/remove/<int:id>')
def remove_vehicle(id):
    cur = mysql.connection.cursor()
    
    # Fetch vehicle number from parking_slots
    cur.execute("SELECT vehicle_number FROM parking_slots WHERE id = %s", (id,))
    vehicle = cur.fetchone()

    if vehicle:
        cur.execute("DELETE FROM parking_slots WHERE id = %s", (id,))
        mysql.connection.commit()

        # Move the first waiting vehicle to the same slot
        cur.execute("SELECT vehicle_number FROM waiting_queue ORDER BY id ASC LIMIT 1")
        next_vehicle = cur.fetchone()
        
        if next_vehicle:
            next_vehicle_number = next_vehicle[0]
            cur.execute("DELETE FROM waiting_queue WHERE vehicle_number = %s", (next_vehicle_number,))
            cur.execute("INSERT INTO parking_slots (id, vehicle_number) VALUES (%s, %s) ON DUPLICATE KEY UPDATE vehicle_number = VALUES(vehicle_number)", (id, next_vehicle_number))
            flash(f'Vehicle {next_vehicle_number} moved from waiting queue to parking slot.', 'info')

    else:
        flash('Vehicle not found.', 'error')

    mysql.connection.commit()
    cur.close()
    flash('Vehicle removed successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
