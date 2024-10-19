import sqlite3

def connect():
    return sqlite3.connect('database.db')

def criar_tabelas():
    conn = connect()
    c = conn.cursor()
   
    with open('schema.sql') as f:
      c.executescript(f.read())
   
    c.execute("""
      INSERT OR IGNORE INTO usuarios (nome, senha) VALUES (?, ?)
    """, ('admin', 'senha_admin'))
   
    c.execute("""
      INSERT OR IGNORE INTO usuarios (nome, senha) VALUES (?, ?)
    """, ('usuario1', 'senha_usuario1'))

    c.execute("""INSERT INTO contato (whatsapp, facebook, instagram, email, endereco) VALUES (?, ?, ?, ?, ?)
    """, ('+5519991626248', 'https://www.facebook.com', 'https://www.instagram.com', 'joaocsc@gmail.com', 'Americana - SP, 13472-000'))
   
    c.execute("""INSERT INTO mensagem_bottom (texto) VALUES (?)
    """, ('© 2024 Website desenvolvido por alunos da UNIVESP para o Projeto Integrador em Computação II.',))

    c.execute("""
      INSERT INTO textos (quem_somos, sobre_a_comunidade, transparencia) select ?, ?, ? where not exists(select * from textos)
    """, ('quem_somos_texto', 'sobre_a_comunidade', 'transparencia'))

    c.execute("""
      INSERT INTO promocao (nome, descricao, imagem) SELECT ?, ?, ? WHERE NOT EXISTS(SELECT * from promocao)
     """, ('Aguarde!', 'Em breve uma nova promoção', ''))

    conn.commit()
    conn.close()
