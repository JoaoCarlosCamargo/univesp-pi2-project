import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from werkzeug.exceptions import abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlite3 import connect
from io import BytesIO
from init_db import criar_tabelas
import os
import uuid
from werkzeug.utils import secure_filename
import base64
from twilio.rest import Client

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB (Aumente se necessário)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

#def salvar_imagem(arquivo):
#    if arquivo and allowed_file(arquivo.filename):
#        nome_unico = str(uuid.uuid4()) + '_' + secure_filename(arquivo.filename)
#        caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
#        arquivo.save(caminho_completo)
#        return nome_unico
#    return None
def salvar_imagem(arquivo):
    if arquivo and allowed_file(arquivo.filename):
        try:
            nome_unico = str(uuid.uuid4()) + '_' + secure_filename(arquivo.filename)
            caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
            arquivo.save(caminho_completo)
            return nome_unico
        except Exception as e:
            # Logar o erro para análise posterior
            logging.error(f"Erro ao salvar imagem: {str(e)}")
            return None
    return None

# ... (resto do código)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    contato = conn.execute('SELECT * FROM contato').fetchall()
    promocao = conn.execute('SELECT * FROM promocao').fetchall()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    textos = conn.execute('SELECT * FROM textos').fetchall()
    clientes = conn.execute('SELECT * FROM cliente').fetchall()
    conn.close()
    return render_template('admin.html', usuario=current_user.nome, contato=contato, usuarios=usuarios, textos=textos, promocao=promocao, clientes=clientes)

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
    contato = conn.execute('SELECT whatsapp, facebook, instagram, email, endereco FROM contato').fetchall()
    mensagem_bottom = conn.execute('SELECT texto FROM mensagem_bottom').fetchall()
    textos = conn.execute('SELECT * FROM textos').fetchall()
    promocao = conn.execute('SELECT nome, descricao, imagem FROM promocao').fetchall()
    # Criar uma lista para armazenar as promoções com a URL da imagem
    promocoes_com_url = []

    for promocao in promocao:
        # Convertendo a string para bytes e codificando em base64
        imagem_binaria = promocao['imagem'].encode('utf-8')
        imagem_base64 = base64.b64encode(imagem_binaria).decode('utf-8')
        
        extensao = promocao['imagem'].split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        # adicione outros tipos MIME conforme necessário
        }
        tipo_mime = mime_types.get(extensao, 'image/jpeg')  # valor padrão se a extensão não for encontrada

        data_url = f"data:{tipo_mime};base64,{imagem_base64}"
        #data_url = f"data:image/jpeg;base64,{imagem_base64}"

        # Criando um novo dicionário e adicionando à lista
        nova_promocao = {
            'nome': promocao['nome'],
            'descricao': promocao['descricao'],
            'imagem': promocao['imagem'],
            'imagem_url': data_url
        }
        promocoes_com_url.append(nova_promocao)
    conn.close()
    global indice_atual
    imagem_atual = imagens[indice_atual]
    return render_template('index.html', contato=contato, mensagem_bottom=mensagem_bottom, imagem=imagem_atual, textos=textos, promocao=promocoes_com_url)

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
        sobre_a_comunidade = request.form['sobre_a_comunidade']
        transparencia = request.form['transparencia']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE textos SET quem_somos = ?, sobre_a_comunidade = ?, transparencia = ? WHERE id = ?', (quem_somos, sobre_a_comunidade, transparencia,  id))
        conn.commit()
        conn.close()
        flash('Textos alterados com sucesso!')
        return redirect(url_for('admin'))

    return render_template('edit_textos.html', textos=textos)

# Route for editing a promocao
@app.route('/admin/edit_promocao/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_promocao(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM promocao WHERE id = ?', (id,))
    promocao = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        imagem = request.files['imagem']
        nome_imagem = salvar_imagem(imagem)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE promocao SET nome = ?, descricao = ?, imagem = ? WHERE id = ?', (nome, descricao, nome_imagem, id))
        conn.commit()
        conn.close()
        flash('Promoção alterada com sucesso!')
        return redirect(url_for('index'))

    return render_template('edit_promocao.html', promocao=promocao)

