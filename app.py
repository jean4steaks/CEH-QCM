import json
import random
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- CHARGEMENT DES DONNÉES ---
def load_questions():
    all_questions = []
    files = ['ceh_12-13_v1.json', 'ceh_12-13_v2.json']
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_questions.extend(data)
        except FileNotFoundError:
            print(f"Attention: {file} introuvable.")
    
    # Mélange les questions au démarrage
    random.shuffle(all_questions)
    return all_questions

questions_db = load_questions()

# --- TEMPLATE HTML (Interface Web) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CEH Exam Trainer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding: 20px; }
        .quiz-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 700px; }
        .question { font-size: 1.2rem; font-weight: bold; margin-bottom: 20px; color: #1c1e21; }
        .options-list { list-style: none; padding: 0; }
        .option-btn { 
            display: block; width: 100%; text-align: left; padding: 12px; margin-bottom: 10px;
            border: 1px solid #ddd; border-radius: 8px; cursor: pointer; transition: 0.2s; background: #fff;
        }
        .option-btn:hover { background: #f7f8fa; border-color: #007bff; }
        .correct { background: #d4edda !important; border-color: #28a745 !important; color: #155724; }
        .wrong { background: #f8d7da !important; border-color: #dc3545 !important; color: #721c24; }
        .explanation { margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 8px; display: none; }
        #next-btn { 
            margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; 
            border: none; border-radius: 5px; cursor: pointer; display: none; float: right;
        }
        .score-info { color: #65676b; margin-bottom: 10px; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="quiz-card">
        <div class="score-info">Question <span id="q-num">1</span> / {{ total }} | Score: <span id="current-score">0</span></div>
        <div id="q-text" class="question">Chargement...</div>
        <div id="options-container" class="options-list"></div>
        <div id="expl-box" class="explanation"></div>
        <button id="next-btn" onclick="loadNext()">Question suivante</button>
    </div>

    <script>
        let currentIndex = 0;
        let score = 0;
        const total = {{ total }};

        async function loadNext() {
            if (currentIndex >= total) {
                alert("Quiz terminé ! Score final: " + score + "/" + total);
                location.reload();
                return;
            }

            const response = await fetch(`/get_question/${currentIndex}`);
            const data = await response.json();

            document.getElementById('q-num').innerText = currentIndex + 1;
            document.getElementById('q-text').innerText = data.question;
            document.getElementById('expl-box').style.display = 'none';
            document.getElementById('next-btn').style.display = 'none';
            
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
                // Montre la bonne réponse
                btns.forEach(b => {
                    if (b.innerText.startsWith(correct + ":")) b.classList.add('correct');
                });
            }

            if (explanation) {
                const eb = document.getElementById('expl-box');
                eb.innerText = "Explication: " + explanation;
                eb.style.display = 'block';
            }
            document.getElementById('next-btn').style.display = 'block';
        }

        // Init
        loadNext();
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, total=len(questions_db))

@app.route('/get_question/<int:idx>')
def get_question(idx):
    if idx < len(questions_db):
        return jsonify(questions_db[idx])
    return jsonify({"error": "Fin du quiz"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)