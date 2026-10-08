from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from difflib import SequenceMatcher
from datetime import datetime
import os
import re


app = Flask(__name__)


MONGODB_URI = os.environ.get("MONGODB_URI")

if not MONGODB_URI:
    print("WARNING: MONGODB_URI environment variable is not set.")

# MongoDB variables
client = None
db = None
records_collection = None

def connect_database():
    global client
    global db
    global records_collection

    if not MONGODB_URI:
        return False

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )

       
        client.admin.command("ping")

        db = client["data_redundancy_database"]

        records_collection = db["records"]

        
        records_collection.create_index(
            "email",
            unique=True
        )

    
        records_collection.create_index(
            "phone",
            unique=True,
            partialFilterExpression={
                "phone": {
                    "$exists": True,
                    "$ne": ""
                }
            }
        )

        print("MongoDB Atlas connected successfully.")

        return True

    except Exception as error:

        print("MongoDB connection failed:")
        print(error)

        return False



def normalize_text(value):

    if value is None:
        return ""

    value = str(value).strip().lower()

    # Remove unnecessary spaces
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_email(email):

    if email is None:
        return ""

    return str(email).strip().lower()


def normalize_phone(phone):

    if phone is None:
        return ""

    # Keep only numbers
    return re.sub(r"\D", "", str(phone))



def validate_record(data):

    errors = []

    name = normalize_text(data.get("name"))
    email = normalize_email(data.get("email"))
    phone = normalize_phone(data.get("phone"))
    city = normalize_text(data.get("city"))

    if not name:

        errors.append(
            "Name is required."
        )

    elif len(name) < 2:

        errors.append(
            "Name must contain at least 2 characters."
        )

    if not email:

        errors.append(
            "Email is required."
        )

    else:

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+"
            r"\.[A-Za-z]{2,}$"
        )

        if not re.match(email_pattern, email):

            errors.append(
                "Invalid email address."
            )

    if phone and len(phone) < 10:

        errors.append(
            "Phone number must contain at least 10 digits."
        )


    if not city:

        errors.append(
            "City is required."
        )

    return errors




def calculate_similarity(value1, value2):

    value1 = normalize_text(value1)
    value2 = normalize_text(value2)

    if not value1 or not value2:
        return 0

    return SequenceMatcher(
        None,
        value1,
        value2
    ).ratio()


# ============================================================
# FIND POSSIBLE MATCHES
# ============================================================

def classify_record(data):

    name = normalize_text(data.get("name"))
    email = normalize_email(data.get("email"))
    phone = normalize_phone(data.get("phone"))
    city = normalize_text(data.get("city"))

    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    existing_email = records_collection.find_one(
        {
            "email": email
        }
    )

    if existing_email:

        existing_name = normalize_text(
            existing_email.get("name")
        )

        existing_phone = normalize_phone(
            existing_email.get("phone")
        )

        # Exact duplicate
        if (
            existing_name == name
            and (
                not phone
                or not existing_phone
                or phone == existing_phone
            )
        ):

            return {
                "classification": "DUPLICATE",
                "reason": (
                    "A record with the same email "
                    "and matching information already exists."
                ),
                "matched_id": str(
                    existing_email["_id"]
                )
            }

        # Same email but conflicting information
        return {
            "classification": "FALSE_POSITIVE",
            "reason": (
                "The email already exists, but other "
                "information is different. Manual "
                "verification is required."
            ),
            "matched_id": str(
                existing_email["_id"]
            )
        }

    # --------------------------------------------------------
    # CHECK PHONE
    # --------------------------------------------------------

    if phone:

        existing_phone = records_collection.find_one(
            {
                "phone": phone
            }
        )

        if existing_phone:

            existing_name = normalize_text(
                existing_phone.get("name")
            )

            if existing_name == name:

                return {
                    "classification": "DUPLICATE",
                    "reason": (
                        "A record with the same phone "
                        "number already exists."
                    ),
                    "matched_id": str(
                        existing_phone["_id"]
                    )
                }

            return {
                "classification": "FALSE_POSITIVE",
                "reason": (
                    "The phone number already exists, "
                    "but the name is different."
                ),
                "matched_id": str(
                    existing_phone["_id"]
                )
            }

    # --------------------------------------------------------
    # SIMILAR NAME DETECTION
    # --------------------------------------------------------

    # Get a limited number of records for comparison
    existing_records = records_collection.find().limit(500)

    for record in existing_records:

        old_name = normalize_text(
            record.get("name")
        )

        old_city = normalize_text(
            record.get("city")
        )

        name_score = calculate_similarity(
            name,
            old_name
        )

        # Very similar name
        if name_score >= 0.90:

            # Same city -> possible duplicate
            if city and old_city and city == old_city:

                return {
                    "classification": "POSSIBLE_DUPLICATE",
                    "reason": (
                        "A very similar name and the "
                        "same city were found. "
                        f"Name similarity: "
                        f"{round(name_score * 100, 2)}%."
                    ),
                    "matched_id": str(
                        record["_id"]
                    )
                }

            # Similar name but different information
            return {
                "classification": "FALSE_POSITIVE",
                "reason": (
                    "A very similar name was found, "
                    "but other information is different."
                ),
                "matched_id": str(
                    record["_id"]
                )
            }

    # --------------------------------------------------------
    # UNIQUE
    # --------------------------------------------------------

    return {
        "classification": "UNIQUE",
        "reason": (
            "No duplicate or suspicious matching "
            "record was found."
        ),
        "matched_id": None
    }


