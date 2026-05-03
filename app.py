from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import models
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


# ---------- Auth Decorators ----------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ---------- Public Routes ----------

@app.route('/')
def index():
    disasters = models.get_all_disasters()
    return render_template('index.html', disasters=disasters)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        role     = request.form['role']
        phone    = request.form.get('phone', '').strip()
        location = request.form['location'].strip()

        if not name or not email or not password or not location:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html')

        # Prevent self-registration as admin
        if role == 'admin':
            flash('Admin accounts cannot be self-registered.', 'danger')
            return render_template('register.html')

        if models.register_user(name, email, password, role, phone, location):
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('An account with that email already exists.', 'danger')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['password']
        user = models.login_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['name']    = user['name']
            session['role']    = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'donor':
                return redirect(url_for('donor_dashboard'))
            else:
                return redirect(url_for('seeker_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ---------- Donor Routes ----------

@app.route('/donor/dashboard')
@login_required
@role_required('donor')
def donor_dashboard():
    donations = models.get_donations_by_donor(session['user_id'])
    allocations = models.get_allocations_for_donor(session['user_id'])
    return render_template('donor_dashboard.html', donations=donations, allocations=allocations)


@app.route('/donor/add_donation', methods=['GET', 'POST'])
@login_required
@role_required('donor')
def add_donation():
    disasters = models.get_all_disasters()
    if request.method == 'POST':
        disaster_id   = request.form['disaster_id']
        resource_name = request.form['resource_name'].strip()
        quantity      = request.form['quantity']
        location      = request.form['location'].strip()
        description   = request.form.get('description', '').strip()

        if not resource_name or not quantity or not location:
            flash('Please fill in all required fields.', 'danger')
            return render_template('add_donation.html', disasters=disasters)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash('Quantity must be a positive whole number.', 'danger')
            return render_template('add_donation.html', disasters=disasters)

        models.add_donation(session['user_id'], disaster_id, resource_name, quantity, location, description)
        flash('Donation submitted successfully! Awaiting admin verification.', 'success')
        return redirect(url_for('donor_dashboard'))
    return render_template('add_donation.html', disasters=disasters)


# ---------- Seeker Routes ----------

@app.route('/seeker/dashboard')
@login_required
@role_required('seeker')
def seeker_dashboard():
    reqs = models.get_requests_by_seeker(session['user_id'])
    allocations = models.get_allocations_for_seeker(session['user_id'])
    return render_template('seeker_dashboard.html', requests=reqs, allocations=allocations)


@app.route('/seeker/add_request', methods=['GET', 'POST'])
@login_required
@role_required('seeker')
def add_request():
    disasters = models.get_all_disasters()
    if request.method == 'POST':
        disaster_id   = request.form['disaster_id']
        resource_name = request.form['resource_name'].strip()
        quantity      = request.form['quantity']
        urgency       = request.form['urgency']
        location      = request.form['location'].strip()
        description   = request.form.get('description', '').strip()

        if not resource_name or not quantity or not location:
            flash('Please fill in all required fields.', 'danger')
            return render_template('add_request.html', disasters=disasters)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash('Quantity must be a positive whole number.', 'danger')
            return render_template('add_request.html', disasters=disasters)

        models.add_request(session['user_id'], disaster_id, resource_name, quantity, urgency, location, description)
        flash('Request submitted successfully! Awaiting admin verification.', 'success')
        return redirect(url_for('seeker_dashboard'))
    return render_template('add_request.html', disasters=disasters)


# ---------- Admin Routes ----------

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    stats = models.get_dashboard_stats()
    return render_template('admin_dashboard.html', stats=stats)


@app.route('/admin/disasters')
@login_required
@role_required('admin')
def manage_disasters():
    disasters = models.get_all_disasters_admin()
    return render_template('manage_disasters.html', disasters=disasters)


@app.route('/admin/disasters/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_disaster():
    if request.method == 'POST':
        name          = request.form['name'].strip()
        description   = request.form.get('description', '').strip()
        location      = request.form['location'].strip()
        date_occurred = request.form['date_occurred']
        if not name or not location or not date_occurred:
            flash('Name, location, and date are required.', 'danger')
            return render_template('add_disaster.html')
        models.add_disaster(name, description, location, date_occurred)
        flash(f'Disaster "{name}" added successfully.', 'success')
        return redirect(url_for('manage_disasters'))
    return render_template('add_disaster.html')


@app.route('/admin/disasters/<int:disaster_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_disaster(disaster_id):
    new_status = request.form.get('status', 'inactive')
    models.update_disaster_status(disaster_id, new_status)
    flash('Disaster status updated.', 'success')
    return redirect(url_for('manage_disasters'))


@app.route('/admin/verify_donations')
@login_required
@role_required('admin')
def verify_donations():
    donations = models.get_unverified_donations()
    return render_template('verify_donations.html', donations=donations)


@app.route('/admin/verify_donation/<int:donation_id>', methods=['POST'])
@login_required
@role_required('admin')
def verify_donation(donation_id):
    action = request.form.get('action', 'verify')
    if action == 'reject':
        models.reject_donation(donation_id)
        flash('Donation rejected.', 'warning')
    else:
        models.verify_donation(donation_id)
        flash('Donation verified successfully!', 'success')
    return redirect(url_for('verify_donations'))


@app.route('/admin/verify_requests')
@login_required
@role_required('admin')
def verify_requests():
    reqs = models.get_unverified_requests()
    return render_template('verify_requests.html', requests=reqs)


@app.route('/admin/verify_request/<int:request_id>', methods=['POST'])
@login_required
@role_required('admin')
def verify_request(request_id):
    action = request.form.get('action', 'verify')
    if action == 'reject':
        models.reject_request(request_id)
        flash('Request rejected.', 'warning')
    else:
        models.verify_request(request_id)
        flash('Request verified successfully!', 'success')
    return redirect(url_for('verify_requests'))


@app.route('/admin/gap_analysis')
@login_required
@role_required('admin')
def gap_analysis():
    gaps = models.get_demand_supply_gap()
    return render_template('gap_analysis.html', gaps=gaps)


@app.route('/admin/match_resources', methods=['POST'])
@login_required
@role_required('admin')
def match_resources():
    try:
        models.match_resources()
        flash('Resource matching completed successfully!', 'success')
    except Exception as e:
        flash(f'Matching failed: {str(e)}', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/allocations')
@login_required
@role_required('admin')
def view_allocations():
    allocations = models.get_all_allocations()
    return render_template('allocations.html', allocations=allocations)


import traceback

@app.errorhandler(500)
def internal_error(e):
    return f"<pre>500 Error:\n{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
