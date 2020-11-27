import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_test_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        setup_test_db(self.app)

        self.new_question = {
            'question': 'Whats my favorite name?',
            'answer': 'lmao lol haha lel lol blah',
            'difficulty': 3,
            'category': 2
        }
        self.wrong_question = {
            'question': 'what what why why ?',
            'answer': 'i will wet myself',
            'category': 2
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)

            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_gets_all_categories(self):
        res = self.client().get('/categories')
        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.get('categories')))

    # def test_gets_404_when_categories_empty(self):
    #     res = self.client().get('/categories')

        # self.assertEqual(res.status_code, 404)
        # assert pages are paginated

    def test_get_10_questions(self):

        res = self.client().get('/questions?page=1')

        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.get('questions')))
        self.assertEqual(len(data.get('questions')), 10)
        self.assertTrue(data.get('questions')[0].get('category') != None)

    def test_get_404_if_questions_not_found(self):
        res = self.client().get('/questions?page=404')

        self.assertEqual(res.status_code, 404)

    def test_new_questions_can_be_added(self):
        res = self.client().post("/questions", json=self.new_question)
        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data.get('success'))

    def test_questions_cant_get_added_with_missing_data(self):
        res = self.client().post("/questions", json=self.wrong_question)
        self.assertEqual(res.status_code, 422)

    def test_questions_can_be_deleted(self):

        # i post a new question (already tested) to the db then gets it id and pass it in the delete route
        new_question_id = str(json.loads(self.client().post(
            "/questions", json=self.new_question).data).get('id'))
        res = self.client().delete("/questions/" + new_question_id)
        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data.get('success'))

    def test_none_found_questions_deletes_requests_404(self):
        res = self.client().delete("/questions/5")
        self.assertEqual(res.status_code, 404)

    def test_questions_search(self):
        res = self.client().get("/questions?search=name")
        data = load_response_data(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.get('questions')))
        self.assertTrue("name" in data.get('questions')[0].get('question'))

    def test_sorting_by_category(self):
        # in the route function i increment the id.
        res = self.client().get("/categories/0/questions")
        data = load_response_data(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.get('questions')))
        self.assertEqual(data.get('questions')[0].get('category'), 1)

    def test_404_if_category_not_found(self):
        res = self.client().get("/categories/300/questions")

        self.assertEqual(res.status_code, 404)

    def test_quizz_returns_random_question_belonging_to_a_selected_category(self):
        res = self.client().post(
            "/quizzes", json={"previous_questions": [1], "quiz_category": {"id": "1", "type" : "whatever"}})

        data = load_response_data(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.get('question')))
        # assert new question isnt the same as the previous question
        self.assertTrue(data.get('question').get('id') != 2)

    def test_quizz_returns_random_question_belonging_to_all_category(self):
        #frontend sends category type clicked for all categories
        res = self.client().post(
            "/quizzes", json={"previous_questions": [1], "quiz_category": {"id": "1", "type" : "click"}})

        data = load_response_data(res)
        
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.get('question')))


    def test_quizz_not_found(self):
        res = self.client().post(
            "/quizzes", json={"previous_questions": [2], "quiz_category": {"id": "2222"}})

        self.assertEqual(res.status_code, 404)

def load_response_data(res):
    return json.loads(res.data)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
