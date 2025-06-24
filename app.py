from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import csv
from io import StringIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'parent' or 'child'
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DifficultySetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., 'easy', 'medium', 'hard'
    display_name = db.Column(db.String(50), nullable=False)  # e.g., 'Helppo', 'Keskitaso', 'Vaikea'
    points = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), default='secondary')  # Bootstrap color class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TaskTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.String(20), default='easy')  # easy, medium, hard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.String(20), default='easy')  # easy, medium, hard
    status = db.Column(db.String(20), default='available')  # available, in_progress, completed, pending_approval
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    always_available = db.Column(db.Boolean, default=False)
    assigned_children = db.Column(db.String(200), nullable=True)  # Comma-separated list of child IDs
    template_id = db.Column(db.Integer, db.ForeignKey('task_template.id'), nullable=True)

class TaskCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_earned = db.Column(db.Integer, nullable=False)
    approved_by_parent = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    comment = db.Column(db.Text, nullable=True)  # Child's comment when completing the task

    # Relationship to Task
    task = db.relationship('Task', backref='completions')

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points_cost = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # Can be deactivated without deleting
    assigned_children = db.Column(db.String(200), nullable=True)  # Comma-separated list of child IDs

class RewardPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by_parent = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    reward = db.relationship('Reward', backref='purchases')

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'parent':
            return redirect(url_for('parent_dashboard'))
        else:
            return redirect(url_for('child_dashboard'))
    
    user = db.session.get(User, session.get('user_id'))
    if user:
        if user.role == 'parent':
            return redirect(url_for('parent_dashboard'))
        else:
            return redirect(url_for('child_dashboard'))
    
    # Show login options
    children = User.query.filter_by(role='child').all()
    return render_template('index.html', children=children)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        
        # Hardcoded parent account
        if password == '2025':
            # Get or create the parent user
            parent = User.query.filter_by(username='Vanhempi').first()
            if not parent:
                parent = User(
                    username='Vanhempi',
                    password_hash=generate_password_hash('2025'),
                    role='parent'
                )
                db.session.add(parent)
                db.session.commit()
            
            session['user_id'] = parent.id
            session['username'] = parent.username
            session['role'] = parent.role
            
            log_action('Parent logged in')
            return redirect(url_for('parent_dashboard'))
        else:
            log_action('Failed parent login attempt')
            flash('Virheellinen salasana')
    
    return render_template('login.html')

@app.route('/child/login', methods=['GET', 'POST'])
def child_login():
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        
        if child_id:
            child = User.query.filter_by(id=child_id, role='child').first()
            if child:
                session['user_id'] = child.id
                session['username'] = child.username
                session['role'] = 'child'
                log_action(f'Child {child.username} logged in')
                return redirect(url_for('child_dashboard'))
        
        log_action('Failed child login attempt')
        flash('Valitse lapsi')
    
    children = User.query.filter_by(role='child').all()
    return render_template('child_login.html', children=children)

@app.route('/logout')
def logout():
    log_action('User logged out')
    session.clear()
    return redirect(url_for('index'))

@app.route('/parent/dashboard')
def parent_dashboard():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    # Only show active tasks (not completed) in parent dashboard
    tasks = Task.query.filter(
        Task.status != 'completed'
    ).order_by(Task.title.asc()).all()
    children = User.query.filter_by(role='child').all()
    
    # Debug: Print task count
    print(f"DEBUG: Found {len(tasks)} active tasks in database")
    for task in tasks:
        print(f"DEBUG: Task ID {task.id}, Title: {task.title}, Status: {task.status}")
    
    # Get pending approvals
    pending_approvals = TaskCompletion.query.join(Task).filter(
        TaskCompletion.approved_by_parent == False
    ).order_by(TaskCompletion.completed_at.desc()).all()
    
    # Get pending reward approvals
    pending_reward_approvals = RewardPurchase.query.join(Reward).filter(
        RewardPurchase.approved_by_parent == False
    ).order_by(RewardPurchase.purchased_at.desc()).all()
    
    # Get task templates
    task_templates = TaskTemplate.query.order_by(TaskTemplate.title.asc()).all()
    
    # Get rewards
    rewards = Reward.query.order_by(Reward.title.asc()).all()
    
    # Get difficulty settings for display
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    
    return render_template('parent_dashboard.html', 
                         tasks=tasks, 
                         children=children, 
                         user=user,
                         pending_approvals=pending_approvals,
                         pending_reward_approvals=pending_reward_approvals,
                         task_templates=task_templates,
                         rewards=rewards,
                         difficulty_settings=difficulty_settings)

