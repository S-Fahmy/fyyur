# **The trivia app!**

> ### A simple entertaining app where its main goal is for visitors to find and answer questions organized by varied categories, and play quick quiz games to show off their trivial knowledge, Users can also add new questions and categorize them.

The trivia app frontend design is a reactive design developed using react, communicating with the app backend api using REST.
---
## getting started and Project dependencies

the backend runs on python and the Flask framework and other libraries and dependencies:

- latest version of **python**
- Postgres db
- Flask framework
- SQLAlchemy
- Flask Cors

the backend folder contains a `requirements.txt` file with the dependencies that needs to get installed
to install the dependencies included in the file, navigate to the backend folder and run the following command:

```bash
pip install -r requirements.txt
```
After the dependencies successfully install follow along:

## Database Setup:
With Postgres running, restore a database using the trivia.psql file provided. From the backend folder in terminal run:
```bash
psql trivia < trivia.psql
```

## Running the application server:
head back to the Windows cmd and assign the __init__.py file in the backend to the FLASK_APP environment variable to be able to run the app

```bash
set FLASK_APP=__init__.py

flask run
```



---

# API Reference

> a detailed reference for all the available endpoints

**Note:**
For this reference the Question and Category models classes have a **format()** function that returns a dictionary that contains the entity data and ready for Json responses.

**`Formatted_question:`**

```
{
    'id': question.id,
    'question': question.question,
    'answer': question.answer,
    'category': question.category_id, #the front end expects a category value containing the category id.
    'difficulty': question.difficulty
}
```

## Endpoints:

**`GET localhost:5000/categories`**

> fetch all categories names from the database

- Request parameters: None
- Returns: a json response containing An array of strings, containing the categories names.

```
{
 "categories": ["category1" "category2", ...]
}
```

---

**`GET localhost:5000/questions`**

> fetch all questions from the database or search for specific questions

- Request parameters: possible search parameters
- Returns: 2 result based on a condition as explained below.

this route functions first check if the url contains an argument called 'search'; if true then it calls for the questions search function,
the **search function** returns a dictionary with a formatted questions results list, total questions and current category

```
{
 "questions": formatted_questions[],
 "total_questions": 92,
 "currentCategory": None
}
```

if the argument wasn't found then get_all_questions() is called, returning a json response containing a dictionary of: a list of questions, total questions, all categories and current category.
and the questions list is paginated, 10 questions per page is the default number.

```
{
 "questions": {
        'id': question.id,
        'question': question.question,
        'answer': question.answer,
        'category': question.category_id, #the front end expects a category value containing the category id.
        'difficulty': question.difficulty
                },
 "total_questions": len(all_questions),
 "categories": get_categories_names_list(),
 "currentCategory": None
}
```

---

**`DELETE localhost:5000/questions/<int:question_id>`**

> deletes a specific question via id

- Request parameters: question id
- Returns: a json response containing a success boolean.

```
{
 "success": True
}
```

---

**`POST localhost:5000/questions/`**

> Post a new question and persist it in the dB

- Request parameters: expects a json body that contains the questions data: question, answer, difficulty number and category id

```
{
   question: "question",
   answer: "answer,
   difficulty: 2,
   category: 1
 }
```

- Returns: a json response containing a success boolean and the new question entity id.

```
{
 "success": True,
 "id" : 14
}
```

---

**`GET localhost:5000/categories/<int:category_id>/questions`**

> sorts questions by categories

- Request parameters: None
- Returns: a json response containing a list of questions sorted by the selected category, total questions in that category, and current category name

```
{
  "questions": formatted_questions[],
  "totalQuestions": 11,
  "currentCategory": "selected_category_name"
 }
```

---

**`POST localhost:5000/quizzes`**

> starts a quiz game where the player tries to answer a specific number of questions in a row.

- Request parameters: None
- Returns: json body that contains a random formatted question dictionary that isn't equal to the previous question if found.

```
{
  "question": question.format()
 }
```

---
