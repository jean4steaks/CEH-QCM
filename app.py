import json
import random
import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- CHARGEMENT DES DONNÉES ---
def load_questions():
    all_questions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = ['ceh_12-13_v1.json', 'ceh_12-13_v2.json']
    
    for file in files:
        file_path = os.path.join(base_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_questions.extend(data)
        except FileNotFoundError:
            print(f"⚠️ Attention: {file_path} introuvable.")
    
    random.shuffle(all_questions)
    return all_questions

# Initialisation globale
questions_db = load_questions()

# --- TEMPLATE HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>CEH Exam Trainer - Randomized</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding: 20px; }
        .quiz-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 800px; }
        .question { font-size: 1.25rem; font-weight: bold; margin-bottom: 20px; color: #1c1e21; line-height: 1.4; }
        .options-list { list-style: none; padding: 0; }
        .option-btn { 
            display: block; width: 100%; text-align: left; padding: 14px; margin-bottom: 12px;
            border: 1px solid #ddd; border-radius: 8px; cursor: pointer; transition: all 0.2s; background: #fff; font-size: 1rem;
        }
        .option-btn:hover:not([disabled]) { background: #f0f7ff; border-color: #007bff; }
        .correct { background: #d4edda !important; border-color: #28a745 !important; color: #155724; font-weight: bold; }
        .wrong { background: #f8d7da !important; border-color: #dc3545 !important; color: #721c24; }
        .explanation { margin-top: 20px; padding: 15px; background: #e7f3ff; border-left: 5px solid #007bff; border-radius: 4px; display: none; line-height: 1.5; }
        .controls { margin-top: 25px; display: flex; justify-content: space-between; }
        #next-btn, #restart-btn { padding: 12px 24px; font-size: 1rem; border: none; border-radius: 6px; cursor: pointer; display: none; }
        #next-btn { background: #007bff; color: white; }
        #restart-btn { background: #6c757d; color: white; }
        .score-info { color: #65676b; margin-bottom: 15px; font-size: 0.95rem; font-weight: 600; border-bottom: 1px solid #eee; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="quiz-card">
        <div class="score-info">
            Question <span id="q-num">0</span> / {{ total }} | Score: <span id="current-score">0</span>
        </div>
        
        <div id="q-text" class="question">Prêt pour un nouveau test aléatoire ?</div>
        
        <div id="options-container" class="options-list">
             <button class="option-btn" style="text-align:center; background:#007bff; color:white;" onclick="startQuiz()">Démarrer le Quiz</button>
        </div>
        
        <div id="expl-box" class="explanation"></div>
        
        <div class="controls">
            <button id="restart-btn" onclick="resetQuiz()">🔄 Re-mélanger et recommencer</button>
            <button id="next-btn" onclick="loadNext()">Question suivante ➡️</button>
        </div>
    </div>

    <script>
        let currentIndex = 0;
        let score = 0;
        const total = {{ total }};

        function startQuiz() {
            currentIndex = 0;
            score = 0;
            loadNext();
        }

        async function resetQuiz() {
            // Appel à la route de mélange côté serveur
            await fetch('/shuffle_questions');
            
            currentIndex = 0;
            score = 0;
            document.getElementById('current-score').innerText = "0";
            document.getElementById('restart-btn').style.display = 'none';
            document.getElementById('expl-box').style.display = 'none';
            document.getElementById('options-container').innerHTML = '';
            loadNext();
        }

        async function loadNext() {
            if (currentIndex >= total) {
                showFinalScore();
                return;
            }

            const response = await fetch(`/get_question/${currentIndex}`);
            const data = await response.json();

            document.getElementById('q-num').innerText = currentIndex + 1;
            document.getElementById('q-text').innerText = data.question;
            document.getElementById('expl-box').style.display = 'none';
            document.getElementById('next-btn').style.display = 'none';
            document.getElementById('restart-btn').style.display = 'none';
            
            const container = document.getElementById('options-container');
            container.innerHTML = '';

            for (let key in data.options) {
                const btn = document.createElement('button');
                btn.className = 'option-btn';
                btn.innerText = key + ": " + data.options[key];
                btn.onclick = () => checkAnswer(key, data.correct_answer, data.explanation, btn);
                container.appendChild(btn);
            }
            currentIndex++;
        }

        function checkAnswer(selected, correct, explanation, btn) {
            const btns = document.querySelectorAll('.option-btn');
            btns.forEach(b => b.disabled = true);

            if (selected === correct) {
                btn.classList.add('correct');
                score++;
                document.getElementById('current-score').innerText = score;
            } else {
                btn.classList.add('wrong');
                btns.forEach(b => {
                    if (b.innerText.trim().startsWith(correct + ":")) {
                        b.classList.add('correct');
                    }
                });
            }

            if (explanation) {
                const eb = document.getElementById('expl-box');
                eb.innerHTML = "<strong>Explication :</strong> " + explanation;
                eb.style.display = 'block';
            }
            document.getElementById('next-btn').style.display = 'block';
        }

        function showFinalScore() {
            document.getElementById('q-text').innerText = "Quiz terminé !";
            document.getElementById('options-container').innerHTML = `
                <div style="text-align:center; padding: 20px;">
                    <h2 style="color: #007bff">Score final : ${score} / ${total}</h2>
                    <p>Les questions ont été re-mélangées pour votre prochaine tentative.</p>
                </div>
            `;
            document.getElementById('next-btn').style.display = 'none';
            document.getElementById('expl-box').style.display = 'none';
            document.getElementById('restart-btn').style.display = 'block';
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, total=len(questions_db))

@app.route('/shuffle_questions')
def shuffle_questions():
    global questions_db
    random.shuffle(questions_db)
    return jsonify({"status": "shuffled"})

@app.route('/get_question/<int:idx>')
def get_question(idx):
    if idx < len(questions_db):
        return jsonify(questions_db[idx])
    return jsonify({"error": "Index out of range"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=4000)