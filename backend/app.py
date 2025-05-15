from flask import Flask, request, jsonify
from flask_cors import CORS
from database_utils import execute_query
import datetime
import json # Import the json module

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes, allowing your frontend to connect

# --- Helper function to get current timestamp ---
def get_current_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# --- API Endpoints ---

@app.route('/api/waste-sourcing', methods=['POST'])
def handle_waste_sourcing():
    data = request.get_json()
    print(f"Received data for waste sourcing: {data}")

    # Extract data from the request
    collection_date = data.get('collectionDate')
    collection_time = data.get('collectionTime')
    source_type = data.get('sourceType')
    source_name = data.get('sourceName')
    waste_type = data.get('wasteType')
    waste_weight = data.get('wasteWeight') # Corresponds to waste_weight DECIMAL(10,2)
    segregation_status = data.get('segregationStatus')
    collection_personnel = data.get('collectionPersonnel')
    contaminants_found = data.get('contaminantsFound') # Expecting a list for JSON type
    collection_notes = data.get('collectionNotes')

    # --- Basic Validation (you should enhance this) ---
    required_fields = [
        'collectionDate', 'collectionTime', 'sourceType', 'sourceName',
        'wasteType', 'wasteWeight', 'segregationStatus', 'collectionPersonnel'
    ]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Validate waste_weight
    try:
        float(waste_weight) # Check if it's a valid number for DECIMAL
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid waste weight. Must be a number."}), 400
        
    # contaminants_found is expected to be a list from the frontend for the JSON DB field.
    # No string conversion needed if the database connector handles list-to-JSON.
    # If it's not a list (e.g., single select or bad data), ensure it's None or an empty list.
    if not isinstance(contaminants_found, list) and contaminants_found is not None:
        # Decide handling: either make it a list or reject
        # For now, if it's a single item, wrap it in a list. If it's something else, set to None.
        if isinstance(contaminants_found, (str, int, float)):
             contaminants_found = [contaminants_found]
        else:
             contaminants_found = None # Or [] if your DB expects an empty list for empty JSON array
    elif contaminants_found is None:
        contaminants_found = None # Or []

    # Convert contaminants_found list to JSON string for DB storage
    contaminants_json_string = None
    if contaminants_found is not None:
        # Ensure it's a list before dumping (it should be by this point from above logic)
        if isinstance(contaminants_found, list):
            contaminants_json_string = json.dumps(contaminants_found)
        else: # Fallback if somehow it's still not a list (e.g. if above logic changes)
            contaminants_json_string = json.dumps([str(contaminants_found)]) # or handle error
    # If contaminants_found was None initially, contaminants_json_string remains None, which is fine for nullable JSON column

    # --- Database Interaction ---
    # Table name is now 'waste_sources'
    # Column name is now 'waste_weight'
    # 'contaminants_found' will be passed as a list (mysql-connector handles JSON conversion)
    # 'created_at' and 'updated_at' are handled by DB defaults.
    query = ("""
        INSERT INTO waste_sources (
            collection_date, collection_time, source_type, source_name, 
            waste_type, waste_weight, segregation_status, collection_personnel, 
            contaminants_found, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """)
    params = (
        collection_date, collection_time, source_type, source_name, 
        waste_type, waste_weight, segregation_status, collection_personnel, 
        contaminants_json_string, # Pass the JSON string
        collection_notes
    )

    try:
        last_id = execute_query(query, params=params, is_insert=True)
        if last_id:
            return jsonify({"message": "Waste sourcing data recorded successfully", "id": last_id}), 201
        else:
            # This else block might be hit if execute_query returns None due to an caught exception within it.
            return jsonify({"error": "Failed to record waste sourcing data. Database operation failed. Check server logs."}), 500
    except Exception as e:
        print(f"Error in /api/waste-sourcing: {e}")
        # Be careful about exposing raw error messages if they contain sensitive info
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

