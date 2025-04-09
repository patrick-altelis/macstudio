#!/usr/bin/env python3
"""
Test très simple pour vérifier si une page statique peut être servie.
"""
from flask import Flask, render_template_string

app = Flask(__name__)

# Une page très simple
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Cette page fonctionne!</h1>
    <p>Si vous voyez cette page, la connexion fonctionne correctement.</p>
</body>
</html>
"""

@app.route('/')
def hello():
    return render_template_string(HTML)

if __name__ == '__main__':
    print("IMPORTANT: Accédez à http://127.0.0.1:4444 dans votre navigateur")
    app.run(debug=True, host='127.0.0.1', port=4444)