# ============================================================
# ADD RECORD
# ============================================================

def add_record(data):

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    errors = validate_record(data)

    if errors:

        return {
            "success": False,
            "classification": "INVALID",
            "message": "Data validation failed.",
            "errors": errors
        }

    # --------------------------------------------------------
    # CLASSIFY
    # --------------------------------------------------------

    classification = classify_record(data)

    # --------------------------------------------------------
    # DUPLICATE
    # --------------------------------------------------------

    if classification["classification"] == "DUPLICATE":

        return {
            "success": False,
            "classification": "DUPLICATE",
            "message": "Duplicate record rejected.",
            "reason": classification["reason"],
            "matched_id": classification["matched_id"]
        }

    # --------------------------------------------------------
    # FALSE POSITIVE
    # --------------------------------------------------------

    if classification["classification"] == "FALSE_POSITIVE":

        return {
            "success": False,
            "classification": "FALSE_POSITIVE",
            "message": (
                "Possible false positive detected. "
                "Manual verification is required."
            ),
            "reason": classification["reason"],
            "matched_id": classification["matched_id"]
        }

    # --------------------------------------------------------
    # POSSIBLE DUPLICATE
    # --------------------------------------------------------

    if classification["classification"] == "POSSIBLE_DUPLICATE":

        return {
            "success": False,
            "classification": "POSSIBLE_DUPLICATE",
            "message": (
                "Possible duplicate detected. "
                "Record was not added."
            ),
            "reason": classification["reason"],
            "matched_id": classification["matched_id"]
        }

    # --------------------------------------------------------
    # UNIQUE RECORD
    # --------------------------------------------------------

    name = normalize_text(data.get("name"))
    email = normalize_email(data.get("email"))
    phone = normalize_phone(data.get("phone"))
    city = normalize_text(data.get("city"))
    source = normalize_text(data.get("data_source"))

    record = {
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "data_source": source,
        "verified": True,
        "classification": "UNIQUE",
        "created_at": datetime.utcnow()
    }

    try:

        result = records_collection.insert_one(
            record
        )

        return {
            "success": True,
            "classification": "UNIQUE",
            "message": (
                "Unique and verified record "
                "added successfully."
            ),
            "record_id": str(
                result.inserted_id
            )
        }

    except DuplicateKeyError:

        return {
            "success": False,
            "classification": "DUPLICATE",
            "message": (
                "Duplicate rejected by the "
                "database protection system."
            )
        }


# ============================================================
# API - ADD DATA
# ============================================================

@app.route(
    "/add",
    methods=["POST"]
)
def add_data():

    if records_collection is None:

        return jsonify({
            "success": False,
            "message": (
                "Database is not connected. "
                "Please configure MONGODB_URI."
            )
        }), 500

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No data received."
            }), 400

        result = add_record(data)

        if result["success"]:

            return jsonify(result), 201

        return jsonify(result), 409

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Server error.",
            "error": str(error)
        }), 500


# ============================================================
# API - GET ALL RECORDS
# ============================================================

@app.route(
    "/records",
    methods=["GET"]
)
def get_records():

    if records_collection is None:

        return jsonify({
            "success": False,
            "message": "Database is not connected."
        }), 500

    records = list(
        records_collection.find().sort(
            "created_at",
            -1
        )
    )

    result = []

    for record in records:

        result.append({

            "id": str(
                record["_id"]
            ),

            "name": record.get(
                "name",
                ""
            ),

            "email": record.get(
                "email",
                ""
            ),

            "phone": record.get(
                "phone",
                ""
            ),

            "city": record.get(
                "city",
                ""
            ),

            "data_source": record.get(
                "data_source",
                ""
            ),

            "verified": record.get(
                "verified",
                False
            ),

            "classification": record.get(
                "classification",
                ""
            ),

            "created_at": str(
                record.get(
                    "created_at",
                    ""
                )
            )
        })

    return jsonify({

        "success": True,

        "total_records": len(result),

        "records": result

    })