@app.route('/child/dashboard')
def child_dashboard():
    if 'user_id' not in session or session['role'] != 'child':
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    # Get all tasks that could be available to this child
    # Only show tasks that are available OR always_available but not completed
    all_tasks = Task.query.filter(
        (Task.status == 'available') | 
        ((Task.always_available == True) & (Task.status != 'completed'))
    ).all()
    
    # Debug: Print all tasks found
    print(f"DEBUG: Child {user.username} - Found {len(all_tasks)} total tasks (available or always_available but not completed)")
    for task in all_tasks:
        print(f"DEBUG: Task ID {task.id}, Title: {task.title}, Status: {task.status}, Always Available: {task.always_available}, Assigned Children: {task.assigned_children}")
    
    # Filter tasks based on assignment
    available_tasks = []
    
    for task in all_tasks:
        # Check if task is assigned to this child (or no specific assignment)
        is_assigned = True
        if task.assigned_children:
            assigned_child_ids = [int(x.strip()) for x in task.assigned_children.split(',') if x.strip()]
            if user.id not in assigned_child_ids:
                is_assigned = False
        
        if not is_assigned:
            continue
            
        # Add to available tasks if it's available or always available
        if task.status == 'available' or task.always_available:
            available_tasks.append(task)
    
    # Debug: Print final available tasks
    print(f"DEBUG: Child {user.username} - Final available tasks: {len(available_tasks)}")
    for task in available_tasks:
        print(f"DEBUG: Available Task ID {task.id}, Title: {task.title}, Status: {task.status}")
    
    my_tasks = Task.query.filter_by(assigned_to=user.id, status='in_progress').order_by(Task.title.asc()).all()
    pending_tasks = Task.query.filter_by(assigned_to=user.id, status='pending_approval').order_by(Task.title.asc()).all()
    completed_tasks = TaskCompletion.query.filter_by(user_id=user.id).order_by(TaskCompletion.completed_at.desc()).limit(10).all()
    
    # Sort available tasks alphabetically
    available_tasks.sort(key=lambda x: x.title)
    
    # Get pending reward purchases
    pending_reward_purchases = RewardPurchase.query.filter_by(
        user_id=user.id,
        approved_by_parent=False
    ).order_by(RewardPurchase.purchased_at.desc()).all()
    
    # Get difficulty settings for display
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    
    return render_template('child_dashboard.html', 
                         available_tasks=available_tasks, 
                         my_tasks=my_tasks, 
                         pending_tasks=pending_tasks,
                         completed_tasks=completed_tasks,
                         pending_reward_purchases=pending_reward_purchases,
                         difficulty_settings=difficulty_settings,
                         user=user)

@app.route('/parent/tasks/create', methods=['GET', 'POST'])
def create_task():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        difficulty = request.form['difficulty']
        due_date_str = request.form.get('due_date')
        always_available = request.form.get('always_available') == 'on'
        assigned_children = request.form.getlist('assigned_children')
        save_as_template = request.form.get('save_as_template') == 'on'
        
        # Get points from difficulty setting
        difficulty_setting = DifficultySetting.query.filter_by(name=difficulty).first()
        if not difficulty_setting:
            flash('Virheellinen vaikeustaso')
            return redirect(url_for('create_task'))
        
        points = difficulty_setting.points
        
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        
        # Convert assigned_children list to comma-separated string
        assigned_children_str = ','.join(assigned_children) if assigned_children else None
        
        # Save as template if requested
        template_id = None
        if save_as_template:
            template = TaskTemplate(
                title=title,
                description=description,
                points=points,
                difficulty=difficulty
            )
            db.session.add(template)
            db.session.flush()  # Get the template ID
            template_id = template.id
            print(f"DEBUG: Created template with ID: {template_id}")
        
        task = Task(
            title=title,
            description=description,
            points=points,
            difficulty=difficulty,
            due_date=due_date,
            always_available=always_available,
            assigned_children=assigned_children_str,
            template_id=template_id
        )
        
        db.session.add(task)
        
        # Debug: Print task info before commit
        print(f"DEBUG: About to create task - Title: {task.title}, Status: {task.status}, Template ID: {template_id}")
        
        try:
            db.session.commit()
            log_action(f'Parent created task: {title}')
            print(f"DEBUG: Successfully created task with title: {title}")
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Error creating task: {e}")
            flash('Virhe tehtävän luomisessa. Yritä uudelleen.')
            return redirect(url_for('create_task'))
        
        if save_as_template:
            flash('Tehtävä ja tehtäväpohja luotu onnistuneesti!')
        else:
            flash('Tehtävä luotu onnistuneesti!')
        return redirect(url_for('parent_dashboard'))
    
    children = User.query.filter_by(role='child').all()
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    return render_template('create_task.html', children=children, difficulty_settings=difficulty_settings)

