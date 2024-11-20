from flask import Flask, render_template

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