# Rota para exibir o formulário de cadastro
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

# Rota para processar o cadastro
@app.route('/cadastro', methods=['POST'])
def process_cadastro():
    nome = request.form['nome']
    telefone = request.form['telefone']

    if not nome or not telefone:
        flash('Todos os campos são obrigatórios!')
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se o telefone já está cadastrado
    cursor.execute('SELECT * FROM cliente WHERE telefone = ?', (telefone,))
    usuario_existente = cursor.fetchone()
    
    if usuario_existente:
        flash('Este número de telefone já está cadastrado!')
        conn.close()
        return redirect('/cadastro')
    
    # Inserir o novo cadastro se o telefone não existir
    cursor.execute('INSERT INTO cliente (nome, telefone) VALUES (?, ?)', (nome, telefone))
    conn.commit()
    conn.close()

    flash('Cadastro realizado com sucesso!')

    # Aqui você pode chamar a função para enviar SMS ou WhatsApp
    # enviar_sms(telefone) ou enviar_whatsapp(telefone)
    enviar_whatsapp(telefone)

    return redirect('/')

# Função para enviar mensagem no WhatsApp
def enviar_whatsapp(telefone):
    account_sid = 'AC5b30a8de6e335f7a233678b3b9ee8758'
    auth_token = 'bd8b0ddf1fa5047c3329401edcca3f8c'
    client = Client(account_sid, auth_token)

    mensagem = client.messages.create(
        body="Obrigado por se cadastrar para receber as promoções das delícias doces da Ana!",
        from_='whatsapp:+14155238886',
        to=f'whatsapp:+55{telefone}'
    )

    print(mensagem.sid)

# Função para enviar SMS usando Twilio
def enviar_sms(telefone):
    account_sid = 'AC5b30a8de6e335f7a233678b3b9ee8758'
    auth_token = 'bd8b0ddf1fa5047c3329401edcca3f8c'
    client = Client(account_sid, auth_token)
    print(telefone)

    mensagem = client.messages.create(
        body="Obrigado por se cadastrar para receber as promoções das delícias doces da Ana!",
        from_='+17315404560',
        to=telefone
    )

    print(mensagem.sid)

@app.route("/admin/excluir_cliente/<int:id>")
def excluir_cliente(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cliente WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Cliente excluído!')
    return redirect(url_for("admin"))

# Rota para exibir o formulário de campanha
@app.route('/campanha')
def campanha():
    return render_template('campanha.html')

# Rota para processar o campanha
@app.route('/campanha', methods=['POST'])
def process_campanha():
    texto = request.form['texto']

    if not texto:
        flash('Texto obrigatório!')
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Recuperar todos os números de telefone da tabela 'cliente'
    cursor.execute('SELECT telefone FROM cliente')
    telefones = cursor.fetchall()
    
    # Percorrer todos os registros e enviar WhatsApp
    for cliente in telefones:
        telefone = cliente['telefone']
        enviar_campanha_whatsapp(telefone, texto)
    
    conn.close()    

    flash('campanha realizado com sucesso!')

    return redirect('/')
    
# Função para enviar mensagem da campanha no WhatsApp
def enviar_campanha_whatsapp(telefone, texto):
    account_sid = 'AC5b30a8de6e335f7a233678b3b9ee8758'
    auth_token = 'bd8b0ddf1fa5047c3329401edcca3f8c'
    client = Client(account_sid, auth_token)

    mensagem = client.messages.create(
        body={texto},
        from_='whatsapp:+14155238886',
        to=f'whatsapp:+55{telefone}'
    )

    print(mensagem.sid)

if __name__ == "__main__":
  criar_tabelas()
  app.run()