@app.route('/parent/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    children = User.query.filter_by(role='child').all()
    
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        difficulty = request.form['difficulty']
        
        # Get points from difficulty setting
        difficulty_setting = DifficultySetting.query.filter_by(name=difficulty).first()
        if not difficulty_setting:
            flash('Virheellinen vaikeustaso')
            return render_template('edit_task.html', task=task, children=children, difficulty_settings=DifficultySetting.query.order_by(DifficultySetting.points.asc()).all())
        
        task.points = difficulty_setting.points
        task.difficulty = difficulty
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        else:
            task.due_date = None
        
        # Always available
        task.always_available = request.form.get('always_available') == 'on'
        
        # Assigned children logic
        assign_all = request.form.get('assign_all') == 'on'
        assigned_children = request.form.getlist('assigned_children')
        if assign_all or not assigned_children:
            task.assigned_children = None
        else:
            task.assigned_children = ','.join(assigned_children)
        
        db.session.commit()
        log_action(f'Parent edited task: {task.title}')
        flash('Tehtävä päivitetty onnistuneesti!')
        return redirect(url_for('parent_dashboard'))
    
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    return render_template('edit_task.html', task=task, children=children, difficulty_settings=difficulty_settings)

@app.route('/parent/tasks/<int:task_id>/delete')
def delete_task(task_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    log_action(f'Parent deleted task: {task.title}')
    db.session.delete(task)
    db.session.commit()
    flash('Tehtävä poistettu onnistuneesti!')
    return redirect(url_for('parent_dashboard'))

@app.route('/child/tasks/<int:task_id>/pick')
def pick_task(task_id):
    if 'user_id' not in session or session['role'] != 'child':
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    user_id = session['user_id']

    if task.always_available:
        # Always create a new instance for the child
        new_task = Task(
            title=task.title,
            description=task.description,
            points=task.points,
            difficulty=task.difficulty,
            due_date=task.due_date,
            always_available=False,  # The new instance is not always available
            assigned_children=task.assigned_children,
            template_id=task.template_id,
            status='in_progress',
            assigned_to=user_id
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Tehtävä valittu onnistuneesti!')
        return redirect(url_for('child_dashboard'))
    else:
        if task.status != 'available':
            flash('Tämä tehtävä ei ole vapaana')
            return redirect(url_for('child_dashboard'))
        task.status = 'in_progress'
        task.assigned_to = user_id
        db.session.commit()
        flash('Tehtävä valittu onnistuneesti!')
        return redirect(url_for('child_dashboard'))

@app.route('/child/tasks/<int:task_id>/complete', methods=['GET', 'POST'])
def complete_task(task_id):
    if 'user_id' not in session or session['role'] != 'child':
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != session['user_id'] or task.status != 'in_progress':
        flash('Voit valmistaa vain sinulle annettuja tehtäviä')
        return redirect(url_for('child_dashboard'))
    
    if request.method == 'POST':
        comment = request.form.get('comment', '').strip()
        
        # Mark task as pending approval
        task.status = 'pending_approval'
        task.completed_at = datetime.utcnow()
        
        # Record completion (without awarding points yet)
        completion = TaskCompletion(
            task_id=task.id,
            user_id=session['user_id'],
            points_earned=task.points,
            approved_by_parent=False,
            comment=comment if comment else None
        )
        
        db.session.add(completion)
        db.session.commit()
        
        flash('Tehtävä valmistunut! Odotetaan vanhemman hyväksyntää.')
        return redirect(url_for('child_dashboard'))
    
    # GET: show completion form
    return render_template('complete_task.html', task=task)

@app.route('/parent/children')
def manage_children():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    children = User.query.filter_by(role='child').all()
    return render_template('manage_children.html', children=children)

@app.route('/parent/children/create', methods=['GET', 'POST'])
def create_child():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        
        if User.query.filter_by(username=username).first():
            flash('Käyttäjänimi on jo olemassa')
            return render_template('create_child.html')
        
        child = User(
            username=username,
            password_hash=generate_password_hash(''),  # Empty password since children don't need to log in
            role='child'
        )
        
        db.session.add(child)
        db.session.commit()
        log_action(f'Parent created child: {username}')
        flash('Lapsen tili luotu onnistuneesti!')
        return redirect(url_for('manage_children'))
    
    return render_template('create_child.html')

@app.route('/parent/templates')
def manage_templates():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    templates = TaskTemplate.query.filter(TaskTemplate.id.isnot(None)).order_by(TaskTemplate.title.asc()).all()
    
    # Get difficulty settings for display
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    
    return render_template('manage_templates.html', templates=templates, difficulty_settings=difficulty_settings)

@app.route('/parent/templates/create', methods=['GET', 'POST'])
def create_template():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        difficulty = request.form['difficulty']
        
        # Get points from difficulty setting
        difficulty_setting = DifficultySetting.query.filter_by(name=difficulty).first()
        if not difficulty_setting:
            flash('Virheellinen vaikeustaso')
            return redirect(url_for('create_template'))
        
        points = difficulty_setting.points
        
        template = TaskTemplate(
            title=title,
            description=description,
            points=points,
            difficulty=difficulty
        )
        
        db.session.add(template)
        db.session.commit()
        log_action(f'Parent created task template: {title}')
        flash('Tehtäväpohja luotu onnistuneesti!')
        return redirect(url_for('manage_templates'))
    
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    return render_template('create_template.html', difficulty_settings=difficulty_settings)

@app.route('/parent/templates/<int:template_id>/delete')
def delete_template(template_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    template = TaskTemplate.query.get_or_404(template_id)
    
    db.session.delete(template)
    db.session.commit()
    log_action(f'Parent deleted task template: {template.title}')
    flash('Tehtäväpohja poistettu onnistuneesti!')
    return redirect(url_for('parent_dashboard'))

@app.route('/parent/templates/<int:template_id>/edit', methods=['GET', 'POST'])
def edit_template(template_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    template = TaskTemplate.query.get_or_404(template_id)
    children = User.query.filter_by(role='child').all()
    
    if request.method == 'POST':
        template.title = request.form['title']
        template.description = request.form['description']
        difficulty = request.form['difficulty']
        
        # Get points from difficulty setting
        difficulty_setting = DifficultySetting.query.filter_by(name=difficulty).first()
        if not difficulty_setting:
            flash('Virheellinen vaikeustaso')
            return render_template('edit_template.html', template=template, children=children, difficulty_settings=DifficultySetting.query.order_by(DifficultySetting.points.asc()).all())
        
        template.points = difficulty_setting.points
        template.difficulty = difficulty
        
        # Always available
        template.always_available = request.form.get('always_available') == 'on'
        
        # Assigned children logic
        assign_all = request.form.get('assign_all') == 'on'
        assigned_children = request.form.getlist('assigned_children')
        if assign_all or not assigned_children:
            template.assigned_children = None
        else:
            template.assigned_children = ','.join(assigned_children)
        
        # Due date is not typically part of a template, so we skip it
        
        db.session.commit()
        log_action(f'Parent edited task template: {template.title}')
        flash('Tehtäväpohja päivitetty onnistuneesti!')
        return redirect(url_for('parent_dashboard'))
    
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    return render_template('edit_template.html', template=template, children=children, difficulty_settings=difficulty_settings)

@app.route('/parent/tasks/create_from_template/<int:template_id>', methods=['POST'])
def create_task_from_template(template_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    template = TaskTemplate.query.get_or_404(template_id)
    
    always_available = request.form.get('always_available') == 'on'
    assign_all = request.form.get('assign_all') == 'on'
    assigned_children = request.form.getlist('assigned_children')
    due_date_str = request.form.get('due_date')
    
    due_date = None
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    
    # Convert assigned_children list to comma-separated string
    # If "assign all" is checked, don't assign to specific children (None)
    # If individual children are selected, use those
    assigned_children_str = None
    if not assign_all and assigned_children:
        assigned_children_str = ','.join(assigned_children)
    
    task = Task(
        title=template.title,
        description=template.description,
        points=template.points,
        difficulty=template.difficulty,
        due_date=due_date,
        always_available=always_available,
        assigned_children=assigned_children_str,
        template_id=template.id
    )
    
    db.session.add(task)
    db.session.commit()
    log_action(f'Parent created task from template: {template.title}')
    flash('Tehtävä luotu tehtäväpohjasta onnistuneesti!')
    return redirect(url_for('parent_dashboard'))

@app.route('/parent/tasks/<int:task_id>/toggle_always_available')
def toggle_always_available(task_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    task.always_available = not task.always_available
    db.session.commit()
    
    status = "toistuva" if task.always_available else "kertatyö"
    log_action(f'Parent toggled always_available for task: {task.title} (now: {task.always_available})')
    flash(f'Tehtävä on nyt {status}!')
    return redirect(url_for('parent_dashboard'))

@app.route('/parent/approvals')
def parent_approvals():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    # Get pending task completions
    pending_approvals = TaskCompletion.query.filter_by(approved_by_parent=False).order_by(TaskCompletion.completed_at.desc()).all()
    
    # Get pending reward purchases
    pending_reward_approvals = RewardPurchase.query.filter_by(approved_by_parent=False).order_by(RewardPurchase.purchased_at.desc()).all()
    
    # Get children for display
    children = User.query.filter_by(role='child').all()
    
    return render_template('approvals.html', 
                         pending_approvals=pending_approvals,
                         pending_reward_approvals=pending_reward_approvals,
                         children=children)

@app.route('/parent/approve/<int:completion_id>')
def approve_completion(completion_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    completion = TaskCompletion.query.get_or_404(completion_id)
    task = db.session.get(Task, completion.task_id)
    
    # Award points to the child
    child = db.session.get(User, completion.user_id)
    child.points += completion.points_earned
    
    # Mark as approved
    completion.approved_by_parent = True
    completion.approved_at = datetime.utcnow()
    completion.approved_by = session['user_id']
    
    # Mark task as completed
    task.status = 'completed'
    
    db.session.commit()
    log_action(f'Parent approved task completion: {task.title} for {child.username}')
    flash(f'Tehtävä hyväksytty! {child.username} sai {completion.points_earned} pistettä.')
    return redirect(url_for('parent_approvals'))

@app.route('/parent/reject/<int:completion_id>')
def reject_completion(completion_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    completion = TaskCompletion.query.get_or_404(completion_id)
    task = db.session.get(Task, completion.task_id)
    child = db.session.get(User, completion.user_id)
    
    # Reset task status to in_progress
    task.status = 'in_progress'
    task.completed_at = None
    
    # Delete the completion record
    db.session.delete(completion)
    db.session.commit()
    
    flash(f'Tehtävä hylätty! {child.username} ei saanut pisteitä.')
    return redirect(url_for('parent_approvals'))

@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Check if user role matches session role
    if session.get('role') != user.role:
        return jsonify({'error': 'Role mismatch'}), 401
    
    if user.role == 'parent':
        active_tasks = Task.query.filter(Task.status != 'completed').count()
        completed_tasks = Task.query.filter(Task.status == 'completed').count()
        pending_tasks = Task.query.filter(Task.status == 'in_progress').count()
        pending_task_approvals = TaskCompletion.query.filter_by(approved_by_parent=False).count()
        pending_reward_approvals = RewardPurchase.query.filter_by(approved_by_parent=False).count()
        pending_approvals = pending_task_approvals + pending_reward_approvals
        
        return jsonify({
            'total_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'pending_approvals': pending_approvals
        })
    else:
        completed_tasks = TaskCompletion.query.filter_by(user_id=user.id).count()
        total_points = user.points
        
        return jsonify({
            'completed_tasks': completed_tasks,
            'total_points': total_points
        })

@app.route('/parent/children/<int:child_id>/history')
def child_history(child_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    child = db.session.get(User, child_id)
    
    # Get all completions for this child
    completions = TaskCompletion.query.filter_by(
        user_id=child.id,
        approved_by_parent=True
    ).order_by(TaskCompletion.approved_at.desc()).all()
    
    # Get all reward purchases for this child
    reward_purchases = RewardPurchase.query.filter_by(
        user_id=child.id,
        approved_by_parent=True
    ).order_by(RewardPurchase.approved_at.desc()).all()
    
    # Calculate points by week and month
    from datetime import datetime, timedelta
    import calendar
    
    now = datetime.utcnow()
    
    # Weekly points (last 8 weeks)
    weekly_points = []
    for i in range(8):
        week_start = now - timedelta(weeks=i)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = week_start - timedelta(days=week_start.weekday())
        week_end = week_start + timedelta(days=7)
        
        week_completions = [c for c in completions if week_start <= c.approved_at < week_end]
        week_total = sum(c.points_earned for c in week_completions)
        
        weekly_points.append({
            'week_start': week_start,
            'week_end': week_end,
            'total': week_total,
            'completions': len(week_completions)
        })
    
    # Monthly points (last 12 months)
    monthly_points = []
    for i in range(12):
        month_start = now.replace(day=1) - timedelta(days=30*i)
        month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get last day of month
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        month_end = next_month - timedelta(days=1)
        
        month_completions = [c for c in completions if month_start <= c.approved_at <= month_end]
        month_total = sum(c.points_earned for c in month_completions)
        
        monthly_points.append({
            'month_start': month_start,
            'month_end': month_end,
            'total': month_total,
            'completions': len(month_completions)
        })
    
    # Get task statistics
    total_completions = len(completions)
    total_points = sum(c.points_earned for c in completions)
    average_points_per_task = total_points / total_completions if total_completions > 0 else 0
    
    # Get reward statistics
    total_reward_purchases = len(reward_purchases)
    total_points_spent = sum(p.points_spent for p in reward_purchases)
    
    # Get most common tasks
    task_counts = {}
    for completion in completions:
        task_title = completion.task.title
        task_counts[task_title] = task_counts.get(task_title, 0) + 1
    
    most_common_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Get difficulty settings for display
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    
    return render_template('child_history.html',
                         child=child,
                         completions=completions,
                         reward_purchases=reward_purchases,
                         weekly_points=weekly_points,
                         monthly_points=monthly_points,
                         total_completions=total_completions,
                         total_points=total_points,
                         total_reward_purchases=total_reward_purchases,
                         total_points_spent=total_points_spent,
                         average_points_per_task=average_points_per_task,
                         most_common_tasks=most_common_tasks,
                         difficulty_settings=difficulty_settings)

@app.route('/parent/children/<int:child_id>/history/remove_completion/<int:completion_id>')
def remove_completion(child_id, completion_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    completion = TaskCompletion.query.get_or_404(completion_id)
    task = db.session.get(Task, completion.task_id)
    
    # Verify the completion belongs to the child
    if completion.user_id != child_id:
        flash('Virheellinen tehtävävalmistus')
        return redirect(url_for('child_history', child_id=child_id))
    
    task = db.session.get(Task, completion.task_id)
    
    # Remove points from child
    child = db.session.get(User, completion.user_id)
    child.points -= completion.points_earned
    if child.points < 0:
        child.points = 0
    
    # Delete the completion record
    db.session.delete(completion)
    db.session.commit()
    
    log_action(f'Parent removed task completion: {task.title} for {child.username}')
    flash(f'Tehtävävalmistus poistettu! {child.username} menetti {completion.points_earned} pistettä.')
    return redirect(url_for('child_history', child_id=child_id))

@app.route('/parent/children/<int:child_id>/history/remove_all_completions')
def remove_all_completions(child_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    child = db.session.get(User, child_id)
    if not child or child.role != 'child':
        flash('Virheellinen lapsi')
        return redirect(url_for('parent_dashboard'))
    
    # Get all task completions for this child
    task_completions = TaskCompletion.query.filter(
        TaskCompletion.user_id == child.id,
        TaskCompletion.approved_by_parent == True
    ).all()
    
    # Get all reward purchases for this child
    reward_purchases = RewardPurchase.query.filter(
        RewardPurchase.user_id == child.id,
        RewardPurchase.approved_by_parent == True
    ).all()
    
    if not task_completions and not reward_purchases:
        flash('Ei poistettavia tietoja')
        return redirect(url_for('child_history', child_id=child_id))
    
    # Calculate total points to remove from task completions
    total_task_points_removed = sum(c.points_earned for c in task_completions)
    
    # Calculate total points spent on rewards
    total_reward_points_spent = sum(p.points_spent for p in reward_purchases)
    
    # Reset child's points to 0
    child.points = 0
    
    # Delete all task completion records
    for completion in task_completions:
        db.session.delete(completion)
    
    # Delete all reward purchase records
    for purchase in reward_purchases:
        db.session.delete(purchase)
    
    db.session.commit()
    
    log_action(f'Parent removed all completions and purchases for child: {child.username}')
    flash(f'Kaikki historia poistettu! {child.username} menetti {total_task_points_removed} pistettä tehtävistä ja {total_reward_points_spent} pistettä palkinnoista. Pisteet nollattu.')
    return redirect(url_for('child_history', child_id=child_id))

# Reward Management Routes
@app.route('/parent/rewards')
def manage_rewards():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    rewards = Reward.query.order_by(Reward.title.asc()).all()
    return render_template('manage_rewards.html', rewards=rewards)

@app.route('/parent/rewards/create', methods=['GET', 'POST'])
def create_reward():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        points_cost = int(request.form['points_cost'])
        assigned_children = request.form.getlist('assigned_children')
        
        # Convert assigned_children list to comma-separated string
        assigned_children_str = ','.join(assigned_children) if assigned_children else None
        
        reward = Reward(
            title=title,
            description=description,
            points_cost=points_cost,
            assigned_children=assigned_children_str
        )
        
        db.session.add(reward)
        db.session.commit()
        log_action(f'Parent created reward: {title}')
        flash('Palkinto luotu onnistuneesti!')
        return redirect(url_for('parent_dashboard'))
    
    children = User.query.filter_by(role='child').all()
    return render_template('create_reward.html', children=children)

@app.route('/parent/rewards/<int:reward_id>/edit', methods=['GET', 'POST'])
def edit_reward(reward_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    reward = Reward.query.get_or_404(reward_id)
    
    if request.method == 'POST':
        reward.title = request.form['title']
        reward.description = request.form['description']
        reward.points_cost = int(request.form['points_cost'])
        assigned_children = request.form.getlist('assigned_children')
        reward.assigned_children = ','.join(assigned_children) if assigned_children else None
        db.session.commit()
        log_action(f'Parent edited reward: {reward.title}')
        flash('Palkinto päivitetty onnistuneesti!')
        return redirect(url_for('manage_rewards'))
    
    children = User.query.filter_by(role='child').all()
    return render_template('edit_reward.html', reward=reward, children=children)

@app.route('/parent/rewards/<int:reward_id>/delete')
def delete_reward(reward_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    reward = Reward.query.get_or_404(reward_id)
    
    db.session.delete(reward)
    db.session.commit()
    log_action(f'Parent deleted reward: {reward.title}')
    flash('Palkinto poistettu onnistuneesti!')
    return redirect(url_for('manage_rewards'))

@app.route('/parent/rewards/<int:reward_id>/toggle')
def toggle_reward(reward_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    reward = Reward.query.get_or_404(reward_id)
    reward.is_active = not reward.is_active
    db.session.commit()
    status = "aktiivinen" if reward.is_active else "ei aktiivinen"
    log_action(f'Parent toggled reward active: {reward.title} (now: {reward.is_active})')
    flash(f'Palkinto on nyt {status}!')
    return redirect(url_for('manage_rewards'))

@app.route('/child/rewards')
def child_rewards():
    if 'user_id' not in session or session['role'] != 'child':
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    # Get all active rewards
    all_rewards = Reward.query.filter(
        Reward.is_active == True
    ).all()
    
    # Filter rewards based on assignment
    available_rewards = []
    for reward in all_rewards:
        # Check if reward is assigned to this child (or no specific assignment)
        is_assigned = True
        if reward.assigned_children:
            assigned_child_ids = [int(x.strip()) for x in reward.assigned_children.split(',') if x.strip()]
            if user.id not in assigned_child_ids:
                is_assigned = False
        
        if is_assigned and user.points >= reward.points_cost:
            available_rewards.append(reward)
    
    # Sort rewards alphabetically
    available_rewards.sort(key=lambda x: x.title)
    
    return render_template('child_rewards.html', rewards=available_rewards, user=user)

@app.route('/child/rewards/<int:reward_id>/purchase')
def purchase_reward(reward_id):
    if 'user_id' not in session or session['role'] != 'child':
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    reward = Reward.query.get_or_404(reward_id)
    
    if not reward.is_active:
        flash('Tämä palkinto ei ole enää saatavilla')
        return redirect(url_for('child_rewards'))
    
    if user.points < reward.points_cost:
        flash(f'Sinulla ei ole tarpeeksi pisteitä. Tarvitset {reward.points_cost} pistettä.')
        return redirect(url_for('child_rewards'))
    
    # Check if there's already a pending purchase for this reward by this user
    existing_purchase = RewardPurchase.query.filter_by(
        reward_id=reward.id,
        user_id=user.id,
        approved_by_parent=False
    ).first()
    
    if existing_purchase:
        flash('Olet jo pyytänyt tätä palkintoa. Odota vanhemman hyväksyntää.')
        return redirect(url_for('child_rewards'))
    
    # Create purchase record (pending approval)
    purchase = RewardPurchase(
        reward_id=reward.id,
        user_id=user.id,
        points_spent=reward.points_cost
    )
    
    db.session.add(purchase)
    db.session.commit()
    
    flash(f'Palkintopyyntö lähetetty! Vanhempi hyväksyy pyynnön pian.')
    return redirect(url_for('child_rewards'))

@app.route('/parent/approve_reward/<int:purchase_id>')
def approve_reward_purchase(purchase_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    purchase = RewardPurchase.query.get_or_404(purchase_id)
    reward = db.session.get(Reward, purchase.reward_id)
    child = db.session.get(User, purchase.user_id)
    
    # Deduct points from child's account
    child.points -= purchase.points_spent
    if child.points < 0:
        child.points = 0
    
    # Mark as approved
    purchase.approved_by_parent = True
    purchase.approved_at = datetime.utcnow()
    purchase.approved_by = session['user_id']
    db.session.commit()
    log_action(f'Parent approved reward purchase: {reward.title} for {child.username}')
    flash(f'Palkinto hyväksytty! {child.username} sai palkinnon: {reward.title}')
    return redirect(url_for('parent_approvals'))

@app.route('/parent/reject_reward/<int:purchase_id>')
def reject_reward_purchase(purchase_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    purchase = RewardPurchase.query.get_or_404(purchase_id)
    reward = db.session.get(Reward, purchase.reward_id)
    child = db.session.get(User, purchase.user_id)
    
    # Delete the purchase record
    db.session.delete(purchase)
    db.session.commit()
    log_action(f'Parent rejected reward purchase: {reward.title} for {child.username}')
    flash(f'Palkintopyyntö hylätty! {child.username} ei saanut palkintoa.')
    return redirect(url_for('parent_approvals'))

@app.route('/parent/children/<int:child_id>/edit_points', methods=['GET', 'POST'])
def edit_child_points(child_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    child = User.query.get_or_404(child_id)
    
    if request.method == 'POST':
        try:
            new_points = int(request.form['points'])
            if new_points < 0:
                new_points = 0
            
            # Calculate the difference for logging
            points_difference = new_points - child.points
            
            # Update the child's points
            child.points = new_points
            db.session.commit()
            log_action(f'Parent edited points for child: {child.username} (new points: {new_points})')
            
            if points_difference > 0:
                flash(f'{child.username} sai {points_difference} lisäpistettä. Uusi saldo: {new_points} pistettä.')
            elif points_difference < 0:
                flash(f'{child.username} menetti {abs(points_difference)} pistettä. Uusi saldo: {new_points} pistettä.')
            else:
                flash(f'{child.username} pisteet pysyivät ennallaan: {new_points} pistettä.')
            
            return redirect(url_for('manage_children'))
            
        except ValueError:
            flash('Virheellinen pistemäärä. Syötä kokonaisluku.')
            return render_template('edit_child_points.html', child=child)
    
    return render_template('edit_child_points.html', child=child)

@app.route('/parent/difficulty_settings')
def manage_difficulty_settings():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    difficulty_settings = DifficultySetting.query.order_by(DifficultySetting.points.asc()).all()
    return render_template('manage_difficulty_settings.html', difficulty_settings=difficulty_settings)

@app.route('/parent/difficulty_settings/create', methods=['GET', 'POST'])
def create_difficulty_setting():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        display_name = request.form['display_name']
        points = int(request.form['points'])
        color = request.form['color']
        
        # Check if name already exists
        if DifficultySetting.query.filter_by(name=name).first():
            flash('Vaikeustason nimi on jo olemassa')
            return render_template('create_difficulty_setting.html')
        
        difficulty_setting = DifficultySetting(
            name=name,
            display_name=display_name,
            points=points,
            color=color
        )
        
        db.session.add(difficulty_setting)
        db.session.commit()
        log_action(f'Parent created difficulty setting: {name}')
        flash('Vaikeustaso luotu onnistuneesti!')
        return redirect(url_for('manage_difficulty_settings'))
    
    return render_template('create_difficulty_setting.html')

@app.route('/parent/difficulty_settings/<int:setting_id>/edit', methods=['GET', 'POST'])
def edit_difficulty_setting(setting_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    difficulty_setting = DifficultySetting.query.get_or_404(setting_id)
    
    if request.method == 'POST':
        difficulty_setting.display_name = request.form['display_name']
        difficulty_setting.points = int(request.form['points'])
        difficulty_setting.color = request.form['color']
        
        db.session.commit()
        log_action(f'Parent edited difficulty setting: {difficulty_setting.name}')
        flash('Vaikeustaso päivitetty onnistuneesti!')
        return redirect(url_for('manage_difficulty_settings'))
    
    return render_template('edit_difficulty_setting.html', difficulty_setting=difficulty_setting)

@app.route('/parent/difficulty_settings/<int:setting_id>/delete')
def delete_difficulty_setting(setting_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    
    difficulty_setting = DifficultySetting.query.get_or_404(setting_id)
    
    # Check if this difficulty is used in any tasks or templates
    tasks_using = Task.query.filter_by(difficulty=difficulty_setting.name).count()
    templates_using = TaskTemplate.query.filter_by(difficulty=difficulty_setting.name).count()
    
    if tasks_using > 0 or templates_using > 0:
        flash(f'Vaikeustasoa ei voi poistaa, koska sitä käytetään {tasks_using + templates_using} tehtävässä.')
        return redirect(url_for('manage_difficulty_settings'))
    
    db.session.delete(difficulty_setting)
    db.session.commit()
    log_action(f'Parent deleted difficulty setting: {difficulty_setting.name}')
    flash('Vaikeustaso poistettu onnistuneesti!')
    return redirect(url_for('manage_difficulty_settings'))

@app.route('/parent/audit_log')
def view_audit_log():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('audit_log.html', logs=logs)

@app.route('/parent/audit_log/download')
def download_audit_log():
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'User ID', 'Username', 'Action', 'IP Address', 'User Agent'])
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user_id,
            log.username,
            log.action,
            log.ip_address,
            log.user_agent
        ])
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=audit_log.csv'})

@app.route('/parent/children/<int:child_id>/delete', methods=['GET', 'POST'])
def delete_child(child_id):
    if 'user_id' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))
    child = User.query.get_or_404(child_id)
    if child.role != 'child':
        flash('Vain lapsen tilejä voi poistaa.')
        return redirect(url_for('manage_children'))
    if request.method == 'POST':
        confirm_name = request.form.get('confirm_name', '').strip()
        if confirm_name != child.username:
            flash('Nimi ei täsmää. Poisto peruttu.')
            return render_template('confirm_delete_child.html', child=child)
        # Delete all task completions for this child
        TaskCompletion.query.filter_by(user_id=child.id).delete()
        # Delete all reward purchases for this child
        RewardPurchase.query.filter_by(user_id=child.id).delete()
        # Delete the child
        db.session.delete(child)
        db.session.commit()
        log_action(f'Parent deleted child: {child.username}')
        flash(f'Lapsi {child.username} ja kaikki siihen liittyvä historia on poistettu.')
        return redirect(url_for('manage_children'))
    # GET: show confirmation form
    return render_template('confirm_delete_child.html', child=child)

@app.route('/child/tasks/<int:task_id>/cancel')
def cancel_task(task_id):
    if 'user_id' not in session or session['role'] != 'child':
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != session['user_id'] or task.status != 'in_progress':
        flash('Voit perua vain sinulle annettuja ja kesken olevia tehtäviä')
        return redirect(url_for('child_dashboard'))
    
    if task.always_available:
        # For always_available tasks, delete this instance since the original is still available
        db.session.delete(task)
        db.session.commit()
        flash('Tehtävä peruttu! Toistuva tehtävä on edelleen saatavilla.')
    else:
        # For regular tasks, make them available again
        task.status = 'available'
        task.assigned_to = None
        task.completed_at = None
        db.session.commit()
        flash('Tehtävä peruttu! Tehtävä on nyt taas saatavilla.')
    
    log_action(f'Child {session["username"]} cancelled task: {task.title}')
    return redirect(url_for('child_dashboard'))

def log_action(action):
    from flask import request, session
    user_id = session.get('user_id')
    username = session.get('username')
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(log)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=8080, debug=True) 