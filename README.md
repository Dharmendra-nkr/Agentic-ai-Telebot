# BubbleBot — a Lightweight Flask Frontend

BubbleBot is a minimal, attractive frontend built with Flask that provides a decorative floating-bubbles background and a centered chat card to connect a chatbot backend quickly for local testing or demos.

## Features
- Floating bubbles background implemented in `static/js/bubbles.js` and styled in `static/css/style.css`.
- Polished, responsive chat card (`templates/index.html`) with header/avatar, message list, and input form.
- Simple `/chat` endpoint in `app.py` that currently echoes incoming messages — ready to be replaced with real bot logic.
- Zero build step: plain Flask app, just run Python.

## Quick Start

Install dependencies and run locally:

```powershell
cd bubblebot
python -m pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:5000 in your browser
```

The `/chat` endpoint currently echoes messages. Replace the logic in `app.py` to hook your chatbot backend.

## File Map
- `app.py` — Flask app and `POST /chat` endpoint (echo by default).
- `templates/index.html` — main UI template (chat card + bubble container).
- `static/css/style.css` — styles for background, bubbles, and chat card.
- `static/js/bubbles.js` — bubble generator & animation logic.
- `requirements.txt` — minimal Python requirements.
- `README.md` — this file.

## How to Hook a Real Chatbot

Replace the echo logic in `app.py`:

```python
# in chat() handler
data = request.get_json(silent=True) or {}
message = data.get('message', '')
# TODO: call your bot here (local model, OpenAI, etc.)
reply = your_bot_reply_function(message)
return jsonify({'reply': reply})
```

Example (pseudocode for an external API):

```python
import requests
def your_bot_reply_function(message):
	resp = requests.post("https://api.example.com/generate", json={"prompt": message, "key": "API_KEY"})
	return resp.json().get("reply","(no reply)")
```

Use environment variables for secrets and never commit API keys.

## Customization Ideas
- Bubble density/speed: tweak values in `static/js/bubbles.js`.
- Theme colors: edit `:root` variables in `static/css/style.css`.
- Message formatting: enhance the client JS to support markdown, timestamps, avatars.
- Persistence: add a server-side message store (SQLite) if you need history across sessions.

## Development Tips
- Only enable Flask debug locally: `app.run(debug=True)` — remove or set to `False` for production.
- Use a virtual environment:

```powershell
python -m venv .venv
.venv\\Scripts\\Activate
python -m pip install -r requirements.txt
```

- To test changes quickly, refresh the browser or use devtools to throttle CPU and test bubble performance.

## Deploy Notes
- Use a WSGI server (Gunicorn/Waitress) behind a reverse proxy for production.
- Serve static files from a CDN or web server for scale.
- Ensure `DEBUG` is disabled and environment variables are set securely.

## Troubleshooting
- Blank page or 404: confirm `app.py` is running and you opened the correct URL.
- No bubbles: check the browser console for JS errors; ensure `static/js/bubbles.js` loaded.
- CORS/API issues when connecting to external services: configure server-side calls (do not call external APIs directly from client JS unless allowed).

## Contributing
- Fork or branch and open a pull request.
- Keep changes small and scoped (UI tweaks, accessibility fixes, or backend integrations).
- Add tests if you add server logic.

## License
Add your chosen license text here (e.g., MIT) or update this file with your project license.

---

If you want, I can also:
- Add an example integration to `app.py` for OpenAI/Anthropic/local model (scaffold environment variable usage).
- Commit and push this update to `main` and open a pull request for you.

Tell me which of the above you'd like next.
