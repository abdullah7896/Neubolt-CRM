"""
MQTT Worker - Handles MQTT connectivity and data processing
Fetches telemetry data from MQTT broker and stores in database
Refactored for new schema (EV_Data, BSS_DATA)
"""
import paho.mqtt.client as mqtt
import json
import logging
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from config import settings
from database import SessionLocal, now_karachi
from routers.vehicles import EV_Data, EV
from routers.stations import BSS_Data, BSS

logger = logging.getLogger(__name__)

# MQTT Client instance
mqtt_client = None

# def get_current_time_karachi() removed as we use now_karachi from database.py

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe("neubolt/ev/+/telemetry")
        client.subscribe("neubolt/station/+/telemetry")
        logger.info("Subscribed to MQTT topics")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    """Callback when message received from MQTT broker"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode('utf-8'))
        
        if "/ev/" in topic:
            process_ev_telemetry(payload)
        elif "/station/" in topic:
            process_station_telemetry(payload)
        
    except Exception as e:
        logger.error(f"Error processing MQTT message: {str(e)}")

def process_ev_telemetry(data: dict):
    """
    Process EV telemetry data and store in flattened EV_Data table
    """
    db = SessionLocal()
    try:
        # Parse time
        telemetry_time = now_karachi()
        if isinstance(data.get('time'), str):
            try:
                telemetry_time = datetime.fromisoformat(data['time'])
            except:
                pass
        
        ev_id = data.get('ev_id')
        
        # 1. Store Vehicle-level telemetry (Flattened)
        ev_telemetry = EV_Data(
            ev_id=ev_id,
            log_time=telemetry_time,
            ev_voltage=data.get('ev_voltage'),
            ev_current=data.get('ev_current'),
            ev_mcu_rpm=data.get('ev_mcu_rpm'),
            distance=data.get('distance'),
            e_mcu_tempflag=data.get('ev_mcu_tempflag')
        )
        
        # 2. Map Battery-level telemetry (Slots) to flattened columns
        batteries = data.get('batteries', [])
        for battery in batteries:
            slot_idx = battery.get('slot')
            if slot_idx in [1, 2, 3]:
                prefix = f"s{slot_idx}_"
                setattr(ev_telemetry, f"{prefix}battery_id", battery.get('id'))
                setattr(ev_telemetry, f"{prefix}temp", battery.get('temp'))
                setattr(ev_telemetry, f"{prefix}soc", battery.get('soc'))
                setattr(ev_telemetry, f"{prefix}soh", battery.get('soh'))
                setattr(ev_telemetry, f"{prefix}vol", battery.get('voltage'))
                setattr(ev_telemetry, f"{prefix}curr", battery.get('current'))
        
        db.add(ev_telemetry)
        
        db.commit()
        logger.debug(f"EV telemetry saved: {ev_id}")
        
    except Exception as e:
        logger.error(f"Error saving EV telemetry: {str(e)}")
        db.rollback()
    finally:
        db.close()

def process_station_telemetry(data: dict):
    """
    Process station telemetry data and store in flattened BSS_Data table
    """
    db = SessionLocal()
    try:
        log_time = now_karachi()
        if isinstance(data.get('datetime'), str):
            try:
                log_time = datetime.fromisoformat(data['datetime'])
            except:
                pass
        
        bss_id = data.get('station_id')
        bss_data = BSS_Data(
            bss_id=bss_id,
            log_time=log_time
        )
        
        # Process all slots (Map to flattened columns s1, s2, s3)
        slots = data.get('slots', [])
        for slot in slots:
            slot_idx = slot.get('slot')
            if slot_idx in [1, 2, 3]:
                prefix = f"s{slot_idx}_"
                setattr(bss_data, f"{prefix}battery_id", slot.get('battery_id'))
                setattr(bss_data, f"{prefix}temp", slot.get('temp'))
                setattr(bss_data, f"{prefix}soc", slot.get('soc'))
                setattr(bss_data, f"{prefix}soh", slot.get('soh'))
                setattr(bss_data, f"{prefix}vol", slot.get('voltage'))
                setattr(bss_data, f"{prefix}curr", slot.get('current'))
                setattr(bss_data, f"{prefix}cycle_cnt", slot.get('cycle_count'))
                setattr(bss_data, f"{prefix}rem_cap", slot.get('remaining_capacity'))
                setattr(bss_data, f"{prefix}full_cap", slot.get('full_capacity'))
                setattr(bss_data, f"{prefix}chr_vol", slot.get('charge_voltage'))
                setattr(bss_data, f"{prefix}chr_curr", slot.get('charge_current'))
                setattr(bss_data, f"{prefix}status", slot.get('charge_status', ''))
                setattr(bss_data, f"{prefix}b_errorflags", slot.get('battery_error_flags', ''))
                setattr(bss_data, f"{prefix}c_errorflags", slot.get('charger_error_flags', ''))

        db.add(bss_data)
        
        db.commit()
        logger.debug(f"Station telemetry saved: {bss_id}")
        
    except Exception as e:
        logger.error(f"Error saving station telemetry: {str(e)}")
        db.rollback()
    finally:
        db.close()

def start_mqtt_worker():
    """Initialize and start MQTT client in background thread"""
    global mqtt_client
    
    def mqtt_thread():
        global mqtt_client
        try:
            mqtt_client = mqtt.Client()
            mqtt_client.on_connect = on_connect
            mqtt_client.on_message = on_message
            
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            
            mqtt_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            mqtt_client.loop_forever()
            
        except Exception as e:
            logger.error(f"MQTT worker error: {str(e)}")
    
    thread = threading.Thread(target=mqtt_thread, daemon=True)
    thread.start()
    logger.info("MQTT worker started in background thread")