# ============================================================
# API - SEARCH
# ============================================================

@app.route(
    "/search",
    methods=["GET"]
)
def search_records():

    if records_collection is None:

        return jsonify({
            "success": False,
            "message": "Database is not connected."
        }), 500

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "success": False,
            "message": "Search query is required."
        }), 400

    search_pattern = re.escape(
        query
    )

    records = list(
        records_collection.find({
            "$or": [

                {
                    "name": {
                        "$regex": search_pattern,
                        "$options": "i"
                    }
                },

                {
                    "email": {
                        "$regex": search_pattern,
                        "$options": "i"
                    }
                },

                {
                    "phone": {
                        "$regex": search_pattern,
                        "$options": "i"
                    }
                },

                {
                    "city": {
                        "$regex": search_pattern,
                        "$options": "i"
                    }
                }

            ]
        })
    )

    result = []

    for record in records:

        result.append({

            "id": str(
                record["_id"]
            ),

            "name": record.get(
                "name",
                ""
            ),

            "email": record.get(
                "email",
                ""
            ),

            "phone": record.get(
                "phone",
                ""
            ),

            "city": record.get(
                "city",
                ""
            )

        })

    return jsonify({

        "success": True,

        "query": query,

        "count": len(result),

        "records": result

    })


# ============================================================
# API - DELETE
# ============================================================

@app.route(
    "/delete/<record_id>",
    methods=["DELETE"]
)
def delete_record(record_id):

    if records_collection is None:

        return jsonify({
            "success": False,
            "message": "Database is not connected."
        }), 500

    try:

        from bson.objectid import ObjectId

        result = records_collection.delete_one(
            {
                "_id": ObjectId(record_id)
            }
        )

        if result.deleted_count == 0:

            return jsonify({
                "success": False,
                "message": "Record not found."
            }), 404

        return jsonify({

            "success": True,

            "message": (
                "Record deleted successfully."
            )

        })

    except Exception as error:

        return jsonify({

            "success": False,

            "message": "Invalid record ID.",

            "error": str(error)

        }), 400


# ============================================================
# WEB DASHBOARD
# ============================================================

HTML_PAGE = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
Data Redundancy Removal System
</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        #0f172a;

    color:
        #e2e8f0;

}

.container {

    width: 92%;

    max-width: 1200px;

    margin:
        40px auto;

}

.header {

    text-align:
        center;

    margin-bottom:
        30px;

}

.header h1 {

    margin-bottom:
        10px;

    font-size:
        32px;

}

.header p {

    color:
        #94a3b8;

}

.card {

    background:
        #1e293b;

    border:
        1px solid #334155;

    border-radius:
        12px;

    padding:
        25px;

    margin-bottom:
        25px;

}

.card h2 {

    margin-top:
        0;

}

.form-grid {

    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                220px,
                1fr
            )
        );

    gap:
        15px;

}

input {

    width:
        100%;

    padding:
        12px;

    background:
        #0f172a;

    border:
        1px solid #475569;

    border-radius:
        7px;

    color:
        white;

    font-size:
        15px;

}

input:focus {

    outline:
        none;

    border-color:
        #38bdf8;

}

button {

    padding:
        12px 20px;

    border:
        none;

    border-radius:
        7px;

    cursor:
        pointer;

    background:
        #2563eb;

    color:
        white;

    font-weight:
        bold;

}

button:hover {

    background:
        #1d4ed8;

}

.submit-button {

    margin-top:
        18px;

    width:
        100%;

}

#result {

    margin-top:
        20px;

    padding:
        15px;

    border-radius:
        8px;

    background:
        #0f172a;

    border:
        1px solid #334155;

}

table {

    width:
        100%;

    border-collapse:
        collapse;

    margin-top:
        20px;

}

th {

    background:
        #0f172a;

    color:
        #38bdf8;

}

th,
td {

    padding:
        12px;

    border:
        1px solid #334155;

    text-align:
        left;

}

.status-unique {

    color:
        #22c55e;

    font-weight:
        bold;

}

.status-duplicate {

    color:
        #ef4444;

    font-weight:
        bold;

}

.small-button {

    padding:
        7px 12px;

    font-size:
        12px;

}

@media(max-width:700px) {

    table {

        font-size:
            12px;

    }

    th,
    td {

        padding:
            7px;

    }

}

</style>

</head>

<body>

<div class="container">

<div class="header">

<h1>
Data Redundancy Removal System
</h1>

<p>
Cloud-based data validation and duplicate detection
</p>

</div>


<div class="card">

<h2>
Add New Data
</h2>

<form id="dataForm">

<div class="form-grid">

<input
type="text"
id="name"
placeholder="Full Name"
required
>

