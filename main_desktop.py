import flet as ft
import sqlite3
import os
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS LOCAL ---
DB_PATH = os.path.join(os.path.expanduser("~"), "sistema_pesagem_v2.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            peso_cadeira REAL NOT NULL,
            data_cadastro TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pesagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            peso_total REAL NOT NULL,
            peso_liquido REAL NOT NULL,
            data TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# --- APP PRINCIPAL ---
def main(page: ft.Page):
    page.title = "Pesagem Pro Desktop"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.colors.BLUE_700, use_material3=True)
    page.window_width = 1200
    page.window_height = 900
    
    init_db()

    def get_db():
        return sqlite3.connect(DB_PATH)

    def show_toast(text, success=True):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(text),
            bgcolor=ft.colors.GREEN_600 if success else ft.colors.RED_600
        )
        page.snack_bar.open = True
        page.update()

    # --- LÓGICA DE EXPORTAÇÃO EXCEL ---
    def export_excel(e):
        try:
            conn = get_db()
            # Aba 1: Resumo
            df_resumo = pd.read_sql_query("""
                SELECT p.nome, 
                       (SELECT peso_liquido FROM pesagens WHERE paciente_id = p.id ORDER BY data DESC LIMIT 1) as 'Peso Atual',
                       (SELECT data FROM pesagens WHERE paciente_id = p.id ORDER BY data DESC LIMIT 1) as 'Última Data',
                       p.peso_cadeira as 'Peso Cadeira'
                FROM pacientes p
            """, conn)
            
            # Aba 2: Histórico
            df_hist = pd.read_sql_query("""
                SELECT p.nome, ps.data, ps.peso_total, ps.peso_liquido
                FROM pesagens ps
                JOIN pacientes p ON p.id = ps.paciente_id
                ORDER BY ps.data DESC
            """, conn)
            
            file_path = os.path.join(os.path.expanduser("~"), "Documents", "Relatorio_Pesagem_Completo.xlsx")
            
            with pd.ExcelWriter(file_path) as writer:
                df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
                df_hist.to_excel(writer, sheet_name="Histórico Completo", index=False)
            
            conn.close()
            show_toast(f"Relatório salvo em Documentos!")
            os.startfile(os.path.dirname(file_path)) # Abre a pasta
        except Exception as ex:
            show_toast(f"Erro ao exportar: {str(ex)}", False)

    # --- TELAS ---

    def view_patient_list(search_query=""):
        page.clean()
        
        patient_grid = ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE, spacing=12)
        
        conn = get_db()
        cursor = conn.cursor()
        query = "SELECT id, nome, peso_cadeira FROM pacientes WHERE nome LIKE ? ORDER BY nome ASC"
        cursor.execute(query, (f"%{search_query}%",))
        pacientes = cursor.fetchall()
        conn.close()

        for p_id, p_nome, p_cadeira in pacientes:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT peso_liquido, data FROM pesagens WHERE paciente_id = ? ORDER BY data DESC LIMIT 1", (p_id,))
            last = cursor.fetchone()
            conn.close()
            
            peso_txt = f"{last[0]:.1f} kg" if last else "---"
            
            patient_grid.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.PERSON_OUTLINE_ROUNDED, color=ft.colors.BLUE_700),
                        ft.Text(p_nome, size=16, weight="bold", expand=True),
                        ft.Text(f"Cadeira: {p_cadeira}kg", size=12, color=ft.colors.GREY_500),
                        ft.VerticalDivider(),
                        ft.Text(peso_txt, size=16, weight="bold", color=ft.colors.BLUE_800),
                        ft.IconButton(ft.icons.ARROW_FORWARD_IOS_ROUNDED, icon_size=16, on_click=lambda _, id=p_id: view_patient_detail(id))
                    ]),
                    padding=ft.padding.all(15),
                    border=ft.border.all(1, ft.colors.GREY_100),
                    border_radius=12,
                    on_click=lambda _, id=p_id: view_patient_detail(id),
                    ink=True
                )
            )

        search_field = ft.TextField(
            hint_text="Buscar paciente por nome...",
            prefix_icon=ft.icons.SEARCH,
            on_change=lambda e: view_patient_list(e.control.value),
            expand=True,
            border_radius=15
        )

        page.add(
            ft.Container(
                padding=25,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestão de Pacientes", size=28, weight="bold"),
                        ft.Row([
                            ft.ElevatedButton("Relatório Excel", icon=ft.icons.FILE_DOWNLOAD, on_click=export_excel),
                            ft.ElevatedButton("Novo Paciente", icon=ft.icons.ADD, on_click=lambda _: open_new_patient_dialog(), 
                                             style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)),
                        ], spacing=10)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=30),
                    search_field,
                    ft.Container(height=10),
                    patient_grid
                ], expand=True)
            )
        )

    def open_new_patient_dialog():
        nome = ft.TextField(label="Nome do Paciente", border_radius=10)
        cadeira = ft.TextField(label="Peso Cadeira (kg)", border_radius=10, value="15.0")
        total = ft.TextField(label="Peso Total Balança (kg) - Opcional", border_radius=10)

        def save(e):
            if not nome.value or not cadeira.value: return
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO pacientes (nome, peso_cadeira, data_cadastro) VALUES (?, ?, ?)",
                         (nome.value, float(cadeira.value), datetime.now().isoformat()))
            p_id = cursor.lastrowid
            if total.value:
                t = float(total.value)
                c = float(cadeira.value)
                cursor.execute("INSERT INTO pesagens (paciente_id, peso_total, peso_liquido, data) VALUES (?, ?, ?, ?)",
                             (p_id, t, t - c, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            dialog.open = False
            view_patient_list()
            show_toast("Paciente cadastrado!")

        dialog = ft.AlertDialog(
            title=ft.Text("Novo Cadastro"),
            content=ft.Column([nome, cadeira, total], tight=True),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog, "open", False)), ft.ElevatedButton("Cadastrar", on_click=save)]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def view_patient_detail(p_id):
        page.clean()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, peso_cadeira FROM pacientes WHERE id = ?", (p_id,))
        paciente = cursor.fetchone()
        cursor.execute("SELECT peso_total, peso_liquido, data FROM pesagens WHERE paciente_id = ? ORDER BY data ASC", (p_id,))
        historico = cursor.fetchall()
        conn.close()

        # Gráfico de Evolução (Flet LineChart)
        chart_data = [ft.LineChartDataPoint(i, h[1]) for i, h in enumerate(historico)]
        
        chart = ft.LineChart(
            data_series=[ft.LineChartData(data_points=chart_data, color=ft.colors.BLUE_700, stroke_width=4, curved=True, with_dots=True)],
            border=ft.border.all(1, ft.colors.GREY_100),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("kg", size=12)),
            bottom_axis=ft.ChartAxis(labels_size=30),
            expand=True,
            min_y=min([h[1] for h in historico]) - 5 if historico else 0,
            max_y=max([h[1] for h in historico]) + 5 if historico else 100,
        )

        peso_atual = historico[-1][1] if historico else 0
        variacao = (historico[-1][1] - historico[-2][1]) if len(historico) > 1 else 0

        peso_input = ft.TextField(label="Peso Total na Balança (kg)", expand=True)

        def add_p(e):
            if not peso_input.value: return
            t = float(peso_input.value)
            c = paciente[1]
            conn = get_db()
            conn.execute("INSERT INTO pesagens (paciente_id, peso_total, peso_liquido, data) VALUES (?, ?, ?, ?)",
                        (p_id, t, t - c, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            view_patient_detail(p_id)

        page.add(
            ft.Container(
                padding=25,
                content=ft.Column([
                    ft.Row([
                        ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: view_patient_list()),
                        ft.Text(paciente[0], size=24, weight="bold", expand=True),
                        ft.IconButton(ft.icons.DELETE_FOREVER, icon_color=ft.colors.RED_400, on_click=lambda _: delete_patient(p_id))
                    ]),
                    ft.Row([
                        ft.Card(content=ft.Container(padding=20, content=ft.Column([ft.Text("Peso Atual", size=12), ft.Text(f"{peso_atual:.1f}kg", size=28, weight="bold")])), expand=True),
                        ft.Card(content=ft.Container(padding=20, content=ft.Column([ft.Text("Variação", size=12), ft.Text(f"{variacao:+.1f}kg", size=28, weight="bold", 
                               color=ft.colors.GREEN if variacao <= 0 else ft.colors.RED)])), expand=True),
                    ]),
                    ft.Container(height=250, content=chart if historico else ft.Text("Sem histórico para exibir gráfico", color=ft.colors.GREY_400)),
                    ft.Divider(),
                    ft.Row([peso_input, ft.ElevatedButton("Salvar Pesagem", icon=ft.icons.CHECK, on_click=add_p, height=50)]),
                    ft.ListView(expand=True, controls=[
                        ft.ListTile(title=ft.Text(f"{h[1]:.1f} kg"), subtitle=ft.Text(f"Total: {h[0]}kg | {h[2][:16]}"))
                        for h in reversed(historico)
                    ])
                ], expand=True)
            )
        )

    def delete_patient(p_id):
        conn = get_db()
        conn.execute("DELETE FROM pacientes WHERE id = ?", (p_id,))
        conn.commit()
        conn.close()
        view_patient_list()
        show_toast("Paciente excluído.")

    view_patient_list()

ft.app(target=main)
 Greenland
