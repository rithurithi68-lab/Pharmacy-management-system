from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
print("MySQL connector work aagudhu")
from twilio.rest import Client
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests
import uuid

load_dotenv()
# --- SMS & Voice Credentials ---
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_FROM_NUMBER")
FAST2SMS_KEY = os.getenv("FAST2SMS_API_KEY")

# Initialize Twilio client
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
CORS(app)

# MySQL Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'varsh10'),
    'database': os.getenv('DB_NAME', 'pharmacy_db'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def init_database():
    """Initialize database with tables and sample data"""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = connection.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            manufacturer VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            current_stock INT NOT NULL DEFAULT 0,
            min_stock_level INT NOT NULL DEFAULT 10,
            price_per_unit DECIMAL(10,2) NOT NULL,
            expiry_date DATE NOT NULL,
            batch_number VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20) NOT NULL UNIQUE,
            email VARCHAR(255),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id VARCHAR(36) PRIMARY KEY,
            customer_id VARCHAR(36) NOT NULL,
            medicine_id VARCHAR(36) NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) DEFAULT 'completed',
            sms_notification_sent BOOLEAN DEFAULT FALSE,
            voice_call_scheduled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id VARCHAR(36) PRIMARY KEY,
            customer_id VARCHAR(36) NOT NULL,
            medicine_id VARCHAR(36),
            type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
        """)
        
        # Insert sample data
        sample_medicines = [
            (str(uuid.uuid4()), 'Paracetamol 500mg', 'PharmaCorp', 'Pain Relief', 25, 20, 5.50, '2025-12-15', 'PAR2024001', 'Common pain reliever and fever reducer'),
            (str(uuid.uuid4()), 'Amoxicillin 250mg', 'MediPharma', 'Antibiotic', 15, 10, 12.75, '2025-08-30', 'AMX2024002', 'Broad-spectrum antibiotic for bacterial infections'),
            (str(uuid.uuid4()), 'Ibuprofen 400mg', 'HealthPlus', 'Anti-inflammatory', 8, 15, 8.25, '2025-11-20', 'IBU2024003', 'Anti-inflammatory medication for pain and swelling')
        ]
        
        sample_customers = [
            (str(uuid.uuid4()), 'John Smith', '+1234567890', 'john@email.com', '123 Main St'),
            (str(uuid.uuid4()), 'Sarah Johnson', '+1234567891', 'sarah@email.com', '456 Oak Ave'),
            (str(uuid.uuid4()), 'Mike Davis', '+1234567892', 'mike@email.com', '789 Pine Rd')
        ]
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM medicines")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO medicines (id, name, manufacturer, category, current_stock, min_stock_level, 
                                     price_per_unit, expiry_date, batch_number, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_medicines)
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO customers (id, name, phone, email, address)
                VALUES (%s, %s, %s, %s, %s)
            """, sample_customers)
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Database initialized successfully!")
        return True
        
    except mysql.connector.Error as err:
        print(f"Error initializing database: {err}")
        return False
