import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config


def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# ---------- Users ----------

def register_user(name, email, password, role, phone, location):
    """Returns True on success, False if email already exists."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            hashed_pw = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password, role, phone, location) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, hashed_pw, role, phone, location)
            )
        return True
    except pymysql.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(email, password):
    """Returns user dict on success, None on failure."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            return user
        return None
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, role, phone, location, created_at FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()


# ---------- Disasters ----------

def get_all_disasters():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM disasters WHERE status = 'active' ORDER BY date_occurred DESC")
            return cursor.fetchall()
    finally:
        conn.close()


def get_all_disasters_admin():
    """All disasters (for admin management)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM disasters ORDER BY date_occurred DESC")
            return cursor.fetchall()
    finally:
        conn.close()


def add_disaster(name, description, location, date_occurred):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO disasters (name, description, location, date_occurred, status) "
                "VALUES (%s, %s, %s, %s, 'active')",
                (name, description, location, date_occurred)
            )
    finally:
        conn.close()


def update_disaster_status(disaster_id, status):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE disasters SET status = %s WHERE id = %s", (status, disaster_id))
    finally:
        conn.close()


# ---------- Donations ----------

def add_donation(donor_id, disaster_id, resource_name, quantity, location, description):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO donations (donor_id, disaster_id, resource_name, quantity, location, description) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (donor_id, disaster_id, resource_name, quantity, location, description)
            )
    finally:
        conn.close()


def get_donations_by_donor(donor_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT d.*, dis.name as disaster_name
                   FROM donations d
                   LEFT JOIN disasters dis ON d.disaster_id = dis.id
                   WHERE d.donor_id = %s
                   ORDER BY d.created_at DESC""",
                (donor_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def get_unverified_donations():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT d.*, u.name AS donor_name, dis.name AS disaster_name
                   FROM donations d
                   JOIN users u ON d.donor_id = u.id
                   LEFT JOIN disasters dis ON d.disaster_id = dis.id
                   WHERE d.status = 'pending'
                   ORDER BY d.created_at ASC"""
            )
            return cursor.fetchall()
    finally:
        conn.close()


def verify_donation(donation_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE donations SET status = 'verified' WHERE id = %s", (donation_id,))
    finally:
        conn.close()


def reject_donation(donation_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE donations SET status = 'rejected' WHERE id = %s", (donation_id,))
    finally:
        conn.close()


# ---------- Requests ----------

def add_request(seeker_id, disaster_id, resource_name, quantity, urgency, location, description):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO requests (seeker_id, disaster_id, resource_name, quantity, urgency, location, description) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (seeker_id, disaster_id, resource_name, quantity, urgency, location, description)
            )
    finally:
        conn.close()


def get_requests_by_seeker(seeker_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT r.*, dis.name as disaster_name
                   FROM requests r
                   LEFT JOIN disasters dis ON r.disaster_id = dis.id
                   WHERE r.seeker_id = %s
                   ORDER BY r.created_at DESC""",
                (seeker_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def get_unverified_requests():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT r.*, u.name AS seeker_name, dis.name AS disaster_name
                   FROM requests r
                   JOIN users u ON r.seeker_id = u.id
                   LEFT JOIN disasters dis ON r.disaster_id = dis.id
                   WHERE r.status = 'pending'
                   ORDER BY
                       FIELD(r.urgency, 'high', 'medium', 'low'),
                       r.created_at ASC"""
            )
            return cursor.fetchall()
    finally:
        conn.close()


def verify_request(request_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE requests SET status = 'verified' WHERE id = %s", (request_id,))
    finally:
        conn.close()


def reject_request(request_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE requests SET status = 'rejected' WHERE id = %s", (request_id,))
    finally:
        conn.close()


# ---------- Gap Analysis ----------

def get_demand_supply_gap():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT
                       r.resource_name,
                       COALESCE(SUM(r.quantity - r.fulfilled_quantity), 0) AS total_requested,
                       COALESCE(SUM(d.quantity - d.allocated_quantity), 0) AS total_available
                   FROM requests r
                   LEFT JOIN donations d
                       ON LOWER(TRIM(r.resource_name)) = LOWER(TRIM(d.resource_name))
                       AND d.status = 'verified'
                   WHERE r.status = 'verified'
                     AND r.fulfilled_quantity < r.quantity
                   GROUP BY r.resource_name
                   ORDER BY (COALESCE(SUM(r.quantity - r.fulfilled_quantity), 0) -
                             COALESCE(SUM(d.quantity - d.allocated_quantity), 0)) DESC"""
            )
            return cursor.fetchall()
    finally:
        conn.close()


# ---------- Resource Matching ----------

def match_resources():
    """
    Greedy matching algorithm:
    - Processes verified requests ordered by urgency (high → medium → low)
    - For each request, finds verified donations with matching resource name
      and location, allocated FIFO
    - Creates allocation records and updates fulfilled/allocated quantities
    - Uses a transaction so partial failures roll back cleanly
    """
    conn = get_db_connection()
    try:
        conn.autocommit = False
        with conn.cursor() as cursor:
            # Fetch all verified, unfulfilled requests ordered by urgency
            cursor.execute(
                """SELECT * FROM requests
                   WHERE status = 'verified' AND fulfilled_quantity < quantity
                   ORDER BY FIELD(urgency, 'high', 'medium', 'low'), created_at ASC"""
            )
            requests = cursor.fetchall()

            for req in requests:
                remaining = req['quantity'] - req['fulfilled_quantity']
                if remaining <= 0:
                    continue

                # Find matching donations: same resource (case-insensitive), same location, available stock
                cursor.execute(
                    """SELECT * FROM donations
                       WHERE status = 'verified'
                         AND LOWER(TRIM(resource_name)) = LOWER(TRIM(%s))
                         AND LOWER(TRIM(location))      = LOWER(TRIM(%s))
                         AND quantity > allocated_quantity
                       ORDER BY created_at ASC""",
                    (req['resource_name'], req['location'])
                )
                donations = cursor.fetchall()

                for don in donations:
                    available = don['quantity'] - don['allocated_quantity']
                    if available <= 0:
                        continue

                    allocate_qty = min(remaining, available)

                    # Insert allocation record
                    cursor.execute(
                        "INSERT INTO allocations (request_id, donation_id, allocated_quantity) "
                        "VALUES (%s, %s, %s)",
                        (req['id'], don['id'], allocate_qty)
                    )

                    # Update donation
                    cursor.execute(
                        "UPDATE donations SET allocated_quantity = allocated_quantity + %s WHERE id = %s",
                        (allocate_qty, don['id'])
                    )

                    # Update request
                    new_fulfilled = req['fulfilled_quantity'] + allocate_qty
                    cursor.execute(
                        "UPDATE requests SET fulfilled_quantity = fulfilled_quantity + %s WHERE id = %s",
                        (allocate_qty, req['id'])
                    )

                    # Mark request fulfilled if fully covered
                    if new_fulfilled >= req['quantity']:
                        cursor.execute(
                            "UPDATE requests SET status = 'fulfilled' WHERE id = %s",
                            (req['id'],)
                        )

                    remaining -= allocate_qty
                    req['fulfilled_quantity'] = new_fulfilled
                    if remaining <= 0:
                        break

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        conn.close()


# ---------- Allocations ----------

def get_all_allocations():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT
                       a.id, a.allocated_quantity, a.status, a.created_at,
                       r.resource_name, r.urgency,
                       r.quantity AS request_qty, r.fulfilled_quantity,
                       r.location AS request_location,
                       u_seeker.name AS seeker_name,
                       u_seeker.phone AS seeker_phone,
                       u_seeker.location AS seeker_location,
                       d.quantity AS donation_qty, d.allocated_quantity AS donation_allocated,
                       u_donor.name AS donor_name,
                       u_donor.phone AS donor_phone,
                       u_donor.location AS donor_location
                   FROM allocations a
                   JOIN requests r ON a.request_id = r.id
                   JOIN users u_seeker ON r.seeker_id = u_seeker.id
                   JOIN donations d ON a.donation_id = d.id
                   JOIN users u_donor ON d.donor_id = u_donor.id
                   ORDER BY a.created_at DESC"""
            )
            return cursor.fetchall()
    finally:
        conn.close()


def get_allocations_for_seeker(seeker_id):
    """Seeker can see donor contact info for their matched requests."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT
                       a.id, a.allocated_quantity, a.status, a.created_at,
                       r.resource_name, r.urgency, r.location AS request_location,
                       u_donor.name AS donor_name,
                       u_donor.phone AS donor_phone,
                       u_donor.location AS donor_location
                   FROM allocations a
                   JOIN requests r ON a.request_id = r.id
                   JOIN donations d ON a.donation_id = d.id
                   JOIN users u_donor ON d.donor_id = u_donor.id
                   WHERE r.seeker_id = %s
                   ORDER BY a.created_at DESC""",
                (seeker_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def get_allocations_for_donor(donor_id):
    """Donor can see seeker contact info for their matched donations."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT
                       a.id, a.allocated_quantity, a.status, a.created_at,
                       r.resource_name, r.urgency, r.location AS request_location,
                       u_seeker.name AS seeker_name,
                       u_seeker.phone AS seeker_phone,
                       u_seeker.location AS seeker_location
                   FROM allocations a
                   JOIN requests r ON a.request_id = r.id
                   JOIN users u_seeker ON r.seeker_id = u_seeker.id
                   JOIN donations d ON a.donation_id = d.id
                   WHERE d.donor_id = %s
                   ORDER BY a.created_at DESC""",
                (donor_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


# ---------- Admin Stats ----------

def get_dashboard_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            stats = {}
            cursor.execute("SELECT COUNT(*) AS n FROM users WHERE role = 'donor'")
            stats['donors'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM users WHERE role = 'seeker'")
            stats['seekers'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM donations WHERE status = 'pending'")
            stats['pending_donations'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM requests WHERE status = 'pending'")
            stats['pending_requests'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM donations WHERE status = 'verified'")
            stats['verified_donations'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM requests WHERE status = 'verified'")
            stats['verified_requests'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM allocations")
            stats['allocations'] = cursor.fetchone()['n']
            cursor.execute("SELECT COUNT(*) AS n FROM disasters WHERE status = 'active'")
            stats['active_disasters'] = cursor.fetchone()['n']
            return stats
    finally:
        conn.close()
