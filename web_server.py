# Imports Python’s built‑in HTTP server module. It provides classes like BaseHTTPRequestHandler and SimpleHTTPRequestHandler for handling HTTP requests.
import http.server
# Provides a framework for network servers, including TCP servers that can be used with HTTP handlers.
import socketserver
# Provides utilities for parsing URLs and query strings (e.g., form data from POST requests).
import urllib.parse
# Provides access to SQLite, a file‑based relational database, used here as backend DB.
import sqlite3
# Allows encoding/decoding JSON data (convert Python objects to JSON strings and back).
import json
# used for file paths, environment variables
import os
# used for timestamps (start_time, submission_time, etc.)
from datetime import datetime
# Sets the TCP port the HTTP server will listen on
PORT = 8000
# request handler class
#  inherits from SimpleHTTPRequestHandler, which by default handles GET requests by serving files from the current directory.
class OAPortalHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/admin':
            try:
                conn = sqlite3.connect('oa_platform.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        r.student_name, 
                        MAX(r.submission_time), 
                        SUM(CASE WHEN q.type = 'MCQ' AND r.answer_text = q.correct_option THEN 1 ELSE 0 END),
                        GROUP_CONCAT(q.content || '|' || COALESCE(r.answer_text, 'N/A') || '|' || COALESCE(q.correct_option, 'N/A') || '|' || q.type, '||')
                    FROM sessions s
                    JOIN questions q ON (',' || s.assigned_question_ids || ',') LIKE ('%,' || q.id || ',%')
                    LEFT JOIN student_responses r ON s.student_name = r.student_name AND q.id = r.question_id
                    GROUP BY s.student_name
                    ORDER BY MAX(s.start_time) DESC
                ''')
                # COALESCE function in SQL Server returns the first non null value from the given list of inputs.
                # cursor.fetchall(): Fetches all rows returned by the query as a list of tuples.
                rows = cursor.fetchall()
                conn.close()
                admin_data = [{"name": r[0], "time": r[1], "score": r[2], "details": r[3]} for r in rows]
                
                self.send_response(200) # Tell the browser the request was successful (200 OK)
                self.send_header('Content-type', 'text/html; charset=utf-8') # Tell the browser I’m sending back an HTML page in UTF‑8.
                self.end_headers() # Finish sending headers; I’m ready to send the actual page content now.
                
                with open('templates/admin.html', 'r', encoding='utf-8') as f:
                    # Replaces the placeholder const questions = []; in the HTML with a JS variable assignment containing the actual questions list (as JSON).
                    content = f.read().replace("const submissions = [];", f"const submissions = {json.dumps(admin_data)};")
                    self.wfile.write(content.encode('utf-8')) # Sends the final HTML page to the browser.
            except Exception as e:
                print(f"Admin Error: {e}")
                self.send_error(500, f"Internal Server Error: {e}")
        else:
            return super().do_GET() # For any GET path that is not /admin, this calls the parent class’s do_GET. That default behavior serves files from the current directory
        

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        if self.path == '/start':
            try:
                params = urllib.parse.parse_qs(post_data) # Parses the URL‑encoded form data in post_data into a dictionary. Each key maps to a list of values.
                name = params.get('student_name', ['Guest'])[0]
                sid = params.get('student_id', ['000'])[0]
                full_id = f"{name} | ID:{sid}"

                conn = sqlite3.connect('oa_platform.db')
                cursor = conn.cursor()
                
                # --- UNIQUE ID CHECK START ---
                # Check if this exact Name + ID combination already exists in responses
                cursor.execute("SELECT student_name FROM student_responses WHERE student_name = ?", (full_id,))
                if cursor.fetchone():
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    # Alert the user and send them back to login
                    response = f"<script>alert('Error: Student ID {sid} has already submitted the test!'); window.location.href='/templates/index.html';</script>"
                    self.wfile.write(response.encode('utf-8'))
                    conn.close()
                    return
                # --- UNIQUE ID CHECK END ---

                cursor.execute("SELECT assigned_question_ids FROM sessions WHERE student_name = ?", (full_id,))
                existing_session = cursor.fetchone()

                if existing_session:
                    id_list = [int(i) for i in existing_session[0].split(',')]
                    placeholders = ','.join(['?'] * len(id_list)) # Builds a string of ? placeholders separated by commas, e.g. "?,?,?". This will be used in the SQL IN clause.
                    cursor.execute(f"SELECT id, title, content, options, type FROM questions WHERE id IN ({placeholders})", id_list)
                    final_questions = cursor.fetchall()
                else:
                    cursor.execute("SELECT id, title, content, options, type FROM questions WHERE type = 'MCQ' ORDER BY assigned_count ASC, RANDOM() LIMIT 5")
                    mcqs = cursor.fetchall()
                    cursor.execute("SELECT id, title, content, options, type FROM questions WHERE type = 'LONG' ORDER BY assigned_count ASC, RANDOM() LIMIT 2")
                    longs = cursor.fetchall()
                    final_questions = mcqs + longs
                    id_string = ",".join(map(str, [q[0] for q in final_questions]))
                    cursor.execute("INSERT INTO sessions (student_name, start_time, assigned_question_ids) VALUES (?, ?, ?)", (full_id, datetime.now(), id_string))
                    for q in final_questions:
                        cursor.execute("UPDATE questions SET assigned_count = assigned_count + 1 WHERE id = ?", (q[0],))
                    conn.commit()
                conn.close()

                questions_list = [{"id": q[0], "title": q[1], "content": q[2], "options": q[3].split('|') if q[3] else [], "type": q[4]} for q in final_questions]
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                with open('templates/index.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                    html = html.replace("const questions = [];", f"const questions = {json.dumps(questions_list)};")
                    html = html.replace("ST OA PORTAL", full_id)
                    self.wfile.write(html.encode('utf-8'))

            except Exception as e:
                print(f"Start Error: {e}")
                self.send_error(500, f"Error starting test: {e}")

        elif self.path == '/submit_answers':
            try:
                data = json.loads(post_data)
                conn = sqlite3.connect('oa_platform.db')
                cursor = conn.cursor()
                for q_id, text in data.get('answers', {}).items():
                    cursor.execute('INSERT INTO student_responses (student_name, question_id, answer_text, submission_time) VALUES (?, ?, ?, ?)', (data.get('name'), q_id, text, datetime.now()))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"Submit Error: {e}")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), OAPortalHandler) as httpd:
    print(f"Server LIVE on http://localhost:{PORT}")
    httpd.serve_forever()