<input
type="email"
id="email"
placeholder="Email Address"
required
>

<input
type="text"
id="phone"
placeholder="Phone Number"
>

<input
type="text"
id="city"
placeholder="City"
required
>

<input
type="text"
id="source"
placeholder="Data Source"
>

</div>

<button
type="submit"
class="submit-button"
>

Validate & Add Data

</button>

</form>


<div id="result">

Ready to validate data.

</div>

</div>


<div class="card">

<h2>
Database Records
</h2>

<button
onclick="loadRecords()"
>

Refresh Records

</button>

<div id="records">

Loading...

</div>

</div>

</div>


<script>

const form =
    document.getElementById(
        "dataForm"
    );


form.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const data = {

            name:
                document.getElementById(
                    "name"
                ).value,

            email:
                document.getElementById(
                    "email"
                ).value,

            phone:
                document.getElementById(
                    "phone"
                ).value,

            city:
                document.getElementById(
                    "city"
                ).value,

            data_source:
                document.getElementById(
                    "source"
                ).value

        };


        const response =
            await fetch(
                "/add",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            data
                        )

                }
            );


        const result =
            await response.json();


        let html =

            "<strong>Classification:</strong> " +

            result.classification +

            "<br><br>" +

            "<strong>Message:</strong> " +

            result.message;


        if (result.reason) {

            html +=

                "<br><br>" +

                "<strong>Reason:</strong> " +

                result.reason;

        }


        if (result.errors) {

            html +=

                "<br><br>" +

                "<strong>Errors:</strong><br>" +

                result.errors.join(
                    "<br>"
                );

        }


        document.getElementById(
            "result"
        ).innerHTML = html;


        loadRecords();

    }
);


async function loadRecords() {

    try {

        const response =
            await fetch(
                "/records"
            );

        const data =
            await response.json();


        if (!data.success) {

            document.getElementById(
                "records"
            ).innerHTML =

                "<p>" +
                data.message +
                "</p>";

            return;

        }


        let html =

            "<p><strong>Total Records: " +

            data.total_records +

            "</strong></p>";


        if (
            data.records.length === 0
        ) {

            html +=
                "<p>No records found.</p>";

        } else {

            html +=
                "<table>";

            html +=
                "<tr>" +

                "<th>ID</th>" +

                "<th>Name</th>" +

                "<th>Email</th>" +

                "<th>Phone</th>" +

                "<th>City</th>" +

                "<th>Verified</th>" +

                "<th>Action</th>" +

                "</tr>";


            data.records.forEach(
                function(record) {

                    html +=

                        "<tr>" +

                        "<td>" +
                        record.id.substring(
                            0,
                            8
                        ) +
                        "</td>" +

                        "<td>" +
                        escapeHtml(
                            record.name
                        ) +
                        "</td>" +

                        "<td>" +
                        escapeHtml(
                            record.email
                        ) +
                        "</td>" +

                        "<td>" +
                        escapeHtml(
                            record.phone
                        ) +
                        "</td>" +

                        "<td>" +
                        escapeHtml(
                            record.city
                        ) +
                        "</td>" +

                        "<td class='status-unique'>" +

                        (
                            record.verified
                                ? "YES"
                                : "NO"
                        ) +

                        "</td>" +

                        "<td>" +

                        "<button " +

                        "class='small-button' " +

                        "onclick=\"deleteRecord('" +

                        record.id +

                        "')\">" +

                        "Delete" +

                        "</button>" +

                        "</td>" +

                        "</tr>";

                }
            );


            html +=
                "</table>";

        }


        document.getElementById(
            "records"
        ).innerHTML = html;

    }

    catch(error) {

        document.getElementById(
            "records"
        ).innerHTML =

            "<p>Unable to load records.</p>";

    }

}


async function deleteRecord(id) {

    if (
        !confirm(
            "Are you sure you want to delete this record?"
        )
    ) {

        return;

    }


    await fetch(

        "/delete/" + id,

        {

            method:
                "DELETE"

        }

    );


    loadRecords();

}


function escapeHtml(value) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


loadRecords();

</script>

</body>

</html>

"""


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template_string(
        HTML_PAGE
    )


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print("")
    print("=" * 60)
    print("DATA REDUNDANCY REMOVAL SYSTEM")
    print("=" * 60)

    database_status = connect_database()

    if database_status:

        print(
            "Database: MongoDB Atlas"
        )

        print(
            "Status: CONNECTED"
        )

    else:

        print(
            "Database: NOT CONNECTED"
        )

        print(
            "Set MONGODB_URI before running the application."
        )

    print("")
    print(
        "Starting Flask server..."
    )

    print(
        "Open: http://127.0.0.1:5000"
    )

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
