from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import re
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Your routes and functions will go here

@app.route('/')
def main_menu():
    return render_template('main_menu.html')
    
def init_db():
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT,
                  answers TEXT,
                  correct_answers TEXT)''')

    with open('questions.txt', 'r', encoding="UTF-8") as f:
        question = ''
        options = ''
        answer = ''
        for line in f:
            line = line.strip()
            if line.startswith('正确答案:'):
                answer = line.split(':')[1].strip()
                c.execute("INSERT INTO questions (question, answers, correct_answers) VALUES (?, ?, ?)",
                          (question, options, answer))
                question = ''
                options = ''
                answer = ''
            elif line.startswith('A.') or line.startswith('B.') or line.startswith('C.') or line.startswith('D.'):
                options += line + '\n'
            else:
                question += line + '\n'

    conn.commit()
    conn.close()

def get_random_question_ids(num_questions):
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.row_factory = sqlite3.Row
    c.execute('SELECT id FROM questions ORDER BY RANDOM() LIMIT ?', (num_questions,))
    question_ids = [row['id'] for row in c.fetchall()]
    conn.close()
    return question_ids
    
def get_question_by_id(question_id):
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.row_factory = sqlite3.Row
    c.execute('SELECT * FROM questions WHERE id=?', (question_id,))
    row = c.fetchone()
    conn.close()
    
    question = {
        'id': row['id'],
        'text': row['question'],
        'options': row['answers'].split('\n'),
        'correct_answer': row['correct_answers'],
        'question_type': 'multiple' if ' ' in row['correct_answers'] else 'single'
    }
    if question['options'][-1] == '':
        question['options'].pop(-1)
        
    
    #question['options'], question['correct_answer'] = shuffle_options_and_correct_answer(question['options'], question['correct_answer'])
    #print(list(question['options']),list(question['correct_answer']))

    return question

def shuffle_options_and_correct_answer(options, correct_answer):
    shuffled_options = []
    suffix_list = []
    prefix_list = []
    correct_answer_indices = []
    
    for option in options:    
        if '.' in option:
            prefix, suffix = option.split('.')
            prefix_list.append(prefix)
            suffix_list.append(suffix)
        else:
            shuffled_options.append(option)
    
    for ans in correct_answer.split(' '):
        ans_index = ord(ans) - ord('A')
        correct_answer_indices.append(ans_index)

    shuffled_indices = list(range(len(suffix_list)))
    random.shuffle(shuffled_indices)

    shuffled_correct_answer_indices = [shuffled_indices.index(ans_index) for ans_index in correct_answer_indices]
    shuffled_correct_answer = ' '.join(sorted(chr(ord('A') + ans_index) for ans_index in shuffled_correct_answer_indices))
    
    for i in range(len(suffix_list)):
        shuffled_suffix = suffix_list[shuffled_indices[i]]
        shuffled_option = prefix_list[i] + '.' + shuffled_suffix
        shuffled_options.append(shuffled_option)
        
    return shuffled_options, shuffled_correct_answer

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    num_questions = int(request.form['num_questions'])
    quiz_mode = request.form['quiz_mode']
    question_ids = get_random_question_ids(num_questions)
    session['question_ids'] = question_ids
    session['current_question'] = 0
    session['correct_answers'] = 0
    session['quiz_mode'] = quiz_mode
    session['show_result'] = quiz_mode == 'show_results_immediately'
    return redirect(url_for('display_question'))

#@app.template_filter('shuffle')
#def filter_shuffle(seq):
#    try:
#        result = list(seq)
#        random.shuffle(result)
#        return result
#    except Exception as e:
#    # Print the exception message
#        print(f"An exception occurred: {e}")
#        return seq

@app.route('/display_question')
def display_question():
    session.pop('submitted', None)
    if 'question_ids' not in session or session['current_question'] >= len(session['question_ids']):
        return redirect(url_for('main_menu'))

    question = get_question_by_id(session['question_ids'][session['current_question']])
    return render_template('question_view.html', question=question)

@app.route('/test_flash')
def test_flash():
    flash('This is a test flash message!', 'info')
    return redirect(url_for('main_menu'))


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    question_id = session['question_ids'][session['current_question']]
    question_data = get_question_by_id(question_id)
    
    user_answer = set(request.form.getlist('answer'))
    correct_answer = set(question_data['correct_answer'].split())
    correct = user_answer == correct_answer

    if correct:
        session['correct_answers'] += 1

    if session['quiz_mode'] == 'show_results_end':
        if session['current_question'] + 1 < len(session['question_ids']):
            session['current_question'] += 1
            return redirect(url_for('display_question'))
        else:
            return redirect(url_for('display_results'))
    else:
        if correct:
            flash('Correct!', 'success')
        else:
            flash(f"Incorrect! The correct answer is: {', '.join(correct_answer)}", 'error')
        
        session['submitted'] = True
        # Increment the current_question index in the session and check if there are more questions left
        if session['current_question'] + 1 < len(session['question_ids']):
            session['current_question'] += 1
            return redirect(url_for('display_question'))
        else:
            return redirect(url_for('display_results'))



@app.route('/display_results', methods=['GET'])
def display_results():
    total_questions = len(session['question_ids'])
    correct_answers = session['correct_answers']
    return render_template('results.html', total_questions=total_questions, correct_answers=correct_answers)

@app.route('/next_question')
def next_question():
    if session['current_question'] >= len(session['question_ids']):
        return redirect(url_for('display_results'))
    session['current_question'] += 1
    return redirect(url_for('display_question'))

 

init_db()
if __name__ == '__main__':
    #init_db()
    app.run(debug=True)

