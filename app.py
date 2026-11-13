from flask import Flask, render_template, request, jsonify, redirect, url_for
import openai
import json
import os 

app = Flask(__name__)
CONFIG_FILE = 'config.json'


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"openai_api_key": "", "agents": []}
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', agents=config.get('agents', []))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    config = load_config()
    if request.method == 'POST':
        # Aktualizacja klucza
        config['openai_api_key'] = request.form.get('api_key')

        # Dodawanie nowego agenta
        new_agent_id = request.form.get('agent_id')
        new_agent_name = request.form.get('agent_name')
        if new_agent_id and new_agent_name:
            config['agents'].append({"id": new_agent_id, "name": new_agent_name})

        save_config(config)
        return redirect(url_for('settings'))

    return render_template('settings.html', config=config)


@app.route('/lesson/<assistant_id>')
def lesson(assistant_id):
    config = load_config()
    client = openai.OpenAI(api_key=config['openai_api_key'])
    # Utworzenie nowego, niezależnego wątku dla lekcji
    thread = client.beta.threads.create()
    return render_template('lesson.html', assistant_id=assistant_id, thread_id=thread.id)


@app.route('/api/chat', methods=['POST'])
def chat():
    config = load_config()
    client = openai.OpenAI(api_key=config['openai_api_key'])

    data = request.json
    thread_id = data.get('thread_id')
    assistant_id = data.get('assistant_id')
    user_message = data.get('message')

    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=user_message
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, assistant_id=assistant_id
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0].content[0].text.value
        return jsonify({"response": latest_message})
    return jsonify({"error": "Błąd generowania odpowiedzi"}), 500


if __name__ == '__main__':
    app.run(debug=True)
