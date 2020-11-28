import os
from flask import Flask, request, abort, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random
import sys
from models import setup_db, Question, Category, db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object('config')
    setup_db(app)

    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    # CORS Headers

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,PATCH,DELETE,OPTIONS')
        return response

    # the frontend excepts this route to return only an array of categories names, no ids.

    @app.route('/categories')
    def get_all_categories():

        categories = get_categories_names_list()

        if len(categories) == 0:

            abort(404)

        return jsonify({
            "categories": categories
        })

    @app.route('/questions')
    def get_or_search_questions():

        # i made the frontend call this route to search questions so checking if its either a specific question search call or getting all questions call
        # if it the get request has json body that means its a search
        searchArg = request.args.get('search', default=None, type=str)

        if searchArg != None:

            return search_questions(searchArg)

        else:

            return get_questions()

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        notFound = False
        try:
            question = Question.query.get(question_id)

            if question == None:
                # apparently i can't simply abort here because abort() still raises an exception, so for now i'm setting a notFound boolean to true

                notFound = True
                abort(404)
                flash("Question doesn't exist!")
            else:
                question.delete()
                flash("Question deleted!")
        except:

            db.session.rollback()
            print(sys.exc_info())
            if notFound:
                abort(404)
            else:
                abort(500)
            flash("Question not deleted!")

        finally:
            db.session.close()

        return jsonify({'success': True})

    @app.route('/questions', methods=['POST'])
    def add_question():

        question_form = request.get_json()
        # category id is incremented by 1 because on the front end category is an array of string and its index/id starts at 0
        category_id = int(question_form.get('category')) + 1
        try:
            new_question = Question(question=question_form.get('question'), answer=question_form.get('answer'),
                                    difficulty=question_form.get('difficulty'), category_id=category_id)

            new_question.insert()
            id = new_question.id

        except:
            abort(422)
            print(sys.exc_info())

        finally:
            db.session.close()

        # i'm returning id for testing purposes
        return {"success": True,
                "id": new_question.id}

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_in_category(category_id):

        # on the frontend, categories is an array of strings of categories types and its index(id) starts at 0,
        # so i increment the id by one before fetching from my db to get the correct result.

        current_category = Category.query.get(category_id+1)

        if current_category == None:
            abort(404)

        questions_by_category = current_category.questions

        if questions_by_category == None or len(questions_by_category) == 0:
            abort(404)

        # on the frontend pagination links reset sort, so i dont paginate results here for now.
        formatted_questions = format_questions(questions_by_category)

        return jsonify({
            "questions": formatted_questions,
            "totalQuestions": len(questions_by_category),
            "currentCategory": current_category.type
        })

    @app.route('/quizzes', methods=['POST'])
    def quizzes():

        # a function that returns a random question that isn't equal to the prev one
        # this could be done programatically, by first getting count() of all questions in a category, then generating a random question id that is <= to qs count and != the prev question id
        # or can be done via sql with an ORDER_BY random() limit 1 statement.

        previous_question_id = 0
        previous_question = request.get_json().get('previous_questions')

        if len(previous_question) > 0:
            previous_question_id = previous_question[0]

        # if selected category type is 'clicked' that means all categories is chosen
        selected_category = request.get_json().get('quiz_category')

        if selected_category.get('type') == 'click':
            question = Question.query.filter(Question.id != previous_question_id).order_by(
                func.random()).limit(1).first()

        else:

            selected_category_id = int(selected_category.get('id')) + 1
            question = Question.query.filter(Question.id != previous_question_id, Question.category_id ==
                                             selected_category_id).order_by(func.random()).limit(1).first()

        if question == None:
            abort(404)

        return jsonify({
            "question": question.format()
        })

    @app.errorhandler(400)
    def bad_request(error):

        return jsonify({
            "success": False,
            "error": 400,
            "message": 'Error, bad request!'
        }), 400

    @app.errorhandler(404)
    def not_found(error):

        return jsonify({
            "success": False,
            "error": 404,
            "message": 'no data found!'
        }), 404

    @app.errorhandler(422)
    def Unprocessable(error):

        return jsonify({
            "success": False,
            "error": 422,
            "message": 'Error Unprocessable entity!'
        }), 422

    @app.errorhandler(500)
    def server_error(error):

        return jsonify({
            "success": False,
            "error": 500,
            "message": 'Server error!'
        }), 500

    return app

###############################


def get_questions():

    all_questions = Question.query.all()

    paginated_questions = paginate_questions(
        request, all_questions, 10)

    if paginated_questions == None:

        abort(404)

    return jsonify({
        "questions": paginated_questions,
        "total_questions": len(all_questions),
        "categories": get_categories_names_list(),
        "currentCategory": None
    })


def search_questions(search_term):

    search_results = Question.query.filter(
        Question.question.ilike('%' + search_term + '%')).all()

    if search_results == None:
        # returning an empty results list instead of aborting
        return jsonify({
            "questions": []
        })

    # on the frontend pagination links reset search, so i dont paginate results here for now.
    formatted_search_results = format_questions(search_results)

    return jsonify({
        "questions": formatted_search_results,
        # i'm not sure if the frontend needs the total of all questions here or total of questions returned from search.
        "total_questions": len(search_results),
        "currentCategory": None
    })


def paginate_questions(request, questions, questions_per_page):

    page_num = request.args.get('page', 1, type=int)
    start = (page_num - 1) * questions_per_page
    end = start + questions_per_page

    # if questions is empty or the pagination page_num argument is out of index return none
    if len(questions) == 0 or start >= len(questions):
        return None

    return format_questions(questions)[start: end]


def format_questions(questions):

    formatted_questions = [question.format() for question in questions]

    return formatted_questions


# apparently the frontend only wants an array of categories names which is fucking retarded
def get_categories_names_list():
    categories = Category.query.all()
    if len(categories):
        # list of strings of categories names
        return [cat.type for cat in categories]
    else:
        return []