@app.route('/api/storage-records', methods=['POST'])
def handle_storage_records():
    data = request.get_json()
    print(f"Received data for storage records: {data}")

    # Extract data from the request
    storage_date = data.get('storageDate')
    storage_method = data.get('storageMethod')
    storage_conditions = data.get('storageConditions')
    storage_duration = data.get('storageDuration')
    planned_utilization = data.get('plannedUtilization')
    person_responsible = data.get('personResponsible')
    storage_observations = data.get('storageObservations')

    # --- Basic Validation (enhance as needed) ---
    required_fields = [
        'storageDate', 'storageMethod', 'storageConditions',
        'storageDuration', 'plannedUtilization', 'personResponsible'
    ]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    try:
        storage_duration_int = int(storage_duration) # This is correct as per your DDL (storage_duration INT)
        if storage_duration_int < 0:
            return jsonify({"error": "Storage duration must be a non-negative number."}), 400
    except ValueError:
        return jsonify({"error": "Invalid storage duration. Must be a number."}), 400

    # --- Database Interaction ---
    # Table name is now 'waste_storage'
    # Column name is 'storage_duration' (not _days)
    # 'created_at' and 'updated_at' are handled by DB defaults.
    query = ("""
        INSERT INTO waste_storage (
            storage_date, storage_method, storage_conditions, storage_duration, 
            planned_utilization, person_responsible, observations
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """)
    params = (
        storage_date, storage_method, storage_conditions, storage_duration_int, 
        planned_utilization, person_responsible, storage_observations
        # get_current_timestamp() removed as created_at is default
    )

    try:
        last_id = execute_query(query, params=params, is_insert=True)
        if last_id:
            return jsonify({"message": "Storage record data recorded successfully", "id": last_id}), 201
        else:
            return jsonify({"error": "Failed to record storage data. Check server logs."}), 500
    except Exception as e:
        print(f"Error in /api/storage-records: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

@app.route('/api/processing-records', methods=['POST'])
def handle_processing_records():
    data = request.get_json()
    print(f"Received data for processing records: {data}")

    # Extract data
    processing_date = data.get('processingDate')
    processing_type = data.get('processingType')
    processing_method = data.get('processingMethod')
    waste_processed = data.get('wasteProcessed')
    by_products = data.get('byProducts')
    waste_reduction = data.get('wasteReduction')
    processing_remarks = data.get('processingRemarks') # Changed from 'remarks' to match HTML name

    # Validation
    required_fields = [
        'processingDate', 'processingType', 'processingMethod', 'wasteProcessed'
    ]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        float(waste_processed) # Validate waste_processed
        if waste_reduction is not None and waste_reduction != '':
            waste_reduction_float = float(waste_reduction)
            if not (0 <= waste_reduction_float <= 100):
                return jsonify({"error": "Waste reduction must be between 0 and 100."}), 400
        else:
            waste_reduction = None # Ensure it's None if empty, for DB
    except ValueError:
        return jsonify({"error": "Invalid number for waste processed or waste reduction."}), 400

    # DB Interaction for waste_processing table
    query = ("""
        INSERT INTO waste_processing (
            processing_date, processing_type, processing_method, waste_processed, 
            by_products, waste_reduction, remarks 
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """)
    # 'storage_id' FK is not handled here as it's not in the form
    params = (
        processing_date, processing_type, processing_method, waste_processed,
        by_products, waste_reduction, processing_remarks
    )

    try:
        last_id = execute_query(query, params=params, is_insert=True)
        if last_id:
            return jsonify({"message": "Processing record data recorded successfully", "id": last_id}), 201
        else:
            return jsonify({"error": "Failed to record processing data. Check server logs."}), 500
    except Exception as e:
        print(f"Error in /api/processing-records: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

@app.route('/api/environmental-monitoring', methods=['POST'])
def handle_environmental_monitoring():
    data = request.get_json()
    print(f"Received data for environmental monitoring: {data}")

    # Extract data
    monitoring_date = data.get('monitoringDate')
    monitoring_time = data.get('monitoringTime')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    odor_level = data.get('odorLevel')
    pest_presence = data.get('pestPresence')
    pest_details = data.get('pestDetails')
    mitigation_actions = data.get('mitigationActions')
    monitoring_remarks = data.get('monitoringRemarks') # Changed from 'remarks' to match HTML name

    # Validation
    required_fields = [
        'monitoringDate', 'monitoringTime', 'temperature', 'humidity', 'odorLevel', 'pestPresence'
    ]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        float(temperature)
        hum_float = float(humidity)
        if not (0 <= hum_float <= 100):
            return jsonify({"error": "Humidity must be between 0 and 100."}), 400
    except ValueError:
        return jsonify({"error": "Invalid temperature or humidity. Must be numbers."}), 400
        
    if pest_presence == 'no': # If no pests, ensure details are null or empty for DB
        pest_details = None
    elif pest_presence == 'yes' and not pest_details:
        return jsonify({"error": "Pest details are required if pest presence is 'yes'."}), 400

    # DB Interaction for environmental_monitoring table
    query = ("""
        INSERT INTO environmental_monitoring (
            monitoring_date, monitoring_time, temperature, humidity, odor_level, 
            pest_presence, pest_details, mitigation_actions, remarks
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """)
    # 'processing_id' FK is not handled here as it's not in the form
    params = (
        monitoring_date, monitoring_time, temperature, humidity, odor_level,
        pest_presence, pest_details, mitigation_actions, monitoring_remarks
    )

    try:
        last_id = execute_query(query, params=params, is_insert=True)
        if last_id:
            return jsonify({"message": "Environmental monitoring data recorded successfully", "id": last_id}), 201
        else:
            return jsonify({"error": "Failed to record environmental monitoring data. Check server logs."}), 500
    except Exception as e:
        print(f"Error in /api/environmental-monitoring: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# You will add more @app.route definitions here for other forms:
# - /api/storage-records
# - /api/processing-records
# - /api/environmental-monitoring

# --- Main execution ---
if __name__ == '__main__':
    # Before running, ensure your MySQL database is running and the
    # `bsf_farm_db` database (or your chosen name in config.py) exists.
    # Also, create the necessary tables (e.g., `waste_sourcing`).
    print("Starting Flask server...")
    print("Make sure your MySQL server is running and configured in config.py")
    print("Ensure the database and required tables are created.")
    app.run(debug=True, port=5000) # Runs on http://127.0.0.1:5000/ 