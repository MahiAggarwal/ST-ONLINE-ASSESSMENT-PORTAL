import sqlite3
import random
from datetime import datetime, timedelta

def get_questions_for_student(student_name):
    conn = sqlite3.connect('oa_platform.db')
    cursor = conn.cursor()

    # 1. Find sessions from the last 30 minutes
    half_hour_ago = datetime.now() - timedelta(minutes=30)
    
    # We look for anyone who started recently
    cursor.execute("SELECT assigned_question_ids FROM sessions WHERE start_time > ?", (half_hour_ago,))
    recent_sessions = cursor.fetchall()
    
    # Convert those database strings back into sets of numbers
    # Example: "1,2,3" becomes {1, 2, 3}
    recent_question_sets = []
    for row in recent_sessions:
        q_ids = set(map(int, row[0].split(',')))
        recent_question_sets.append(q_ids)

    # 2. Get all possible question IDs from our bank
    cursor.execute("SELECT id FROM questions")
    all_ids = [row[0] for row in cursor.fetchall()]

    # 3. Try to find a unique set (The Anti-Cheating Logic)
    max_attempts = 100
    for _ in range(max_attempts):
        # Pick 5 random questions
        candidate_set = set(random.sample(all_ids, 5))
        
        is_safe = True
        for existing_set in recent_question_sets:
            # Check overlap
            overlap = candidate_set.intersection(existing_set)
            # 10% of 5 questions is 0.5, so we allow 0 or 1 overlapping question
            if len(overlap) > 1: 
                is_safe = False
                break
        
        if is_safe:
            # 4. Save this session to the database
            q_string = ",".join(map(str, candidate_set))
            cursor.execute("INSERT INTO sessions (student_name, start_time, assigned_question_ids) VALUES (?, ?, ?)",
                           (student_name, datetime.now(), q_string))
            conn.commit()
            
            print(f"\n==========================================")
            print(f"   OFFICIAL ASSESSMENT: {student_name.upper()}")
            print(f"   TIME START: {datetime.now().strftime('%H:%M:%S')}")
            print(f"==========================================\n")

            # Let's fetch the actual question text using those IDs
            placeholders = ', '.join(['?'] * len(candidate_set))
            cursor.execute(f"SELECT title, content FROM questions WHERE id IN ({placeholders})", tuple(candidate_set))
            questions = cursor.fetchall()

            for i, q in enumerate(questions, 1):
                print(f"QUESTION {i}: {q[0]}")
                print(f"TASK: {q[1]}")
                print("-" * 30)
            
            print("\nStatus: Exam Generated Successfully.")
            break
    else:
        print("Error: Could not find a unique enough set. Please expand the question bank!")

    conn.close()

# Let's test it!
if __name__ == "__main__":
    name = input("Enter student name to start test: ")
    get_questions_for_student(name)