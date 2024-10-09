import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from werkzeug.exceptions import abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlite3 import connect
from io import BytesIO
from init_db import criar_tabelas
import os

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta'

login_manager = LoginManager()
login_manager.init_app(app)

class Usuario(UserMixin):
    def __init__(self, id, created, nome):
        self.id = id
        self.created = created
        self.nome = nome

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?',
                        (user_id,)).fetchone()
    conn.close()
    if usuario:
        return Usuario(usuario[0], usuario[1], usuario[2])
    return None

@app.route("/login_pre")
def login_pre():
    if current_user.is_authenticated:
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("login"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE nome = ? AND senha = ?', (nome, senha))
        usuario = cursor.fetchone()
        con.close()
        if usuario:
            login_user(Usuario(usuario[0], usuario[1], usuario[2]))
            return redirect(url_for('admin'))
        flash('Login inválido!')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    contato = conn.execute('SELECT * FROM contato').fetchall()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    reports = conn.execute('SELECT * FROM reports ORDER BY ordem').fetchall()
    textos = conn.execute('SELECT * FROM textos').fetchall()
    conn.close()
    return render_template('admin.html', usuario=current_user.nome, posts=posts, contato=contato, usuarios=usuarios, reports=reports, textos=textos)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Imagens usadas no carrossel
imagens_dir = "static/img/fotos/bolos"
imagens = []
# Walk through the directory and append image paths to the list
for root, _, filenames in os.walk(imagens_dir):
    for filename in filenames:
        if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):  # Check for image file extensions
            imagens.append(os.path.join(root, filename).replace('static/', ''))
indice_atual = 0

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    contato = conn.execute('SELECT whatsapp, facebook, instagram, email, endereco FROM contato').fetchall()
    mensagem_bottom = conn.execute('SELECT texto FROM mensagem_bottom').fetchall()
    textos = conn.execute('SELECT * FROM textos').fetchall()
    reports = conn.execute('SELECT * FROM reports ORDER BY ordem').fetchall()
    conn.close()
    global indice_atual
    imagem_atual = imagens[indice_atual]
    return render_template('index.html', posts=posts, contato=contato, mensagem_bottom=mensagem_bottom, imagem=imagem_atual, textos=textos, reports=reports)

@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/semeie')
def semeie():
    conn = get_db_connection()
    textos = conn.execute('SELECT * FROM textos').fetchall()
    contato = conn.execute('SELECT whatsapp, facebook, instagram, email, endereco FROM contato').fetchall()
    conn.close()

    return render_template('semeie.html', textos=textos, contato=contato)

@app.route('/proxima')
def proxima():
    global indice_atual
    indice_atual = (indice_atual + 1) % len(imagens)
    return jsonify({'imagem': imagens[indice_atual]})

@app.route('/anterior')
def anterior():
    global indice_atual
    indice_atual = (indice_atual - 1) % len(imagens)
    return jsonify({'imagem': imagens[indice_atual]})

