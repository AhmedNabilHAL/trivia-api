import os
import sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  cors = CORS(app, resources={r"/*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

  @app.route("/categories")
  def get_categories():
    categories = Category.query.order_by(Category.id).all()
    categories = [category.type for category in categories]

    if (len(categories) == 0):
      abort(404)

    return jsonify({
      "success": True,
      "categories": categories
    })

  def paginate(request, selection, per_page):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * per_page
    end = start + per_page
    
    entries = [entry.format() for entry in selection]
    current_entries = entries[start:end]
    return current_entries

  @app.route("/questions")
  def get_questions():
    questions = Question.query.order_by(Question.id).all()
    total_questions = len(questions)

    categories = Category.query.order_by(Category.id).all()
    categories = [category.type for category in categories]

    current_questions = paginate(request, questions, QUESTIONS_PER_PAGE)
    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": total_questions,
      "current_category": "all",
      "categories": categories
    })

  @app.route("/questions/<int:question_id>", methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)
    if question is None:
      abort(404)

    question.delete()
    question = question.format()
    
    return jsonify({
      **question,
      "success": True
    })

  @app.route("/questions", methods=['POST'])
  def create_question():
    body = request.get_json()
    if body is None:
      abort(400)

    question = body.get("question", None)
    answer = body.get("answer", None)
    difficulty = body.get("difficulty", None)
    category = body.get("category", None)

    if question is None or answer is None or difficulty is None or category is None or \
      type(question) is not str or type(answer) is not str or type(difficulty) is not int or type(category) is not str or \
        Question.query.filter(Question.question==question).count() != 0:
      abort(400)

    category = int(category) + 1

    question = Question(question, answer, category, difficulty)
    question.insert()

    return jsonify({
      **question.format(),
      "success": True
    })

  @app.route("/questions/search", methods=['POST'])
  def search_questions():
    body = request.get_json()
    if body is None:
      abort(400)
    search_term = body.get("search")
    if search_term is None:
      abort(400)

    questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).order_by(Question.id).all()
    current_questions = paginate(request, questions, QUESTIONS_PER_PAGE)
    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": len(questions)
    })

  @app.route("/categories/<int:category_id>/questions", methods=['GET'])
  def get_questions_in_category(category_id):
    category_id = category_id + 1
    questions = Question.query.filter(Question.category==category_id).order_by(Question.id).all()
    total_questions = len(questions)

    current_questions = paginate(request, questions, QUESTIONS_PER_PAGE)
    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      "success": True,
      "questions": current_questions,
      "current_category": Category.query.get(category_id).type,
      "total_questions": total_questions
    })
  
  @app.route("/quizzes", methods=['POST'])
  def get_quiz():
    body = request.get_json()
    if body is None: 
      abort(400)

    quiz_category = body.get("quiz_category", None)
    previous_questions = body.get("previous_questions", [])
    if quiz_category is None:
      abort(400)
      
    available_questions = []
    current_question = None
    if quiz_category["type"] == "click":
      available_questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
    else:
      available_questions = Question.query.filter(Question.category==int(quiz_category["id"])+1, Question.id.notin_(previous_questions)).all()

    if len(available_questions) >1:
      current_question = random.sample(available_questions, 1)[0].format()

    return jsonify({
      "success": True,
      "questions": current_question,
      "category": quiz_category["type"],
      "total_questions": len(available_questions),
      "question": current_question
    })

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": "resource not found"
    }), 404

  @app.errorhandler(422)
  def not_found(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": "unprocessable Entity"
    }), 422

  @app.errorhandler(400)
  def not_found(error):
    return jsonify({
        "success": False, 
        "error": 400,
        "message": "bad request"
    }), 400

  @app.errorhandler(405)
  def not_found(error):
    return jsonify({
        "success": False, 
        "error": 405,
        "message": "method not allowed"
    }), 405

  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
        "success": False, 
        "error": 500,
        "message": "internal server error"
    }), 500
  
  return app