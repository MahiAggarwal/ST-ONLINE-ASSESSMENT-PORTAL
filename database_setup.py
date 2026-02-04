import sqlite3 #allows your script to create and interact with SQLite databases
import os #to interact with the operating system

def setup_fresh_database():
    db_name = 'oa_platform.db'
    
    # Remove the old database if it exists to start fresh
    if os.path.exists(db_name):
        os.remove(db_name)
        print("Old database removed.")

    connection = sqlite3.connect(db_name)
    #Creates a cursor object used to execute SQL commands
    cursor = connection.cursor()

    # 1. Create Questions Table 
    # Executes the SQL command inside the triple quotes.
    cursor.execute('''
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            type TEXT NOT NULL,       
            options TEXT,             
            difficulty TEXT,
            correct_option TEXT,
            assigned_count INTEGER DEFAULT 0
        )
    ''')

    # 2. Create Sessions Table
    cursor.execute('''
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY,
            student_name TEXT,
            start_time TIMESTAMP,
            assigned_question_ids TEXT
        )
    ''')

    # 3. Create Student Responses Table
    cursor.execute('''
        CREATE TABLE student_responses (
            id INTEGER PRIMARY KEY,
            student_name TEXT,
            question_id INTEGER,
            answer_text TEXT,
            submission_time TIMESTAMP
        )
    ''')

    # 4. Data: (Title, Content, Type, Options, Difficulty, Correct_Option)
    # Note: Long questions have None for Options and Correct_Option (to be graded manually)
    questions_data = [
        # --- 10 MCQ QUESTIONS ---
        ('Python Data Types', 'Which of these is immutable?', 'MCQ', 'List|Set|Tuple|Dictionary', 'Easy', 'Tuple'),
        ('SQL Basics', 'Which command is used to fetch data?', 'MCQ', 'GET|SELECT|FETCH|EXTRACT', 'Easy', 'SELECT'),
        ('C++ Pointers', 'What is the size of a pointer on a 64-bit system?', 'MCQ', '2 bytes|4 bytes|8 bytes|16 bytes', 'Medium', '8 bytes'),
        ('Logic Gate', 'Which gate is known as the Universal Gate?', 'MCQ', 'AND|OR|NAND|XOR', 'Easy', 'NAND'),
        ('Loops', 'Which loop is guaranteed to run at least once?', 'MCQ', 'for|while|do-while|none', 'Easy', 'do-while'),
        ('HTML', 'Which tag is used for the largest heading?', 'MCQ', 'head|h6|heading|h1', 'Easy', 'h1'),
        ('Python Lists', 'What is the result of [1,2] + [3]?', 'MCQ', '[1,2,3]|[6]|[1,2,[3]]|Error', 'Easy', '[1,2,3]'),
        ('Binary', 'What is the binary value of 10?', 'MCQ', '1010|1100|1001|1011', 'Medium', '1010'),
        ('DSA', 'Which data structure follows LIFO?', 'MCQ', 'Queue|Stack|Tree|Graph', 'Medium', 'Stack'),
        ('Networking', 'What does HTTP stand for?', 'MCQ', 'HighText|HyperText|HyperTransfer|HyperTool', 'Easy', 'HyperText'),

        # --- 5 LONG QUESTIONS ---
        ('Software Lifecycle', 'Explain the different phases of the SDLC model.', 'LONG', None, 'Medium', None),
        ('Plagiarism in OA', 'Describe three ways an online platform can prevent cheating.', 'LONG', None, 'Hard', None),
        ('Database Normalization', 'Explain the difference between 1NF and 2NF with examples.', 'LONG', None, 'Hard', None),
        ('Python vs C++', 'Discuss the memory management differences between Python and C++.', 'LONG', None, 'Medium', None),
        ('Artificial Intelligence', 'Explain the concept of Neural Networks in simple terms.', 'LONG', None, 'Medium', None)
    ]

    # Insert the data 
    # Executes the same SQL INSERT statement multiple times with different data.
    # ? placeholders are used for parameterized queries to avoid manual string formatting and reduce SQL injection risk.
    # The list of tuples is passed to executemany, so each tuple fills in the ? placeholders for one row.
    cursor.executemany(
        'INSERT INTO questions (title, content, type, options, difficulty, correct_option) VALUES (?, ?, ?, ?, ?, ?)', 
        questions_data
    )
    
    connection.commit() # Saves (commits) all changes to the database file.
    connection.close()
    print(f"Successfully created fresh database '{db_name}' !")

if __name__ == "__main__":
    setup_fresh_database()