@app.route("/admin/excluir_post/<int:id>")
def excluir_post(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Postagem excluída!')
    return redirect(url_for("admin"))

# Route for creating a new post
@app.route('/admin/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
        conn.commit()
        conn.close()
        flash('Postagem criada com sucesso!')
        return redirect(url_for('admin'))
    return render_template('create_post.html')

# Route for editing a post
@app.route('/admin/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (id,))
    post = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, id))
        conn.commit()
        conn.close()
        flash('Postagem alterada com sucesso!')
        return redirect(url_for('admin'))

    return render_template('edit_post.html', post=post)

@app.route("/admin/excluir_usuario/<int:id>")
def excluir_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Usuário excluído!')
    return redirect(url_for("admin"))

# Route for creating a new usuario
@app.route('/admin/create_usuario', methods=['GET', 'POST'])
@login_required
def create_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO usuarios (nome, senha) VALUES (?, ?)', (nome, senha))
        conn.commit()
        conn.close()
        flash('Usuário criado com sucesso!')
        return redirect(url_for('admin'))
    return render_template('create_usuario.html')

# Route for editing a usuario
@app.route('/admin/edit_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (id,))
    usuario = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE usuarios SET nome = ?, senha = ? WHERE id = ?', (nome, senha, id))
        conn.commit()
        conn.close()
        flash('Usuário alterado com sucesso!')
        return redirect(url_for('admin'))

    return render_template('edit_usuario.html', usuario=usuario)

# Rota para upload de novo relatório
@app.route('/reports/new', methods=['GET', 'POST'])
@login_required
def create_report():
    if request.method == 'POST':
        description = request.form['description']
        ordem = request.form['ordem']
        if 'report_file' not in request.files:
            flash('Selecione um arquivo PDF para upload')
            return redirect(url_for('create_report'))

        report_file = request.files['report_file']
        
        # Extract filename from report_file object
        filename = report_file.filename
        
        if filename.endswith('.pdf'):
            report_data = report_file.read()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO reports (description, report_name, report_file, ordem) VALUES (?, ?, ?, ?)', (description, filename, report_data, ordem))
            conn.commit()
            conn.close()
            flash('Relatório cadastrado com sucesso!')
            return redirect(url_for('admin'))
        else:
            flash('Apenas arquivos PDF são permitidos')
            return redirect(url_for('create_report'))

    return render_template('create_report.html')

@app.route('/reports/<int:id>/download')
def download_report(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports WHERE id = ?', (id,))
    report = cursor.fetchone()
    conn.commit()
    conn.close()

    if report is None:
        abort(404)

    # Retrieve the PDF data from the database
    pdf_data = report[2]

    # Specify the download name (optional but recommended)
    download_name = report[3]

    response = send_file(BytesIO(pdf_data), as_attachment=True, mimetype='application/pdf', download_name=download_name)
    return response

@app.route("/admin/excluir_report/<int:id>")
def excluir_report(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Relatório excluído!')
    return redirect(url_for("admin"))

# Route for editing a report
@app.route('/admin/edit_report/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_report(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports WHERE id = ?', (id,))
    report = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        description = request.form['description']
        report_file = request.files['report_file']
        ordem = request.form['ordem']
        
        # Extract filename from report_file object
        filename = report_file.filename
        
        if filename.endswith('.pdf'):
            report_data = report_file.read()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('update reports set description = ?, report_name = ?, report_file = ?, ordem = ? where id = ?', (description, filename, report_data, ordem, id))
            conn.commit()
            conn.close()
            flash('Relatório alterado com sucesso!')
            return redirect(url_for('admin'))
        else:
            flash('Apenas arquivos PDF são permitidos')
            return redirect(url_for('edit_report'))

    return render_template('edit_report.html', report=report)

# Route for editing a contato
@app.route('/admin/edit_contato/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_contato(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contato WHERE id = ?', (id,))
    contato = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        whatsapp = request.form['whatsapp']
        facebook = request.form['facebook']
        instagram = request.form['instagram']
        email = request.form['email']
        endereco = request.form['endereco']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE contato SET whatsapp = ?, facebook = ?, instagram = ?, email = ?, endereco = ? WHERE id = ?', (whatsapp, facebook, instagram, email, endereco, id))
        conn.commit()
        conn.close()
        flash('Contatos alterados com sucesso!')
        return redirect(url_for('admin'))

    return render_template('edit_contato.html', contato=contato)

# Route for editing a texto
@app.route('/admin/edit_textos/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_textos(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM textos WHERE id = ?', (id,))
    textos = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        quem_somos = request.form['quem_somos']
        visao_semear = request.form['visao_semear']
        missao_semear = request.form['missao_semear']
        sobre_a_comunidade = request.form['sobre_a_comunidade']
        nossa_historia = request.form['nossa_historia']
        atividades = request.form['atividades']
        parceiros = request.form['parceiros']
        transparencia = request.form['transparencia']
        novidades = request.form['novidades']
        semeie = request.form['semeie']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE textos SET quem_somos = ?, visao_semear = ?, missao_semear = ?, sobre_a_comunidade = ?, nossa_historia = ?, atividades = ?, parceiros = ?, transparencia = ?, novidades = ?, semeie = ? WHERE id = ?', (quem_somos, visao_semear, missao_semear, sobre_a_comunidade, nossa_historia, atividades, parceiros, transparencia, novidades, semeie, id))
        conn.commit()
        conn.close()
        flash('Textos alterados com sucesso!')
        return redirect(url_for('admin'))

    return render_template('edit_textos.html', textos=textos)

@app.route('/reports')
def reports():
    conn = get_db_connection()
    cursor = conn.cursor()
    reports = conn.execute('SELECT * FROM reports').fetchall()
    conn.close()

    return render_template('reports.html', reports=reports)

@app.route('/posts')
def posts():
    conn = get_db_connection()
    cursor = conn.cursor()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    return render_template('posts.html', posts=posts)

if __name__ == "__main__":
  criar_tabelas()
  app.run()
