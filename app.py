from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt

# Initialize Flask app
app = Flask(__name__)
app.secret_key = '@2407'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Replace with your database username
app.config['MYSQL_PASSWORD'] = '@2407jana'  # Replace with your database password
app.config['MYSQL_DB'] = 'todo_app'  # Replace with your database name

# Initialize MySQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('login.html') 

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):  # user[3] is the hashed password column
            session['user_id'] = user[0]  # Store user ID in session
            return redirect(url_for('tasks'))  # Redirect to tasks page
        else:
            flash('Invalid credentials, please try again.', 'danger')

    return render_template('login.html')

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']  # Get the name
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()

        flash('Sign up successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for the tasks page (dashboard)
@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Handle adding a new task
    if request.method == 'POST':
        task_text = request.form['task_text']
        if task_text.strip():  # Ensure the task is not empty
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO tasks (user_id, task_text) VALUES (%s, %s)", (user_id, task_text))
            mysql.connection.commit()
            cur.close()
            flash('Task added successfully!', 'success')
        else:
            flash('Task cannot be empty!', 'danger')

    # Fetch all tasks for the logged-in user, regardless of completion status
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    tasks = cur.fetchall()
    cur.close()

    return render_template('task.html', tasks=tasks)



# Route for logging out
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    task_text = request.form['task_description']  # Fetch input from the form

    if task_text.strip():  # Ensure the task is not empty
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tasks (user_id, task_text) VALUES (%s, %s)", (user_id, task_text))
        mysql.connection.commit()
        cur.close()
        flash('Task added successfully!', 'success')
    else:
        flash('Task cannot be empty!', 'danger')

    return redirect(url_for('tasks'))

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('login'))

# Route for deleting a task
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    mysql.connection.commit()
    cur.close()

    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    updated_task = request.form['updated_task']
    if updated_task.strip():
        cur = mysql.connection.cursor()
        cur.execute("UPDATE tasks SET task_text = %s WHERE id = %s AND user_id = %s", (updated_task, task_id, session['user_id']))
        mysql.connection.commit()
        cur.close()
        flash('Task updated successfully!', 'success')
    else:
        flash('Task cannot be empty!', 'danger')
    
    return redirect(url_for('tasks'))


# Route for updating task status (completed or not)
@app.route('/toggle_task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cur.fetchone()

    if task:
        new_status = not task[3]  # Toggle the 'completed' field
        cur.execute("UPDATE tasks SET completed = %s WHERE id = %s", (new_status, task_id))
        mysql.connection.commit()
    cur.close()

    flash('Task status updated!', 'success')
    return redirect(url_for('tasks'))


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
