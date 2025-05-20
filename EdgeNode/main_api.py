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
MQTT_BROKER = "192.168.18.25"  # Change to your MQTT broker address
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"  # Change to your topic
MQTT_CONTROL_TOPIC = "fan/control"  # Topic for fan control commands
MQTT_USERNAME = None  # Set if your broker requires authentication
MQTT_PASSWORD = None  # Set if your broker requires authentication

# Temperature threshold for fan control
TEMPERATURE_THRESHOLD = 30.0

API_ENDPOINT = "https://your-cloud-api.com/data"  # Change to your API endpoint
API_KEY = "your-api-key"  # Change to your API key

DB_PATH = "data/sensor_data.db"

# Queue for API posting
# api_queue = queue.Queue()

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
        fan_status INTEGER,
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
def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")

def on_message(client, userdata, msg, properties=None):
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
            data_id, timestamp = save_to_database(client_id, temperature, humidity, fan_status_to_save)
            
            # if data_id:
            #     # Add to queue for API posting
            #     api_data = {
            #         'id': data_id,
            #         'client_id': client_id,
            #         'temperature': temperature,
            #         'humidity': humidity,
            #         'fan_status': fan_status_to_save,
            #         'timestamp': timestamp
            #     }
            #     api_queue.put(api_data)
        else:
            logger.warning("Received message missing temperature or humidity data")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")

# API posting
# async def post_to_api(session, data):
#     """Post data to cloud API."""
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {API_KEY}"
#     }
    
#     try:
#         async with session.post(API_ENDPOINT, json=data, headers=headers) as response:
#             if response.status == 200:
#                 logger.info(f"Successfully posted data to API: {data['id']}")
#                 # Mark as uploaded in database
#                 conn = sqlite3.connect(DB_PATH)
#                 cursor = conn.cursor()
#                 cursor.execute("UPDATE sensor_data SET uploaded = 1 WHERE id = ?", (data['id'],))
#                 conn.commit()
#                 conn.close()
#                 return True
#             else:
#                 logger.error(f"API error: {response.status} - {await response.text()}")
#                 return False
#     except Exception as e:
#         logger.error(f"Exception during API post: {e}")
#         return False

# async def api_worker():
#     """Worker to process the API queue."""
#     async with aiohttp.ClientSession() as session:
#         while True:
#             try:
#                 # Get data from queue with timeout
#                 try:
#                     data = api_queue.get(timeout=1)
#                 except queue.Empty:
#                     await asyncio.sleep(1)
#                     continue
                
#                 # Post to API
#                 success = await post_to_api(session, data)
                
#                 # If failed, put back in queue for retry
#                 if not success:
#                     logger.info(f"Requeueing data ID {data['id']} for retry")
#                     await asyncio.sleep(5)  # Wait before retry
#                     api_queue.put(data)
                
#                 api_queue.task_done()
                
#             except Exception as e:
#                 logger.error(f"Error in API worker: {e}")
#                 await asyncio.sleep(5)

# # Function to start the asyncio event loop for API posting
# def start_api_worker():
#     """Start the asyncio event loop for the API worker."""
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(api_worker())

def main():
    """Main function to run the MQTT client and API worker."""
    # Setup database
    setup_database()
    
    # Start API worker in a separate thread
    # api_thread = threading.Thread(target=start_api_worker, daemon=True)
    # api_thread.start()
    
    # Setup MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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