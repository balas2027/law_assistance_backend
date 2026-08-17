from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QuizAnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None


class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    status: str
    score: int
    correct_answers: int
    wrong_answers: int
    accuracy_pct: Optional[float] = None
    xp_earned: int
    time_taken_sec: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuizCompleteOut(QuizAttemptOut):
    total_questions: int = 0
    streak: int = 0
    longest_streak: int = 0
    total_xp: int = 0
    level: int = 1
    passed: bool = False
    topic_mastery: Optional[dict] = None


class UserStatsOut(BaseModel):
    user_id: int
    total_xp: int
    level: int
    quizzes_taken: int
    quizzes_passed: int
    questions_answered: int
    questions_correct: int
    best_accuracy_pct: Optional[float] = None
    current_streak: int
    longest_streak: int

    model_config = ConfigDict(from_attributes=True)


class UserTopicProgressOut(BaseModel):
    topic_id: int
    topic_name: str
    quizzes_taken: int
    avg_accuracy_pct: Optional[float] = None
    xp_earned: int
    mastery_level: int

    model_config = ConfigDict(from_attributes=True)


class QuizAnalyticsOut(BaseModel):
    quiz_id: int
    quiz_title: str
    total_attempts: int
    attendees: int
    completions: int
    avg_score: Optional[float] = None
    avg_accuracy_pct: Optional[float] = None
    avg_time_sec: Optional[float] = None
    pass_rate_pct: Optional[float] = None
    per_question: List[dict] = []


class TopicAnalyticsOut(BaseModel):
    topic_id: int
    topic_name: str
    total_quizzes: int
    published_quizzes: int
    total_attempts: int
    attendees: int
    avg_accuracy_pct: Optional[float] = None