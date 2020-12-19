import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, Question, Category

class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://postgres:postgres@{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        """Test getting categories"""
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["categories"]), 6)

    def test_get_questions(self):
        """Test getting questions"""
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["questions"])
        self.assertTrue(len(data["questions"]), QUESTIONS_PER_PAGE)
        self.assertTrue(data["total_questions"])

    def test_get_questions_404_request_beyond_valid_page(self):
        """Test getting questions from a beyond valid page"""
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "resource not found")

    def test_delete_question(self):
        """Test deleting a question"""
        question = Question("test question?", "answer", 1, 1)
        question.insert()
        qid = question.id
        question = Question.query.get(qid)
        self.assertIsNotNone(question)
        res = self.client().delete("/questions/{}".format(qid))
        data = json.loads(res.data)
        question = Question.query.get(qid)
        
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(question)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["answer"])
        self.assertTrue(data["category"])
        self.assertTrue(data["category_id"])
        self.assertTrue(data["difficulty"])
        self.assertTrue(data["answer"])
        self.assertEqual(data["id"], qid)

    def test_delete_question_not_exist(self):
        """Test deleting a question that doesn't exist"""
        res = self.client().delete("/questions/1000")
        data = json.loads(res.data)
        question = Question.query.get(1000)
        
        self.assertEqual(res.status_code, 404)
        self.assertIsNone(question)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "resource not found")

    def test_create_question(self):
        """Test creating a question"""
        res = self.client().post("/questions", json={

            "question": "test question?",
            "answer": "answer",
            "category": "1",
            "difficulty": 1
        })
        data = json.loads(res.data)
        question = Question.query.filter(Question.question == "test question?").first()

        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(question)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["answer"])
        self.assertEqual(data["category"].lower(), "art".lower())
        self.assertEqual(data["category_id"], 2)
        self.assertEqual(data["difficulty"], 1)
        self.assertTrue(data["answer"])
        self.assertEqual(data["id"], question.id)

    def test_create_question_bad_request(self):
        """Test deleting a question that doesn't exist"""
        res = self.client().post("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "bad request")

    def test_search_questions_found_results(self):
        """Test searching for a question and finding some results"""
        res = self.client().post("/questions/search", json={"search": "what"})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["questions"])
        self.assertTrue(data["total_questions"])

    def test_search_questions_without_results(self):
        """Test searching for a question without results"""
        res = self.client().post("/questions/search", json={"search": "abracadbrablabla"})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["questions"]), 0)
        self.assertEqual(data["total_questions"], 0)

    def test_search_questions_bad_request(self):
        """Test searching for a question without a body"""
        res = self.client().post("/questions/search")
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "bad request")

    def test_get_questions_in_category(self):
        """Test getting questions in a category"""
        res = self.client().get("/categories/0/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["questions"])
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["total_questions"])
        self.assertEqual(data["current_category"], "Science")

    def test_get_questions_in_category_404_request_beyond_valid_page(self):
        """Test getting questions from a beyond valid page"""
        res = self.client().get("/categories/100/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "resource not found")

    def test_get_quiz_category_all(self):
        """Test getting a quiz with category set to all"""
        res = self.client().post("/quizzes", json={"quiz_category": {"type": "all", "id": 0}})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["questions"]), 6)
        self.assertEqual(data["category"], "all")
        self.assertTrue(data["total_questions"])

    def test_get_quiz_category_history(self):
        """Test getting a quiz with category set to history"""
        res = self.client().post("/quizzes", json={"quiz_category": {"type": "history", "id": 0}})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertEqual(data["category"], "history")
        self.assertTrue(data["total_questions"])

    def test_get_quiz_category_history_with_previous_questions(self):
        """Test getting a quiz with category set to history and some previous questions exist"""
        res = self.client().post("/quizzes", json={
            "quiz_category": {"type": "history", "id": 0},
            "previous_questions": [5, 9, 23]})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["questions"]["id"], 12)
        self.assertEqual(data["category"], "history")
        self.assertTrue(data["total_questions"]) 

    def test_get_quiz_400_no_body(self):
        """Test getting a quiz with no body"""
        res = self.client().post("/quizzes")
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "resource not found")

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()