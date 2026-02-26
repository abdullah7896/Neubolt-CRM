"""
GPS Worker - TCP Server for GPS Trackers
Listens on port 8000 for GPS tracker data and stores in GPS table
Refactored for new schema (GPS log)
"""
import socket
import threading
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from config import settings
from database import SessionLocal, now_karachi
from routers.vehicles import GPS

logger = logging.getLogger(__name__)

# def get_current_time_karachi() removed as we use now_karachi from database.py

def process_gps_data(conn, addr):
    """
    Process incoming GPS data from tracker
    Expected format: IMEI/EVID,LATITUDE,LONGITUDE
    Example: MAC123,31.5204,74.3587
    """
    try:
        raw_data = conn.recv(1024).decode('utf-8').strip()
        
        if not raw_data:
            return
        
        logger.debug(f"GPS data from {addr}: {raw_data}")
        
        parts = raw_data.split(',')
        
        if len(parts) >= 3:
            ev_id = parts[0]
            latitude = float(parts[1])
            longitude = float(parts[2])
            
            db = SessionLocal()
            try:
                # Assuming GPSId is generated or is MAC+Timestamp. Since GPSId is PK in schema.
                # The schema says "GPSId VARCHAR PRIMARY KEY -- Note: MAC".
                # If GPSId is just MAC, it can't track history (duplicate keys). 
                # GPSId is likely a unique ID for the LOG entry, OR the user meant "GPSId is the device ID" and there should be a composite key or auto-inc.
                # However, the schema provided:
                # CREATE TABLE "GPS" ( "GPSId" VARCHAR PRIMARY KEY, "Ev_Id" VARCHAR, "latitude" ..., "Timestamp" ... );
                # If GPSId is the PK, we need to generate a unique one for every log.
                # I will generate a UUID for GPSId.
                import uuid
                gps_id = f"GPS-{uuid.uuid4().hex[:12].upper()}"

                gps_log = GPS(
                    gps_id=gps_id, 
                    ev_id=ev_id,
                    latitude=latitude,
                    longitude=longitude,
                    gps_timestamp=now_karachi()
                )
                
                db.add(gps_log)
                db.commit()
                
                logger.info(f"GPS log saved: {ev_id} -> ({latitude}, {longitude})")
                conn.send(b"OK\n")
                
            except Exception as e:
                logger.error(f"Error saving GPS log: {str(e)}")
                db.rollback()
            finally:
                db.close()
        else:
            logger.warning(f"Invalid GPS data format: {raw_data}")
            
    except Exception as e:
        logger.error(f"Error processing GPS data: {str(e)}")
    finally:
        conn.close()

def gps_tcp_server():
    """Run GPS TCP server"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((settings.GPS_TCP_HOST, settings.GPS_TCP_PORT))
        server.listen(100)
        
        logger.info(f"GPS TCP Server listening on {settings.GPS_TCP_HOST}:{settings.GPS_TCP_PORT}")
        
        while True:
            conn, addr = server.accept()
            logger.debug(f"GPS connection from {addr}")
            
            threading.Thread(
                target=process_gps_data,
                args=(conn, addr),
                daemon=True
            ).start()
            
    except Exception as e:
        logger.error(f"GPS TCP server error: {str(e)}")

def start_gps_worker():
    """Start GPS TCP server in background thread"""
    thread = threading.Thread(target=gps_tcp_server, daemon=True)
    thread.start()
    logger.info("GPS worker started in background thread")
