from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

def conectar():
    return sqlite3.connect('database.db')

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------------- CADASTRO ----------------
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO usuarios (nome, usuario, senha, tipo)
            VALUES (?, ?, ?, ?)
            """, (
                request.form['nome'],
                request.form['usuario'],
                request.form['senha'],
                request.form['tipo']
            ))
            conn.commit()
        except:
            return "Usuário já existe"

        conn.close()
        return redirect('/login')

    return render_template('cadastro.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?",
                       (request.form['usuario'], request.form['senha']))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['usuario_id'] = user[0]
            session['nome'] = user[1]
            session['tipo'] = user[4]
            return redirect('/dashboard')

        flash("Login inválido", "erro")

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')

    if session['tipo'] == 'master':
        return render_template('dashboard_master.html')
    elif session['tipo'] == 'operador':
        return render_template('dashboard_operador.html')
    else:
        return render_template('dashboard_cliente.html')

# ---------------- USUÁRIOS ----------------
@app.route('/usuarios')
def usuarios():
    if session.get('tipo') not in ['master', 'operador']:
        return redirect('/')

    conn = conectar()
    cursor = conn.cursor()

    if session['tipo'] == 'operador':
        cursor.execute("SELECT * FROM usuarios WHERE tipo='cliente'")
    else:
        cursor.execute("SELECT * FROM usuarios")

    lista = cursor.fetchall()
    conn.close()

    return render_template('usuarios.html', usuarios=lista)

# ---------------- EDITAR USUÁRIO ----------------
@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if session.get('tipo') != 'master':
        return redirect('/')

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("""
        UPDATE usuarios
        SET nome=?, usuario=?, tipo=?
        WHERE id=?
        """, (
            request.form['nome'],
            request.form['usuario'],
            request.form['tipo'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect('/usuarios')

    cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
    usuario = cursor.fetchone()
    conn.close()

    return render_template('editar_usuario.html', usuario=usuario)

# ---------------- EXCLUIR USUÁRIO ----------------
@app.route('/excluir_usuario/<int:id>')
def excluir_usuario(id):
    if session.get('tipo') != 'master':
        return redirect('/')

    if id == session['usuario_id']:
        return "Você não pode excluir seu próprio usuário"

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/usuarios')

# ---------------- NOVO USUÁRIO ----------------
@app.route('/novo_usuario', methods=['GET', 'POST'])
def novo_usuario():
    if session.get('tipo') != 'master':
        return redirect('/')

    if request.method == 'POST':
        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO usuarios (nome, usuario, senha, tipo)
            VALUES (?, ?, ?, ?)
            """, (
                request.form['nome'],
                request.form['usuario'],
                request.form['senha'],
                request.form['tipo']
            ))
            conn.commit()
        except:
            return "Usuário já existe"

        conn.close()
        return redirect('/usuarios')

    return render_template('novo_usuario.html')

# ---------------- NOVO CLIENTE ----------------
@app.route('/novo_cliente', methods=['GET', 'POST'])
def novo_cliente():
    if session.get('tipo') not in ['master', 'operador']:
        return redirect('/')

    if request.method == 'POST':
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO usuarios (nome, usuario, senha, tipo)
        VALUES (?, ?, ?, 'cliente')
        """, (
            request.form['nome'],
            request.form['usuario'],
            request.form['senha']
        ))

        conn.commit()
        conn.close()
        return redirect('/usuarios')

    return render_template('novo_cliente.html')

# ---------------- PROFISSIONAIS ----------------
@app.route('/profissionais', methods=['GET', 'POST'])
def profissionais():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST' and session['tipo'] == 'master':
        cursor.execute("""
        INSERT INTO profissionais (nome, especialidade)
        VALUES (?, ?)
        """, (request.form['nome'], request.form['especialidade']))
        conn.commit()

    busca = request.args.get('busca')

    if busca:
        cursor.execute("""
        SELECT * FROM profissionais
        WHERE nome LIKE ? OR especialidade LIKE ?
        """, (f"%{busca}%", f"%{busca}%"))
    else:
        cursor.execute("SELECT * FROM profissionais")

    lista = cursor.fetchall()
    conn.close()

    return render_template('profissionais.html', profissionais=lista)

# ---------------- AGENDA PROFISSIONAL ----------------
@app.route('/agenda_profissional/<int:id>')
def agenda_profissional(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        strftime('%d/%m/%Y', a.data),
        a.hora,
        u.nome,
        a.tipo
    FROM agendamentos a
    JOIN usuarios u ON a.paciente_id = u.id
    WHERE a.profissional_id=?
    ORDER BY a.data, a.hora
    """, (id,))

    agenda = cursor.fetchall()

    cursor.execute("SELECT nome FROM profissionais WHERE id=?", (id,))
    profissional = cursor.fetchone()[0]

    conn.close()

    return render_template('agenda_profissional.html',
                           agenda=agenda,
                           profissional=profissional)

