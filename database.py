import sqlite3

def conectar():
    return sqlite3.connect('database.db')

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT UNIQUE,
        senha TEXT,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profissionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        especialidade TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        profissional_id INTEGER,
        data TEXT,
        hora TEXT,
        descricao TEXT,
        tipo TEXT
    )
    """)

    

    conn.commit()
    conn.close()

    

if __name__ == "__main__":
    criar_tabelas()