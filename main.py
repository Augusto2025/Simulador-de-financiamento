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
root.title("Saldo Zero - Tabela Price (Juros Compostos)")
root.geometry("420x650")
root.configure(bg="#F0F2F5")

try:
    icon_path = resource_path("img/Saldo-Zero-Logo.ico")
    if os.path.exists(icon_path): root.iconbitmap(icon_path)
except: pass

canvas = tk.Canvas(root, bg="#F0F2F5", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#F0F2F5")
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=380)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True, padx=10)
scrollbar.pack(side="right", fill="y")

# --- LÓGICA FINANCEIRA (PRICE) ---

def etapa_1_entrada():
    global saldo_devedor_base
    try:
        total = float(e_valor_imovel.get().replace(',', '.'))
        entrada = float(e_entrada.get().replace(',', '.'))
        if entrada >= total:
            messagebox.showerror("Erro", "A entrada deve ser menor que o total!")
            return
        saldo_devedor_base = total - entrada
        dados_pdf.update({'total': total, 'entrada': entrada, 'cliente': e_cliente.get().upper(), 'imovel': e_desc.get().upper()})
        lbl_saldo_1.config(text=f"Saldo Devedor: R$ {saldo_devedor_base:,.2f}", fg="#2c3e50")
        btn_calc_1.config(state="disabled", text="✓ VALOR BASE DEFINIDO")
        frame_mensal.pack(fill="x", pady=10)
    except: messagebox.showerror("Erro", "Valores inválidos.")

def etapa_2_mensal():
    try:
        n = int(e_m_qtd.get() or 0)
        i = float(e_m_juros.get().replace(',', '.') or 0) / 100
        
        if i > 0:
            # Fórmula da Tabela Price (Juros Compostos)
            parcela = saldo_devedor_base * (i / (1 - (1 + i)**-n))
        else:
            parcela = saldo_devedor_base / n

        e_m_valor.config(state="normal")
        e_m_valor.delete(0, tk.END)
        e_m_valor.insert(0, f"{parcela:.2f}")
        e_m_valor.config(state="readonly")
        
        dados_pdf.update({'m_qtd': n, 'm_valor': parcela, 'm_juros': i*100})
        btn_calc_2.config(state="disabled", text="✓ MENSALIDADES CALCULADAS")
        frame_anual.pack(fill="x", pady=10)
    except: messagebox.showerror("Erro", "Preencha QTD e JUROS %")

def etapa_3_anual():
    try:
        n = int(e_a_qtd.get() or 0)
        i = float(e_a_juros.get().replace(',', '.') or 0) / 100
        
        # Para reforços anuais (compostos anualmente)
        if i > 0:
            parcela_anual = saldo_devedor_base * (i / (1 - (1 + i)**-n))
        else:
            parcela_anual = saldo_devedor_base / n

        e_a_valor.config(state="normal")
        e_a_valor.delete(0, tk.END)
        e_a_valor.insert(0, f"{parcela_anual:.2f}")
        e_a_valor.config(state="readonly")

        dados_pdf.update({'a_qtd': n, 'a_valor': parcela_anual, 'a_juros': i*100})
        btn_calc_3.config(state="disabled", text="✓ ANUAIS CALCULADAS")
        finalizar_fluxo()
    except: messagebox.showerror("Erro", "Preencha QTD e JUROS %")

# --- UI (Criação de Campos e Layout) ---

def criar_campo(pai, label, cor="#636E72", editavel=True):
    tk.Label(pai, text=label, bg="white", fg=cor, font=("Segoe UI", 7, "bold")).pack(anchor="w")
    ent = ttk.Entry(pai)
    if not editavel: ent.config(state="readonly")
    ent.pack(fill="x", pady=(0, 5))
    return ent

def finalizar_fluxo():
    lbl_final.config(text="✓ CÁLCULOS PRICE FINALIZADOS!", fg="#27ae60")
    frame_final_btns.pack(fill="x", pady=15)