# --- SMS and Voice Notification Functions ---
def send_sms(phone, message):
    """Send SMS via Fast2SMS"""
    import requests

    FAST2SMS_KEY = "yAxUGXFb8hgHaCSnzukN1wQZ37JIPRTmj2WBiKOYovEVs4q6eLr6DjtvUhQBidAZl97GYux1yMRsFwIS"

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "sender_id": "TXTIND",
        "message": message,
        "language": "english",
        "route": "v3",
        "numbers": phone
    }
    headers = {
        "authorization": FAST2SMS_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        r = requests.post(url, data=payload, headers=headers)
        print("✅ SMS sent:", r.text)
    except Exception as e:
        print("❌ SMS Error:", e)


def send_voice_call(phone, message):
    """Send automated voice call via Twilio"""
    try:
        call = twilio_client.calls.create(
            twiml=f'<Response><Say voice="alice">Your medicine paracetamal will expiry soon,So be alert and use it. </Say></Response>',
            to="+919677855260",  # assuming Indian numbers
            from_="+14342048371"
        )
        print(f"📞 Voice Call Sent: {call.sid}")
    except Exception as e:
        print("❌ VoiceError:",e)
# Routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/inventory')
def inventory():
    return render_template("inventory.html")

@app.route('/billing')
def billing():
    return render_template("billing.html")

@app.route('/customers')
def customers():
    return render_template("customers.html")

@app.route('/notifications')
def notifications():
    return render_template("notifications.html")

@app.route('/reports')
def reports():
    return render_template("reports.html")

@app.route('/api/dashboard/stats')
def dashboard_stats():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get total medicines
        cursor.execute("SELECT COUNT(*) as count FROM medicines")
        total_medicines = cursor.fetchone()['count']
        
        # Get low stock items
        cursor.execute("SELECT COUNT(*) as count FROM medicines WHERE current_stock <= min_stock_level")
        low_stock_items = cursor.fetchone()['count']
        
        # Get total customers
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        total_customers = cursor.fetchone()['count']
        
        # Get today's sales
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM transactions 
            WHERE DATE(created_at) = CURDATE()
        """)
        todays_sales = float(cursor.fetchone()['total'])
        
        return jsonify({
            "totalMedicines": total_medicines,
            "lowStockItems": low_stock_items,
            "totalCustomers": total_customers,
            "todaysSales": todays_sales
        })
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/medicines')
def get_medicines():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM medicines ORDER BY created_at DESC")
        medicines = cursor.fetchall()
        
        # Convert Decimal to float and date to string
        for medicine in medicines:
            medicine['price_per_unit'] = str(medicine['price_per_unit'])
            medicine['expiry_date'] = medicine['expiry_date'].isoformat()
            if medicine['created_at']:
                medicine['created_at'] = medicine['created_at'].isoformat()
        
        return jsonify(medicines)
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    data = request.json
    
    try:
        medicine_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO medicines (id, name, manufacturer, category, current_stock, min_stock_level,
                                 price_per_unit, expiry_date, batch_number, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            medicine_id,
            data['name'],
            data['manufacturer'],
            data['category'],
            data['currentStock'],
            data['minStockLevel'],
            data['pricePerUnit'],
            data['expiryDate'],
            data['batchNumber'],
            data.get('description', '')
        ))
        
        connection.commit()
        
        # Return the created medicine
        cursor.execute("SELECT * FROM medicines WHERE id = %s", (medicine_id,))
        medicine = cursor.fetchone()
        medicine['price_per_unit'] = str(medicine['price_per_unit'])
        medicine['expiry_date'] = medicine['expiry_date'].isoformat()
        medicine['created_at'] = medicine['created_at'].isoformat()
        
        return jsonify(medicine), 201
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/customers')
def get_customers():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
        customers = cursor.fetchall()
        
        for customer in customers:
            if customer['created_at']:
                customer['created_at'] = customer['created_at'].isoformat()
        
        return jsonify(customers)
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/customers', methods=['POST'])
def add_customer():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    data = request.json
    
    try:
        customer_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO customers (id, name, phone, email, address)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            customer_id,
            data['name'],
            data['phone'],
            data.get('email'),
            data.get('address')
        ))
        
        connection.commit()
        
        # Return the created customer
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        customer['created_at'] = customer['created_at'].isoformat()
        
        return jsonify(customer), 201
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/transactions')
def get_transactions():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT t.*, c.name as customer_name, m.name as medicine_name
            FROM transactions t
            JOIN customers c ON t.customer_id = c.id
            JOIN medicines m ON t.medicine_id = m.id
            ORDER BY t.created_at DESC
        """)
        transactions = cursor.fetchall()
        
        for transaction in transactions:
            transaction['unit_price'] = str(transaction['unit_price'])
            transaction['total_amount'] = str(transaction['total_amount'])
            if transaction['created_at']:
                transaction['created_at'] = transaction['created_at'].isoformat()
        
        return jsonify(transactions)
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)
    data = request.get_json()

    try:
        customer_name = data.get('customer_name')
        phone = data.get('phone')
        medicine_name = data.get('medicine_name')
        quantity = int(data.get('quantity', 0))
        unit_price = float(data.get('unit_price', 0))
        total_amount = float(data.get('total', 0))

        # Get or create customer
        cursor.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
        customer = cursor.fetchone()
        if customer:
            customer_id = customer['id']
        else:
            customer_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO customers (id, name, phone) VALUES (%s, %s, %s)",
                (customer_id, customer_name, phone)
            )

        # Get medicine ID
        cursor.execute("SELECT id, expiry_date FROM medicines WHERE name = %s", (medicine_name,))
        medicine = cursor.fetchone()
        if not medicine:
            return jsonify({"error": "Medicine not found"}), 404

        medicine_id = medicine['id']
        expiry_date = medicine['expiry_date']

        # Create transaction record
        transaction_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO transactions (id, customer_id, medicine_id, quantity, unit_price, total_amount, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            transaction_id,
            customer_id,
            medicine_id,
            quantity,
            unit_price,
            total_amount,
            'completed'
        ))

        # Reduce stock
        cursor.execute(
            "UPDATE medicines SET current_stock = current_stock - %s WHERE id = %s",
            (quantity, medicine_id)
        )

        connection.commit()

        # ✅ Send SMS + Voice Call Notification
        sms_msg = f"Hello {customer_name}, you purchased {medicine_name} for ₹{total_amount}. It expires on {expiry_date}. Thank you!"
        call_msg = f"Hello {customer_name}, reminder: your medicine {medicine_name} will expire on {expiry_date}. Please check and renew it if necessary."

        send_sms(phone, sms_msg)
        send_voice_call(phone, call_msg)

        print(f"✅ Transaction completed & notification sent to {customer_name}")
        return jsonify({"status": "success", "message": "Transaction saved and notification sent."}), 200

    except Exception as e:
        print("❌ Error saving billing:", e)
        connection.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/api/notifications')
def get_notifications():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT n.*, c.name as customer_name, m.name as medicine_name
            FROM notifications n
            JOIN customers c ON n.customer_id = c.id
            LEFT JOIN medicines m ON n.medicine_id = m.id
            ORDER BY n.created_at DESC
        """)
        notifications = cursor.fetchall()
        
        for notification in notifications:
            if notification['created_at']:
                notification['created_at'] = notification['created_at'].isoformat()
            if notification['scheduled_at']:
                notification['scheduled_at'] = notification['scheduled_at'].isoformat()
            if notification['sent_at']:
                notification['sent_at'] = notification['sent_at'].isoformat()
        
        return jsonify(notifications)
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()       
if __name__== '__main__':
    send_sms("919677855260", "Medicine Expiry Alert: Your Paracetamol 500mg stock is expiring soon.")
    print("Initializing database...")
    if init_database():
        print("Starting Flask application...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("Failed to initialize database. Please check your MySQL configuration.")