# ---------------- AGENDAR ----------------
@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profissionais")
    profissionais = cursor.fetchall()

    cursor.execute("SELECT * FROM usuarios WHERE tipo='cliente'")
    pacientes = cursor.fetchall()

    horarios = []
    for h in range(8, 19):
        horarios.append(f"{h:02d}:00")
        if h != 18:
            horarios.append(f"{h:02d}:30")

    # horários disponíveis
    if request.args.get('profissional') and request.args.get('data'):
        cursor.execute("""
        SELECT hora FROM agendamentos
        WHERE profissional_id=? AND data=?
        """, (
            request.args.get('profissional'),
            request.args.get('data')
        ))
        ocupados = [h[0] for h in cursor.fetchall()]
        horarios = [h for h in horarios if h not in ocupados]

    if request.method == 'POST':
        data = request.form['data']
        hora = request.form['hora']
        profissional_id = request.form['profissional']
        tipo = request.form.get('tipo')

        if not tipo:
            flash("Selecione o tipo de atendimento!", "erro")
            return redirect(request.url)

        paciente_id = session['usuario_id'] if session['tipo'] == 'cliente' else request.form['paciente']

        cursor.execute("""
        SELECT * FROM agendamentos
        WHERE data=? AND hora=? AND profissional_id=?
        """, (data, hora, profissional_id))

        if cursor.fetchone():
            conn.close()
            flash("Horário já ocupado!", "erro")
            return redirect(request.url)

        cursor.execute("""
        INSERT INTO agendamentos (paciente_id, profissional_id, data, hora, descricao, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            paciente_id,
            profissional_id,
            data,
            hora,
            request.form['descricao'],
            tipo
        ))

        conn.commit()
        conn.close()
        return redirect('/consultas')

    conn.close()

    return render_template('agendar.html',
                           profissionais=profissionais,
                           pacientes=pacientes,
                           horarios=horarios)


# ---------------- EDITAR AGENDAMENTO ----------------
@app.route('/editar_agendamento/<int:id>', methods=['GET', 'POST'])
def editar_agendamento(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    if session.get('tipo') == 'cliente':
        return "Acesso negado"

    conn = conectar()
    cursor = conn.cursor()

    # profissionais
    cursor.execute("SELECT * FROM profissionais")
    profissionais = cursor.fetchall()

    # pacientes
    cursor.execute("SELECT * FROM usuarios WHERE tipo='cliente'")
    pacientes = cursor.fetchall()

    # horários
    horarios = []
    for h in range(8, 19):
        horarios.append(f"{h:02d}:00")
        if h != 18:
            horarios.append(f"{h:02d}:30")

    if request.method == 'POST':

        data = request.form['data']
        hora = request.form['hora']
        profissional_id = request.form['profissional']

        # 🔥 BLOQUEIO DE CONFLITO
        cursor.execute("""
        SELECT * FROM agendamentos
        WHERE data=? AND hora=? AND profissional_id=? AND id!=?
        """, (data, hora, profissional_id, id))

        if cursor.fetchone():
            conn.close()
            flash("Horário já ocupado!", "erro")
            return redirect(request.url)

        cursor.execute("""
        UPDATE agendamentos
        SET paciente_id=?, profissional_id=?, data=?, hora=?, descricao=?, tipo=?
        WHERE id=?
        """, (
            request.form['paciente'],
            profissional_id,
            data,
            hora,
            request.form['descricao'],
            request.form.get('tipo'),
            id
        ))

        conn.commit()
        conn.close()

        return redirect('/consultas')

    # buscar agendamento
    cursor.execute("SELECT * FROM agendamentos WHERE id=?", (id,))
    agendamento = cursor.fetchone()

    conn.close()

    return render_template(
        'editar_agendamento.html',
        agendamento=agendamento,
        profissionais=profissionais,
        pacientes=pacientes,
        horarios=horarios
    )

# ---------------- EXCLUIR AGENDAMENTO ----------------
@app.route('/excluir_agendamento/<int:id>')
def excluir_agendamento(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    # 🔥 cliente só pode excluir o próprio
    if session['tipo'] == 'cliente':
        cursor.execute("""
        DELETE FROM agendamentos
        WHERE id=? AND paciente_id=?
        """, (id, session['usuario_id']))
    else:
        cursor.execute("""
        DELETE FROM agendamentos
        WHERE id=?
        """, (id,))

    conn.commit()
    conn.close()

    return redirect('/consultas')

# ---------------- CONSULTAS ----------------
@app.route('/consultas')
def consultas():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    busca = request.args.get('busca')

    if session['tipo'] == 'cliente':
        cursor.execute("""
        SELECT 
            a.id,
            u.nome,
            p.nome,
            strftime('%d/%m/%Y', a.data),
            a.hora,
            a.descricao,
            a.tipo,
            a.status
        FROM agendamentos a
        JOIN usuarios u ON a.paciente_id = u.id
        JOIN profissionais p ON a.profissional_id = p.id
        WHERE a.paciente_id=?
        """, (session['usuario_id'],))

    else:
        status = request.args.get('status')

        query = """
        SELECT 
            a.id,
            u.nome,
            p.nome,
            strftime('%d/%m/%Y', a.data),
            a.hora,
            a.descricao,
            a.tipo,
            a.status
        FROM agendamentos a
        JOIN usuarios u ON a.paciente_id = u.id
        JOIN profissionais p ON a.profissional_id = p.id
        WHERE 1=1
        """

        params = []

        if busca:
            query += " AND u.nome LIKE ?"
            params.append(f"%{busca}%")

        if status:
            query += " AND a.status = ?"
            params.append(status)

        cursor.execute(query, params)

    # 🔥 ESSA LINHA ESTAVA FALTANDO
    dados = cursor.fetchall()

    conn.close()

    return render_template('consultas.html', consultas=dados)


@app.route('/confirmar_agendamento/<int:id>')
def confirmar_agendamento(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE agendamentos
    SET status='confirmado'
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/consultas')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)