def gerar_pdf():
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path: return
    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []
    s = getSampleStyleSheet()
    elements.append(Paragraph(f"PROPOSTA COMERCIAL (PRICE): {dados_pdf['cliente']}", s['Title']))
    tabela = [
        ["ITEM", "QTD", "TAXA JUROS", "VALOR PARCELA"],
        ["VALOR TOTAL", "-", "-", f"R$ {dados_pdf['total']:,.2f}"],
        ["ENTRADA", "-", "-", f"R$ {dados_pdf['entrada']:,.2f}"],
        ["MENSALIDADES", f"{dados_pdf['m_qtd']}x", f"{dados_pdf['m_juros']:.2f}%", f"R$ {dados_pdf['m_valor']:,.2f}"],
        ["ANUAIS/REFORÇOS", f"{dados_pdf.get('a_qtd',0)}x", f"{dados_pdf.get('a_juros',0):.2f}%", f"R$ {dados_pdf.get('a_valor',0):,.2f}"]
    ]
    t = Table(tabela, colWidths=[110, 60, 70, 120])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    doc.build(elements)
    messagebox.showinfo("Sucesso", "PDF Gerado com Juros Compostos!")

def recomecar():
    root.destroy()
    os.startfile(__file__)

# --- LAYOUT DOS CARDS ---
f1 = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#DCDDE1")
f1.pack(fill="x", pady=5)
e_cliente = criar_campo(f1, "NOME DO CLIENTE")
e_desc = criar_campo(f1, "IMÓVEL / UNIDADE")
e_valor_imovel = criar_campo(f1, "VALOR TOTAL DO IMÓVEL")
e_entrada = criar_campo(f1, "VALOR DE ENTRADA")
btn_calc_1 = tk.Button(f1, text="DEFINIR SALDO BASE", command=etapa_1_entrada, bg="#2c3e50", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_1.pack(fill="x", pady=5)
lbl_saldo_1 = tk.Label(f1, text="", bg="white", font=("Segoe UI", 8, "bold"))
lbl_saldo_1.pack()

frame_mensal = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#3498db")
e_m_qtd = criar_campo(frame_mensal, "Nº DE MESES (n)", "#3498db")
e_m_juros = criar_campo(frame_mensal, "TAXA MENSAL (i) %", "#3498db")
e_m_valor = criar_campo(frame_mensal, "PARCELA PRICE (RESULTADO)", "#3498db", editavel=False)
btn_calc_2 = tk.Button(frame_mensal, text="CALCULAR MENSALIDADES", command=etapa_2_mensal, bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_2.pack(fill="x", pady=5)

frame_anual = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#e74c3c")
e_a_qtd = criar_campo(frame_anual, "Nº DE ANUAIS/REFORÇOS", "#e74c3c")
e_a_juros = criar_campo(frame_anual, "TAXA ANUAL (i) %", "#e74c3c")
e_a_valor = criar_campo(frame_anual, "REFORÇO PRICE (RESULTADO)", "#e74c3c", editavel=False)
btn_calc_3 = tk.Button(frame_anual, text="CALCULAR REFORÇOS", command=etapa_3_anual, bg="#e74c3c", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_3.pack(fill="x", pady=5)

lbl_final = tk.Label(scrollable_frame, text="", bg="#F0F2F5", font=("Segoe UI", 9, "bold"))
lbl_final.pack(pady=5)
frame_final_btns = tk.Frame(scrollable_frame, bg="#F0F2F5")
tk.Button(frame_final_btns, text="GERAR PDF", command=gerar_pdf, bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15).pack(side="left", expand=True, fill="x", padx=5)
tk.Button(frame_final_btns, text="RECOMECAR", command=recomecar, bg="#95a5a6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15).pack(side="left", expand=True, fill="x", padx=5)

root.mainloop()