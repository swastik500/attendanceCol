from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func
from datetime import date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'teacher', 'student']), name='valid_role'),
    )

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    classes = db.relationship('Class', backref='course', lazy=True, cascade='all, delete-orphan')

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    subjects = db.relationship('Subject', backref='class_rel', lazy=True, cascade='all, delete-orphan')
    __table_args__ = (
        UniqueConstraint('name', 'year', name='unique_class_year'),
    )

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id', ondelete='CASCADE'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    teacher = db.relationship('User', backref=db.backref('subjects', lazy=True, cascade='all, delete'))
    __table_args__ = (
        UniqueConstraint('name', 'class_id', name='unique_subject_per_class'),
    )

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    subject = db.relationship('Subject', backref='attendances', lazy=True)
    __table_args__ = (
        CheckConstraint(status.in_(['Present', 'Absent']), name='valid_status'),
        CheckConstraint(date <= func.current_date(), name='valid_date'),
        UniqueConstraint('student_id', 'subject_id', 'date', name='unique_attendance_record'),
    )

class LectureSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    subject = db.relationship('Subject', backref='schedules')
    class_rel = db.relationship('Class', backref='schedules')
    
    __table_args__ = (
        CheckConstraint(day_of_week.in_(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']), name='valid_day'),
        UniqueConstraint('subject_id', 'class_id', 'day_of_week', 'start_time', name='unique_lecture_schedule')
    )