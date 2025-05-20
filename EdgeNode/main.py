import paho.mqtt.client as mqtt
import sqlite3
import json
import time
import asyncio
import aiohttp
import logging
from datetime import datetime
import queue
import threading
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/mqtt_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MQTT_Service")

# Configuration
MQTT_BROKER = "100.113.20.83"  # Change to your MQTT broker address
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"  # Change to your topic
MQTT_CONTROL_TOPIC = "fan/control"  # Topic for fan control commands
MQTT_USERNAME = None  # Set if your broker requires authentication
MQTT_PASSWORD = None  # Set if your broker requires authentication

# Temperature threshold for fan control
TEMPERATURE_THRESHOLD = 30.0

# Webhook configuration
WEBHOOK_URL = "https://your-blazor-app.com/api/iot/webhook"  # Change to your Blazor webhook endpoint
WEBHOOK_API_KEY = "your-webhook-api-key"  # API key for webhook authentication
WEBHOOK_BATCH_SIZE = 10  # Number of records to send in one webhook call
WEBHOOK_INTERVAL = 30  # Seconds between webhook calls

DB_PATH = "data/sensor_data.db"

# Database setup
def setup_database():
    """Create the SQLite database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table for sensor data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        temperature REAL,
        humidity REAL,
        fan_status TEXT,
        timestamp TEXT,
        uploaded INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database setup completed")

# Database operations
def save_to_database(client_id, temperature, humidity, fan_status):
    """Save temperature, humidity, and fan status data to SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO sensor_data (client_id, temperature, humidity, fan_status, timestamp) VALUES (?, ?, ?, ?, ?)",
            (client_id, temperature, humidity, fan_status, timestamp)
        )
        
        data_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Data saved to database: ID={data_id}, Client={client_id}, Temp={temperature}, Humidity={humidity}, Fan={fan_status}")
        return data_id, timestamp
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None, None

# Fan control function
def control_fan(mqtt_client, client_id, temperature):
    """Control fan based on temperature threshold."""
    command = "ON" if temperature > TEMPERATURE_THRESHOLD else "OFF"
    
    # Create control message
    control_message = {
        "target_client_id": client_id,
        "command": command
    }
    
    # Publish control message
    try:
        mqtt_client.publish(MQTT_CONTROL_TOPIC, json.dumps(control_message))
        logger.info(f"Fan control command sent: {command} to client {client_id} (Temperature: {temperature}°C)")
        return command
    except Exception as e:
        logger.error(f"Failed to publish fan control command: {e}")
        return None

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")

def on_message(client, userdata, msg):
    """Callback when message is received from MQTT broker."""
    try:
        payload = msg.payload.decode()
        logger.info(f"Received message: {payload}")
        
        # Parse the JSON payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            # If standard JSON parsing fails, try to fix common issues
            # Like missing quotes around property names
            import re
            fixed_payload = re.sub(r'(\w+):', r'"\1":', payload)
            try:
                data = json.loads(fixed_payload)
                logger.info(f"Successfully parsed after fixing JSON format: {fixed_payload}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON even after fixing: {payload}")
                return
        
        # Extract client_id, temperature, humidity, and fan_status
        client_id = data.get('client_id', 'unknown')
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        current_fan_status = data.get('fan_status', 'OFF')  # Default to OFF if not provided
        
        if temperature is not None and humidity is not None:
            # Control fan based on temperature
            new_fan_status = control_fan(client, client_id, temperature)
            
            # If fan control was successful, use the new status, otherwise use the current status
            fan_status_to_save = new_fan_status if new_fan_status is not None else current_fan_status
            
            # Save to database
            save_to_database(client_id, temperature, humidity, fan_status_to_save)
        else:
            logger.warning("Received message missing temperature or humidity data")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Webhook sender function
def send_webhook_data():
    """Send unsent data to webhook endpoint."""
    while True:
        try:
            # Get unsent records from database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, client_id, temperature, humidity, fan_status, timestamp FROM sensor_data WHERE uploaded = 0 LIMIT ?",
                (WEBHOOK_BATCH_SIZE,)
            )
            records = cursor.fetchall()
            conn.close()
            
            if records:
                # Format data for webhook
                webhook_data = {
                    "apiKey": WEBHOOK_API_KEY,
                    "deviceId": "edge-device-001",  # Unique ID for this edge device
                    "records": [{
                        "id": record[0],
                        "clientId": record[1],
                        "temperature": record[2],
                        "humidity": record[3],
                        "fanStatus": record[4],
                        "timestamp": record[5]
                    } for record in records]
                }
                
                # Send data to webhook
                try:
                    response = requests.post( # This line was causing the error
                        WEBHOOK_URL, 
                        json=webhook_data,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response.status_code in (200, 201, 202):
                        # Mark records as uploaded
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        record_ids = [record[0] for record in records]
                        placeholders = ','.join('?' for _ in record_ids)
                        cursor.execute(f"UPDATE sensor_data SET uploaded = 1 WHERE id IN ({placeholders})", record_ids)
                        conn.commit()
                        conn.close()
                        logger.info(f"Successfully sent {len(records)} records to webhook")
                    else:
                        logger.error(f"Webhook error: {response.status_code} - {response.text}")
                        
                except requests.RequestException as e:
                    logger.error(f"Webhook request failed: {e}")
            
            # Sleep until next interval
            time.sleep(WEBHOOK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in webhook sender: {e}")
            time.sleep(WEBHOOK_INTERVAL)

def main():
    """Main function to run the MQTT client and webhook sender."""
    # Setup database
    setup_database()
    
    # Start webhook sender in a separate thread
    webhook_thread = threading.Thread(target=send_webhook_data, daemon=True)
    webhook_thread.start()
    logger.info("Started webhook sender thread")
    
    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set username and password if provided
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Connect to broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        
        # Start the MQTT loop
        client.loop_forever()
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")