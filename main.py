import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json, subprocess, os, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def verificar_ativacao():
    try:
        cmd = 'wmic csproduct get uuid'
        hwid_atual = str(subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip())
        if not os.path.exists("config.json"): return False
        with open("config.json", "r") as f:
            dados = json.load(f)
            hwid_autorizado = dados.get("hwid_autorizado")
        return hwid_atual == hwid_autorizado
    except: return False

if not verificar_ativacao(): exit()

# --- VARIÁVEIS GLOBAIS ---
saldo_devedor_base = 0.0
dados_pdf = {}

root = tk.Tk()
root.title("Saldo Zero - Simulação Price Custom")
root.geometry("450x780")
root.configure(bg="#F0F2F5")

try:
    icon_path = resource_path("img/Saldo-Zero-Logo.ico")
    if os.path.exists(icon_path): root.iconbitmap(icon_path)
except: pass

canvas = tk.Canvas(root, bg="#F0F2F5", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#F0F2F5")
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=410)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True, padx=10)
scrollbar.pack(side="right", fill="y")

# --- LÓGICA PRICE SOBRE VALOR DIGITADO ---

def etapa_1_entrada():
    global saldo_devedor_base
    try:
        total = float(e_valor_imovel.get().replace('.', '').replace(',', '.'))
        entrada = float(e_entrada.get().replace('.', '').replace(',', '.'))
        saldo_devedor_base = total - entrada
        
        dados_pdf.update({'total': total, 'entrada': entrada, 'cliente': e_cliente.get().upper(), 'imovel': e_desc.get().upper()})
        
        lbl_saldo_res.config(text=f"SALDO A FINANCIAR: R$ {saldo_devedor_base:,.2f}")
        btn_calc_1.config(state="disabled", text="✓ DADOS VALIDADOS")
        frame_mensal.pack(fill="x", pady=10)
    except: messagebox.showerror("Erro", "Valores inválidos.")

def formula_price_custom(p_base, n, i):
    if i == 0: return p_base
    # Aplicando a lógica de amortização sobre o valor que você DIGITOU
    fator = (i * (1 + i) ** n) / ((1 + i) ** n - 1)
    return p_base * (fator * n) / n # Ajuste para manter a proporção Price no valor base

def etapa_2_mensal():
    try:
        p_base = float(e_m_valor.get().replace('.', '').replace(',', '.'))
        n = int(e_m_qtd.get() or 0)
        i = float(e_m_juros.get().replace(',', '.') or 0) / 100
        
        # Resultado 1: A parcela recalculada com a lógica Price
        fator = (i * (1 + i) ** n) / ((1 + i) ** n - 1)
        # Para que o valor digitado seja a "base", aplicamos o fator de juros acumulado da Price
        parcela_final = p_base * (fator * n) / ( ( (1+i)**n - 1 ) / (i * (1+i)**n ) * fator * n ) # Simplificação para juro composto real
        
        # Maneira Direta conforme sua fórmula:
        parcela_com_juros = p_base * (i * (1 + i) ** n) / ((1 + i) ** n - 1)
        total_acumulado = parcela_com_juros * n
        
        lbl_res_mensal.config(text=f"PARCELA C/ JUROS: R$ {parcela_com_juros:,.2f}\nTOTAL NO PERÍODO: R$ {total_acumulado:,.2f}", fg="#1e3799")
        
        dados_pdf.update({'m_qtd': n, 'm_valor': parcela_com_juros, 'm_juros': i*100, 'm_total': total_acumulado})
        btn_calc_2.config(state="disabled", text="✓ MENSAL CALCULADO")

        if p_base < saldo_devedor_base:
            frame_anual.pack(fill="x", pady=10)
            canvas.yview_moveto(1.0)
        else:
            finalizar_fluxo()
    except: messagebox.showerror("Erro", "Verifique os dados.")

def etapa_3_anual():
    try:
        p_base_a = float(e_a_valor.get().replace('.', '').replace(',', '.'))
        n_a = int(e_a_qtd.get() or 0)
        i_a = float(e_a_juros.get().replace(',', '.') or 0) / 100
        
        parcela_anual_com_juros = p_base_a * (i_a * (1 + i_a) ** n_a) / ((1 + i_a) ** n_a - 1)
        total_acumulado_a = parcela_anual_com_juros * n_a
        
        lbl_res_anual.config(text=f"ANUAL C/ JUROS: R$ {parcela_anual_com_juros:,.2f}\nTOTAL REFORÇOS: R$ {total_acumulado_a:,.2f}", fg="#b71540")
        
        dados_pdf.update({'a_qtd': n_a, 'a_valor': parcela_anual_com_juros, 'a_juros': i_a*100, 'a_total': total_acumulado_a})
        finalizar_fluxo()
    except: messagebox.showerror("Erro", "Verifique os dados.")

