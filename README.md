# README.md
# AI-Powered Personalized Learning System

A comprehensive Flask-based learning management system with AI-powered student assessment and personalized recommendations.

## Features

### For Students:
- **Initial Assessment Test**: Take an AI-analyzed assessment to determine your learning style
- **AI Classification**: Get classified as Fast, Average, or Slow learner
- **Personalized Quiz Recommendations**: Receive quiz suggestions based on weak topics
- **Study Notes**: Access recommended study materials
- **Performance Tracker**: Track progress with charts and detailed analytics
- **Dashboard**: View all activities and recommendations in one place

### For Admins:
- **Content Management**: Add/manage assessment questions, quiz questions, and study notes
- **Student Monitoring**: View all students and their learning profiles
- **Analytics Dashboard**: Track overall platform performance and topic-wise analysis
- **Learner Distribution**: View breakdown of student types

### AI Features:
- **Smart Assessment Analysis**: Analyzes accuracy, timing, and difficulty to classify learners
- **Recommendation Engine**: Suggests quizzes and notes based on weak topics
- **Performance Prediction**: Tracks improvement patterns
- **Adaptive Difficulty**: Recommends content matching learner type

## Installation

### 1. Install Python
Make sure you have Python 3.8+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

The application will start on `http://127.0.0.1:5000/`

### 4. Access the System
- **Home Page**: http://127.0.0.1:5000/
- **Login**: http://127.0.0.1:5000/login
- **Register**: http://127.0.0.1:5000/register

### Default Admin Credentials:
- Email: `admin@example.com`
- Password: `admin123`

## Database Structure

The system uses SQLite with the following tables:

### Users Table
- id, name, email, password_hash, role, learner_type, created_at

### Assessment Questions Table
- id, question_text, option_a, option_b, option_c, option_d, correct_answer, topic, difficulty

### Assessment Results Table
- id, student_id, score, total_questions, time_taken, topic_scores, completed_at

### Quiz Bank Table
- id, question_text, option_a, option_b, option_c, option_d, correct_answer, topic, difficulty, created_by

### Quiz Attempts Table
- id, student_id, topic, score, total_questions, difficulty, time_taken, completed_at

### Study Notes Table
- id, title, content, topic, difficulty, created_by, created_at

## Project Structure

```
ai-learning-system/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── learning_system.db              # SQLite database (auto-created)
├── templates/
│   ├── base.html                   # Base layout template
│   ├── index.html                  # Home page
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── student/
│   │   ├── dashboard.html          # Student dashboard
│   │   ├── assessment.html         # Assessment test page
│   │   ├── quiz.html               # Quiz taking page
│   │   ├── notes.html              # Study notes page
│   │   └── performance.html        # Performance tracker
│   └── admin/
│       ├── dashboard.html          # Admin dashboard
│       ├── assessment_questions.html
│       ├── quiz_questions.html
│       ├── notes.html
│       ├── students.html
│       └── analytics.html
└── README.md
```

## Usage Guide

### For Students:

1. **Register**: Create a student account
2. **Take Assessment**: Complete the initial assessment (20 questions)
3. **Get Classified**: AI analyzes your performance and classifies you
4. **View Dashboard**: See your learner type and recommendations
5. **Take Quizzes**: Practice with recommended quizzes
6. **Study Notes**: Access recommended study materials
7. **Track Progress**: Monitor improvement in performance tracker

### For Admins:

1. **Login**: Use admin credentials
2. **Add Questions**: Create assessment and quiz questions
3. **Add Notes**: Upload study materials
4. **Monitor Students**: View all students and their progress
5. **Analytics**: Check platform-wide performance metrics

## AI Classification Logic

The system classifies students based on:
- **Score Percentage**: Accuracy in answering questions
- **Time Taken**: Speed of completion
- **Topic Performance**: Strength in different subjects

### Classification Criteria:
- **Fast Learner**: Score ≥ 80% AND avg time < 30 seconds/question
- **Average Learner**: Score ≥ 60% AND avg time < 45 seconds/question
- **Slow Learner**: Otherwise

## Customization

### Topics
You can add any topics like:
- Mathematics
- Science
- English
- History
- Programming
- Physics
- Chemistry
etc.

### Difficulty Levels
- Easy
- Medium
- Hard

### Adding Sample Data

The system automatically adds sample assessment questions on first run. To add more:
1. Login as admin
2. Go to "Assessment Questions" or "Quiz Questions"
3. Fill the form and submit

## Troubleshooting

### Database Issues
If you encounter database errors, delete `learning_system.db` and restart the app. It will recreate the database.

### Port Already in Use
If port 5000 is busy, modify the last line in `app.py`:
```python
app.run(debug=True, port=5001)
```

### Missing Dependencies
Reinstall requirements:
```bash
pip install -r requirements.txt --force-reinstall
```

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Charts**: Chart.js
- **Icons**: Font Awesome
- **AI Logic**: Custom classification algorithm

## Security Notes

- Passwords are hashed using Werkzeug security
- Session management with Flask sessions
- Role-based access control (Student/Admin)
- CSRF protection enabled
- Input validation on all forms

## Future Enhancements

- File upload for PDFs
- Video lessons support
- Real-time chat between students
- Email notifications
- Certificate generation
- Mobile app version
- Advanced ML models for better classification
- Collaborative learning features

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments in app.py
3. Ensure all dependencies are installed correctly

## License

Free to use for educational purposes.

---

**Note**: This is a complete, production-ready learning management system with AI capabilities. All features work out of the box!