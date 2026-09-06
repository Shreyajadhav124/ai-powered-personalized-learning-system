import sqlite3
import string
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'admin'
    learner_type = db.Column(db.String(20))  # 'fast', 'average', 'slow'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('AssessmentResult', backref='student', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='student', lazy=True)
    sessions_created = db.relationship('LiveSession', backref='creator', lazy=True)

class LiveSession(db.Model):
    __tablename__ = 'live_sessions'
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    meeting_link = db.Column(db.String(300), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AssessmentQuestion(db.Model):
    __tablename__ = 'assessment_questions'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'easy', 'medium', 'hard'

class AssessmentResult(db.Model):
    __tablename__ = 'assessment_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer)  # in seconds
    topic_scores = db.Column(db.Text)  # JSON string
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizBank(db.Model):
    __tablename__ = 'quiz_bank'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    time_taken = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudyNote(db.Model):
    __tablename__ = 'study_notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== AI ENGINE SIMULATION ====================

def analyze_assessment(student_id, answers, questions, time_taken):
    """Simulates AI analysis of assessment results"""
    correct_count = 0
    topic_performance = {}
    
    for i, answer in enumerate(answers):
        question = questions[i]
        topic = question.topic
        
        if topic not in topic_performance:
            topic_performance[topic] = {'correct': 0, 'total': 0}
        
        topic_performance[topic]['total'] += 1
        
        if answer == question.correct_answer:
            correct_count += 1
            topic_performance[topic]['correct'] += 1
    
    score_percentage = (correct_count / len(questions)) * 100
    avg_time_per_question = time_taken / len(questions)
    
    # AI Classification Logic
    if score_percentage >= 80 and avg_time_per_question < 30:
        learner_type = 'fast'
    elif score_percentage >= 60 and avg_time_per_question < 45:
        learner_type = 'average'
    else:
        learner_type = 'slow'
    
    # Calculate topic-wise accuracy
    topic_scores = {
        topic: (data['correct'] / data['total'] * 100) 
        for topic, data in topic_performance.items()
    }
    
    return {
        'learner_type': learner_type,
        'score': score_percentage,
        'topic_scores': topic_scores,
        'weak_topics': [topic for topic, score in topic_scores.items() if score < 60]
    }

def get_recommended_quizzes(student_id):
    """AI-based quiz recommendation"""
    student = User.query.get(student_id)
    
    # Get last assessment result
    last_assessment = AssessmentResult.query.filter_by(
        student_id=student_id
    ).order_by(AssessmentResult.completed_at.desc()).first()
    
    if not last_assessment:
        return []
    
    topic_scores = json.loads(last_assessment.topic_scores) if last_assessment.topic_scores else {}
    weak_topics = [topic for topic, score in topic_scores.items() if score < 60]
    
    # Recommend quizzes based on learner type and weak topics
    difficulty_map = {
        'fast': 'hard',
        'average': 'medium',
        'slow': 'easy'
    }
    
    recommended_difficulty = difficulty_map.get(student.learner_type, 'medium')
    
    recommendations = []
    for topic in weak_topics[:3]:  # Top 3 weak topics
        recommendations.append({
            'topic': topic,
            'difficulty': recommended_difficulty,
            'reason': f'Improve your {topic} skills'
        })
    
    return recommendations

def get_recommended_notes(student_id):
    """AI-based notes recommendation"""
    student = User.query.get(student_id)
    
    last_assessment = AssessmentResult.query.filter_by(
        student_id=student_id
    ).order_by(AssessmentResult.completed_at.desc()).first()
    
    if not last_assessment:
        return []
    
    topic_scores = json.loads(last_assessment.topic_scores) if last_assessment.topic_scores else {}
    weak_topics = [topic for topic, score in topic_scores.items() if score < 60]
    
    # Get notes for weak topics
    recommended_notes = StudyNote.query.filter(
        StudyNote.topic.in_(weak_topics)
    ).limit(5).all()
    
    return recommended_notes

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# ==================== STUDENT ROUTES ====================

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    student = User.query.get(session['user_id'])
    
    # Get assessment results
    assessments = AssessmentResult.query.filter_by(
        student_id=session['user_id']
    ).order_by(AssessmentResult.completed_at.desc()).all()
    
    # Get quiz attempts
    quizzes = QuizAttempt.query.filter_by(
        student_id=session['user_id']
    ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()
    
    # Get recommendations
    recommended_quizzes = get_recommended_quizzes(session['user_id'])
    recommended_notes = get_recommended_notes(session['user_id'])
    
    return render_template('student/dashboard.html',
                         student=student,
                         assessments=assessments,
                         quizzes=quizzes,
                         recommended_quizzes=recommended_quizzes,
                         recommended_notes=recommended_notes)

@app.route('/student/assessment/start')
def start_assessment():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    # Get 20 random assessment questions
    questions = AssessmentQuestion.query.order_by(db.func.random()).limit(20).all()
    
    if not questions:
        flash('No assessment questions available. Please contact admin.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    session['assessment_start_time'] = datetime.utcnow().timestamp()
    
    return render_template('student/assessment.html', questions=questions)

@app.route('/student/assessment/submit', methods=['POST'])
def submit_assessment():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    # Calculate time taken
    start_time = session.get('assessment_start_time')
    time_taken = int(datetime.utcnow().timestamp() - start_time) if start_time else 0
    
    # Get questions and answers
    question_ids = request.form.getlist('question_ids')
    questions = AssessmentQuestion.query.filter(
        AssessmentQuestion.id.in_(question_ids)
    ).all()
    
    answers = [request.form.get(f'answer_{qid}') for qid in question_ids]
    
    # AI Analysis
    analysis = analyze_assessment(session['user_id'], answers, questions, time_taken)
    
    # Update student learner type
    student = User.query.get(session['user_id'])
    student.learner_type = analysis['learner_type']
    
    # Save assessment result
    result = AssessmentResult(
        student_id=session['user_id'],
        score=analysis['score'],
        total_questions=len(questions),
        time_taken=time_taken,
        topic_scores=json.dumps(analysis['topic_scores'])
    )
    db.session.add(result)
    db.session.commit()
    
    flash(f'Assessment completed! You are classified as a {analysis["learner_type"]} learner.', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/quiz/<topic>/<difficulty>')
def take_quiz(topic, difficulty):
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    # Get 10 questions for the quiz
    questions = QuizBank.query.filter_by(
        topic=topic,
        difficulty=difficulty
    ).order_by(db.func.random()).limit(10).all()
    
    if not questions:
        flash('No questions available for this topic and difficulty.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    session['quiz_start_time'] = datetime.utcnow().timestamp()
    
    return render_template('student/quiz.html', 
                         questions=questions,
                         topic=topic,
                         difficulty=difficulty)

@app.route('/student/quiz/submit', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    start_time = session.get('quiz_start_time')
    time_taken = int(datetime.utcnow().timestamp() - start_time) if start_time else 0
    
    question_ids = request.form.getlist('question_ids')
    topic = request.form.get('topic')
    difficulty = request.form.get('difficulty')
    
    questions = QuizBank.query.filter(QuizBank.id.in_(question_ids)).all()
    
    correct_count = 0
    for question in questions:
        answer = request.form.get(f'answer_{question.id}')
        if answer == question.correct_answer:
            correct_count += 1
    
    score = (correct_count / len(questions)) * 100
    
    attempt = QuizAttempt(
        student_id=session['user_id'],
        topic=topic,
        score=score,
        total_questions=len(questions),
        difficulty=difficulty,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()
    
    flash(f'Quiz completed! Score: {score:.1f}%', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/notes')
def student_notes():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    # Get all notes
    notes = StudyNote.query.order_by(StudyNote.created_at.desc()).all()
    
    # Get recommended notes
    recommended_notes = get_recommended_notes(session['user_id'])
    
    return render_template('student/notes.html',
                         notes=notes,
                         recommended_notes=recommended_notes)

@app.route('/student/performance')
def student_performance():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('login'))
    
    student = User.query.get(session['user_id'])
    
    # Get all quiz attempts
    quiz_attempts = QuizAttempt.query.filter_by(
        student_id=session['user_id']
    ).order_by(QuizAttempt.completed_at).all()
    
    # Get assessment results
    assessments = AssessmentResult.query.filter_by(
        student_id=session['user_id']
    ).order_by(AssessmentResult.completed_at).all()
    
    return render_template('student/performance.html',
                         student=student,
                         quiz_attempts=quiz_attempts,
                         assessments=assessments)

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    # Get statistics
    total_students = User.query.filter_by(role='student').count()
    total_assessments = AssessmentQuestion.query.count()
    total_quizzes = QuizBank.query.count()
    total_notes = StudyNote.query.count()
    
    # Get learner distribution
    fast_learners = User.query.filter_by(role='student', learner_type='fast').count()
    avg_learners = User.query.filter_by(role='student', learner_type='average').count()
    slow_learners = User.query.filter_by(role='student', learner_type='slow').count()
    
    # Get recent students
    recent_students = User.query.filter_by(role='student').order_by(
        User.created_at.desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_assessments=total_assessments,
                         total_quizzes=total_quizzes,
                         total_notes=total_notes,
                         fast_learners=fast_learners,
                         avg_learners=avg_learners,
                         slow_learners=slow_learners,
                         recent_students=recent_students)

@app.route('/admin/assessment-questions', methods=['GET', 'POST'])
def manage_assessment_questions():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        question = AssessmentQuestion(
            question_text=request.form.get('question_text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            topic=request.form.get('topic'),
            difficulty=request.form.get('difficulty')
        )
        db.session.add(question)
        db.session.commit()
        flash('Assessment question added successfully!', 'success')
        return redirect(url_for('manage_assessment_questions'))
    
    questions = AssessmentQuestion.query.order_by(AssessmentQuestion.id.desc()).all()
    return render_template('admin/assessment_questions.html', questions=questions)

@app.route('/admin/quiz-questions', methods=['GET', 'POST'])
def manage_quiz_questions():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        question = QuizBank(
            question_text=request.form.get('question_text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            topic=request.form.get('topic'),
            difficulty=request.form.get('difficulty'),
            created_by=session['user_id']
        )
        db.session.add(question)
        db.session.commit()
        flash('Quiz question added successfully!', 'success')
        return redirect(url_for('manage_quiz_questions'))
    
    questions = QuizBank.query.order_by(QuizBank.id.desc()).all()
    return render_template('admin/quiz_questions.html', questions=questions)

@app.route('/admin/notes', methods=['GET', 'POST'])
def manage_notes():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        note = StudyNote(
            title=request.form.get('title'),
            content=request.form.get('content'),
            topic=request.form.get('topic'),
            difficulty=request.form.get('difficulty'),
            created_by=session['user_id']
        )
        db.session.add(note)
        db.session.commit()
        flash('Study note added successfully!', 'success')
        return redirect(url_for('manage_notes'))
    
    notes = StudyNote.query.order_by(StudyNote.created_at.desc()).all()
    return render_template('admin/notes.html', notes=notes)

@app.route('/admin/students')
def view_students():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    students = User.query.filter_by(role='student').order_by(User.created_at.desc()).all()
    return render_template('admin/students.html', students=students)

@app.route('/admin/analytics')
def admin_analytics():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    # Get all students performance data
    students = User.query.filter_by(role='student').all()
    
    # Topic-wise performance
    all_assessments = AssessmentResult.query.all()
    topic_performance = {}
    
    for assessment in all_assessments:
        if assessment.topic_scores:
            scores = json.loads(assessment.topic_scores)
            for topic, score in scores.items():
                if topic not in topic_performance:
                    topic_performance[topic] = []
                topic_performance[topic].append(score)
    
    # Calculate averages
    topic_averages = {
        topic: sum(scores) / len(scores)
        for topic, scores in topic_performance.items()
    }
    
    return render_template('admin/analytics.html',
                         students=students,
                         topic_averages=topic_averages)

@app.route('/admin/delete/<model>/<int:id>')
def admin_delete(model, id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))
    
    models_map = {
        'assessment': AssessmentQuestion,
        'quiz': QuizBank,
        'note': StudyNote
    }
    
    if model in models_map:
        item = models_map[model].query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        flash(f'{model.capitalize()} deleted successfully!', 'success')
    
    return redirect(request.referrer)

# ==================== INITIALIZE DATABASE ====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                name='Admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@example.com / admin123")
        
        # Add sample assessment questions if none exist
        if AssessmentQuestion.query.count() == 0:
            sample_questions = [
                # Math Questions
                AssessmentQuestion(
                    question_text="What is 15 × 12?",
                    option_a="150", option_b="180", option_c="200", option_d="165",
                    correct_answer="B", topic="Mathematics", difficulty="easy"
                ),
                AssessmentQuestion(
                    question_text="Solve: 2x + 5 = 15",
                    option_a="5", option_b="10", option_c="7", option_d="8",
                    correct_answer="A", topic="Mathematics", difficulty="medium"
                ),
                AssessmentQuestion(
                    question_text="What is the derivative of x²?",
                    option_a="x", option_b="2x", option_c="x²", option_d="2x²",
                    correct_answer="B", topic="Mathematics", difficulty="hard"
                ),
                
                # Science Questions
                AssessmentQuestion(
                    question_text="What is the chemical formula for water?",
                    option_a="H2O", option_b="CO2", option_c="O2", option_d="H2O2",
                    correct_answer="A", topic="Science", difficulty="easy"
                ),
                AssessmentQuestion(
                    question_text="What is Newton's second law of motion?",
                    option_a="F=ma", option_b="E=mc²", option_c="V=IR", option_d="PV=nRT",
                    correct_answer="A", topic="Science", difficulty="medium"
                ),
                
                # English Questions
                AssessmentQuestion(
                    question_text="What is the plural of 'child'?",
                    option_a="childs", option_b="children", option_c="childes", option_d="child's",
                    correct_answer="B", topic="English", difficulty="easy"
                ),
                AssessmentQuestion(
                    question_text="Identify the verb in: 'The cat runs quickly.'",
                    option_a="cat", option_b="runs", option_c="quickly", option_d="the",
                    correct_answer="B", topic="English", difficulty="medium"
                ),
            ]
            
            for q in sample_questions:
                db.session.add(q)
            
            db.session.commit()
            print(f"Added {len(sample_questions)} sample assessment questions")
            
@app.route('/student/ai-chat', methods=['GET'])
def chats():
    return render_template('student/ai_chat.html')

@app.route('/student/ai-chat', methods=['POST'])
def chat():
    
    
    data = request.json
    user_message = data.get('message', '')
    
    # Prepare Gemini API request
    gemini_payload = {
        "contents": [{
            "parts": [{
                "text": f"You are a helpful AI assistant specializing in Alzheimer's disease information. Please provide accurate, compassionate, and helpful information about: {user_message}"
            }]
        }],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.7,
            "topP": 0.8,
            "topK": 40
        }
    }
    
    # Call Gemini API
    response = request.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyD4cRNwk6qQfZgrrBu7pNsGdn2yo9kLiJQ',
        json=gemini_payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        result = response.json()
        ai_response = result['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'response': ai_response})
    else:
        return jsonify({'error': 'Failed to get AI response'}), 500


@app.route('/admin/live-sessions', methods=['GET', 'POST'])
def admin_live_sessions():
    if request.method == "POST":
        topic = request.form['topic']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']

        room_id = f"AIClass_{uuid.uuid4().hex[:8]}"
        meeting_link = f"https://meet.jit.si/{room_id}"

        new_session = LiveSession(
            topic=topic,
            description=description,
            date=date,
            time=time,
            meeting_link=meeting_link,
            created_by=session["user_id"]
        )
        db.session.add(new_session)
        db.session.commit()
        flash("Live session created successfully!", "success")
        return redirect(url_for("admin_live_sessions"))

    sessions = LiveSession.query.order_by(LiveSession.date.desc()).all()
    now = datetime.now()

    for s in sessions:
        # Convert date and time to datetime
        if isinstance(s.date, str):
            try:
                session_date = datetime.strptime(s.date, "%Y-%m-%d").date()
            except ValueError:
                session_date = datetime.strptime(s.date, "%d/%m/%Y").date()
        else:
            session_date = s.date

        if isinstance(s.time, str):
            try:
                session_time = datetime.strptime(s.time, "%H:%M").time()
            except ValueError:
                session_time = datetime.strptime(s.time, "%H:%M:%S").time()
        else:
            session_time = s.time

        session_datetime = datetime.combine(session_date, session_time)

        # Admin can join 10 minutes before and 2 hours after session start
        if now >= session_datetime - timedelta(minutes=10) and now <= session_datetime + timedelta(hours=2):
            s.join_available = True
        else:
            s.join_available = False

    return render_template("admin/admin_live_sessions.html", sessions=sessions)


# ---------- STUDENT: VIEW AVAILABLE LIVE SESSIONS ----------
@app.route('/student/live-sessions')
def student_live_sessions():
    sessions = LiveSession.query.order_by(LiveSession.date.desc()).all()
    now = datetime.now()

    for s in sessions:
        # Convert string date to date object if needed
        if isinstance(s.date, str):
            try:
                session_date = datetime.strptime(s.date, "%Y-%m-%d").date()
            except ValueError:
                session_date = datetime.strptime(s.date, "%d/%m/%Y").date()
        else:
            session_date = s.date

        # Convert string time to time object if needed
        if isinstance(s.time, str):
            try:
                session_time = datetime.strptime(s.time, "%H:%M").time()
            except ValueError:
                session_time = datetime.strptime(s.time, "%H:%M:%S").time()
        else:
            session_time = s.time

        session_datetime = datetime.combine(session_date, session_time)

        # Default flags
        s.join_available = False
        s.status = "Upcoming"

        # Define timing windows
        start_window = session_datetime - timedelta(minutes=10)
        end_window = session_datetime + timedelta(hours=1)
        missed_window = session_datetime + timedelta(minutes=30)

        # Ongoing: within start -10min and +1hr
        if start_window <= now <= end_window:
            s.join_available = True
            s.status = "Ongoing"

        # Missed: after 30 min of meeting start
        elif now > missed_window:
            s.status = "Missed"

        # Upcoming: before -10min of start
        else:
            s.status = "Upcoming"

    return render_template("student/student_live_sessions.html", sessions=sessions)
# ---------- JOIN SESSION (JITSI IFRAME) ----------
@app.route('/join/<room_name>')
def join_live(room_name):
    return render_template('join_live.html', room_name=room_name)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)