# --- UI COMPONENTES ---

def criar_campo(pai, label, cor="#636E72"):
    tk.Label(pai, text=label, bg="white", fg=cor, font=("Segoe UI", 7, "bold")).pack(anchor="w")
    ent = ttk.Entry(pai)
    ent.pack(fill="x", pady=(0, 5))
    return ent

def finalizar_fluxo():
    lbl_final.config(text="✓ SIMULAÇÃO PRONTA", fg="#27ae60")
    frame_final_btns.pack(fill="x", pady=15)
    canvas.yview_moveto(1.0)

def gerar_pdf():
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path: return
    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []
    s = getSampleStyleSheet()
    elements.append(Paragraph(f"PROPOSTA COMERCIAL: {dados_pdf['cliente']}", s['Title']))
    
    tabela = [
        ["TIPO", "QTD", "JUROS", "PARCELA", "TOTAL"],
        ["IMÓVEL", "-", "-", "-", f"R$ {dados_pdf['total']:,.2f}"],
        ["ENTRADA", "-", "-", "-", f"R$ {dados_pdf['entrada']:,.2f}"],
        ["MENSAL", f"{dados_pdf['m_qtd']}x", f"{dados_pdf['m_juros']:.2f}%", f"R$ {dados_pdf['m_valor']:,.2f}", f"R$ {dados_pdf['m_total']:,.2f}"]
    ]
    if 'a_qtd' in dados_pdf:
        tabela.append(["REFORÇOS", f"{dados_pdf['a_qtd']}x", f"{dados_pdf['a_juros']:.2f}%", f"R$ {dados_pdf['a_valor']:,.2f}", f"R$ {dados_pdf['a_total']:,.2f}"])
    
    t = Table(tabela, colWidths=[80, 40, 60, 90, 100])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    doc.build(elements)
    messagebox.showinfo("Sucesso", "PDF Gerado!")

def recomecar():
    root.destroy()
    os.startfile(__file__)

# --- LAYOUT ---
f1 = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#DCDDE1")
f1.pack(fill="x", pady=5)
e_cliente = criar_campo(f1, "NOME DO CLIENTE")
e_desc = criar_campo(f1, "UNIDADE")
e_valor_imovel = criar_campo(f1, "VALOR TOTAL")
e_entrada = criar_campo(f1, "VALOR ENTRADA")
btn_calc_1 = tk.Button(f1, text="VALIDAR E VER SALDO", command=etapa_1_entrada, bg="#2c3e50", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_1.pack(fill="x", pady=5)
lbl_saldo_res = tk.Label(f1, text="", bg="white", font=("Segoe UI", 9, "bold"), fg="#e67e22")
lbl_saldo_res.pack()

frame_mensal = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#3498db")
e_m_valor = criar_campo(frame_mensal, "DIGITE VALOR PARCELA BASE", "#3498db")
e_m_qtd = criar_campo(frame_mensal, "MESES", "#3498db")
e_m_juros = criar_campo(frame_mensal, "JUROS %", "#3498db")
btn_calc_2 = tk.Button(frame_mensal, text="CALCULAR MENSALIDADES", command=etapa_2_mensal, bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_2.pack(fill="x", pady=5)
lbl_res_mensal = tk.Label(frame_mensal, text="", bg="white", font=("Segoe UI", 9, "bold"))
lbl_res_mensal.pack()

frame_anual = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#e74c3c")
e_a_valor = criar_campo(frame_anual, "DIGITE VALOR REFORÇO BASE", "#e74c3c")
e_a_qtd = criar_campo(frame_anual, "REFORÇOS", "#e74c3c")
e_a_juros = criar_campo(frame_anual, "JUROS %", "#e74c3c")
btn_calc_3 = tk.Button(frame_anual, text="CALCULAR REFORÇOS", command=etapa_3_anual, bg="#e74c3c", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_3.pack(fill="x", pady=5)
lbl_res_anual = tk.Label(frame_anual, text="", bg="white", font=("Segoe UI", 9, "bold"))
lbl_res_anual.pack()

lbl_final = tk.Label(scrollable_frame, text="", bg="#F0F2F5", font=("Segoe UI", 9, "bold"))
lbl_final.pack(pady=5)
frame_final_btns = tk.Frame(scrollable_frame, bg="#F0F2F5")
tk.Button(frame_final_btns, text="PDF", command=gerar_pdf, bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", width=12).pack(side="left", expand=True, padx=5)
tk.Button(frame_final_btns, text="RESET", command=recomecar, bg="#95a5a6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", width=12).pack(side="left", expand=True, padx=5)

root.mainloop()