import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json, subprocess, os, sys, re, pandas as pd
from datetime import datetime
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
saldo_inicial_backup = 0.0 
dados_pdf = {}

root = tk.Tk()
root.title("Financiamento Imobiliário - Saldo Zero")
root.geometry("450x620")
root.configure(bg="#F0F2F5")
root.resizable(False, False)

# --- ÍCONE ---
try:
    icon_path = resource_path("img/Saldo-Zero-Logo.ico")
    if os.path.exists(icon_path): root.iconbitmap(icon_path)
except: pass

# --- LÓGICA DE FORMATAÇÃO MOEDA ---

def formatar_moeda(event):
    entry = event.widget
    valor = entry.get()
    apenas_numeros = re.sub(r'\D', '', valor)
    if apenas_numeros == "":
        entry.delete(0, tk.END)
        return
    valor_float = float(apenas_numeros) / 100
    valor_formatado = f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    entry.delete(0, tk.END)
    entry.insert(0, valor_formatado)

def converter_para_float(texto):
    limpo = re.sub(r'[R$\s.]', '', texto).replace(',', '.')
    return float(limpo) if limpo else 0.0

# --- FUNÇÕES DE LIMPEZA E RESET ---

def limpar_campos(lista_campos):
    for campo in lista_campos:
        campo.delete(0, tk.END)

def reset_geral():
    global saldo_devedor_base, saldo_inicial_backup, dados_pdf
    saldo_devedor_base = 0.0
    saldo_inicial_backup = 0.0
    dados_pdf = {}
    limpar_campos([e_cliente, e_desc, e_valor_imovel, e_entrada, 
                    e_cap_meses, e_cap_juros,
                    e_m_valor, e_m_qtd, e_m_juros, 
                    e_a_valor, e_a_qtd, e_a_juros])
    lbl_saldo_res.config(text="", fg="#e67e22")
    lbl_res_cap.config(text="")
    lbl_res_mensal.config(text="")
    lbl_res_anual.config(text="")
    lbl_final.config(text="")
    btn_calc_1.config(state="normal", text="VALIDAR E VER SALDO")
    btn_calc_cap.config(state="normal", text="CALCULAR VALOR FUTURO")
    btn_calc_2.config(state="normal", text="CALCULAR MENSALIDADES")
    btn_calc_3.config(state="normal", text="CALCULAR ANUAL")
    frame_cap.pack_forget()
    frame_mensal.pack_forget()
    frame_anual.pack_forget()
    frame_final_btns.pack_forget()
    canvas.yview_moveto(0.0)

# --- LÓGICA DE NAVEGAÇÃO ---

def etapa_1_entrada():
    global saldo_devedor_base, saldo_inicial_backup
    try:
        total = converter_para_float(e_valor_imovel.get())
        entrada = converter_para_float(e_entrada.get())
        saldo_devedor_base = total - entrada
        saldo_inicial_backup = saldo_devedor_base 
        
        dados_pdf.update({'total': total, 'entrada': entrada, 'cliente': e_cliente.get().upper(), 'imovel': e_desc.get().upper()})
        lbl_saldo_res.config(text=f"SALDO INICIAL: R$ {saldo_devedor_base:,.2f}", fg="#e67e22")
        btn_calc_1.config(text="✓ DADOS VALIDADOS", state="disabled")
        
        pergunta = messagebox.askyesno("Valor Futuro", "Deseja calcular o Valor Futuro (capitalização) antes de prosseguir?")
        if pergunta:
            frame_cap.pack(fill="x", pady=10)
            canvas.yview_moveto(0.2)
        else:
            frame_mensal.pack(fill="x", pady=10)
            canvas.yview_moveto(0.3)
    except: messagebox.showerror("Erro", "Valores inválidos.")

def etapa_capitalizacao():
    global saldo_devedor_base
    try:
        n = int(e_cap_meses.get() or 0)
        i = float(e_cap_juros.get().replace(',', '.') or 0) / 100
        valor_futuro =  saldo_devedor_base * ((1 + i) ** n)
        saldo_devedor_base = valor_futuro 
        
        lbl_res_cap.config(text=f"VALOR FUTURO ACUMULADO: R$ {valor_futuro:,.2f}", fg="#8e44ad")
        
        dados_pdf.update({'cap_n': n, 'cap_j': i*100, 'cap_total': valor_futuro, 'is_vf': True})
        btn_calc_cap.config(text="✓ VALOR FUTURO CALCULADO", state="disabled")
        frame_mensal.pack(fill="x", pady=10)
        canvas.yview_moveto(0.5)
    except: messagebox.showerror("Erro", "Dados de capitalização inválidos.")

def etapa_2_mensal():
    global saldo_devedor_base
    try:
        p_base = converter_para_float(e_m_valor.get())
        if p_base > (saldo_devedor_base + 0.05):
            messagebox.showwarning("Valor Excedido", f"O valor base total não pode ser maior que o Saldo (R$ {saldo_devedor_base:,.2f})!")
            return

        n = int(e_m_qtd.get() or 0)
        i = float(e_m_juros.get().replace(',', '.') or 0) / 100
        
        if n > 0:
            if i > 0:
                parcela_com_juros = p_base * (i * (1 + i) ** n) / ((1 + i) ** n - 1)
            else:
                parcela_com_juros = p_base / n
        else:
            parcela_com_juros = 0
        
        lbl_res_mensal.config(text=f"PARCELA C/ JUROS: R$ {parcela_com_juros:,.2f}", fg="#1e3799")
        
        dados_pdf.update({
            'm_base': p_base, 
            'm_qtd': n, 
            'm_valor': parcela_com_juros, 
            'm_juros': i*100,
            'm_abatido': p_base
        })
        
        btn_calc_2.config(text="✓ MENSAL CALCULADO", state="disabled")
        
        falta = round(saldo_devedor_base - p_base, 2)
        if falta <= 0.05:
             finalizar_fluxo()
        else:
            valor_sugerido = f"R$ {falta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            e_a_valor.delete(0, tk.END)
            e_a_valor.insert(0, valor_sugerido)
            frame_anual.pack(fill="x", pady=10)
            root.update_idletasks()
            canvas.yview_moveto(0.8)
    except Exception as e: 
        messagebox.showerror("Erro", f"Erro no cálculo mensal: {e}")

def etapa_3_anual():
    try:
        p_base_a = converter_para_float(e_a_valor.get())
        m_abatido = dados_pdf.get('m_abatido', 0)
        saldo_restante = round(saldo_devedor_base - m_abatido, 2)

        if p_base_a > (saldo_restante + 0.05):
            messagebox.showwarning("Valor Excedido", f"O Valor Anual não pode ser maior que o saldo restante (R$ {saldo_restante:,.2f})!")
            return

        n_a = int(e_a_qtd.get() or 0)
        i_a = float(e_a_juros.get().replace(',', '.') or 0) / 100
        
        if n_a > 0:
            if i_a > 0:
                parcela_anual_com_juros = p_base_a * (i_a * (1 + i_a) ** n_a) / ((1 + i_a) ** n_a - 1)
            else:
                parcela_anual_com_juros = p_base_a / n_a
        else:
            parcela_anual_com_juros = 0
            
        lbl_res_anual.config(text=f"ANUAL C/ JUROS: R$ {parcela_anual_com_juros:,.2f}", fg="#b71540")
        
        dados_pdf.update({
            'a_base': p_base_a, 
            'a_qtd': n_a, 
            'a_valor': parcela_anual_com_juros, 
            'a_juros': i_a*100
        })
        
        btn_calc_3.config(text="✓ ANUAL CALCULADO", state="disabled")
        finalizar_fluxo()
    except Exception as e: 
        messagebox.showerror("Erro", f"Erro no cálculo anual: {e}")

# --- FUNÇÕES DE VOLTAR ---

def voltar_etapa_cap():
    global saldo_devedor_base
    saldo_devedor_base = saldo_inicial_backup 
    lbl_saldo_res.config(text=f"SALDO INICIAL: R$ {saldo_devedor_base:,.2f}", fg="#e67e22")
    limpar_campos([e_cap_meses, e_cap_juros])
    lbl_res_cap.config(text="")
    btn_calc_cap.config(state="normal", text="CALCULAR VALOR FUTURO")
    frame_cap.pack_forget()
    btn_calc_1.config(state="normal", text="VALIDAR E VER SALDO")
    canvas.yview_moveto(0.0)

def voltar_etapa_1():
    limpar_campos([e_m_valor, e_m_qtd, e_m_juros])
    frame_mensal.pack_forget()
    lbl_res_mensal.config(text="")
    btn_calc_2.config(state="normal", text="CALCULAR MENSALIDADES")
    if not frame_cap.winfo_ismapped():
        btn_calc_1.config(state="normal", text="VALIDAR E VER SALDO")
        canvas.yview_moveto(0.0)
    else:
        btn_calc_cap.config(state="normal", text="CALCULAR VALOR FUTURO")
        canvas.yview_moveto(0.2)

def voltar_etapa_2():
    limpar_campos([e_a_valor, e_a_qtd, e_a_juros])
    frame_anual.pack_forget()
    lbl_res_anual.config(text="")
    btn_calc_3.config(state="normal", text="CALCULAR ANUAL")
    btn_calc_2.config(state="normal", text="CALCULAR MENSALIDADES")
    canvas.yview_moveto(0.5)

# --- EXPORTAÇÃO ---

def gerar_pdf():
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path: return
    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []
    s = getSampleStyleSheet()
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    elements.append(Paragraph(f"<para align='right'><font size='8'>{agora}</font></para>", s['Normal']))
    elements.append(Paragraph(f"PROPOSTA COMERCIAL", s['Title']))
    elements.append(Paragraph(f"<b>CLIENTE:</b> {dados_pdf.get('cliente', '')}", s['Normal']))
    elements.append(Paragraph(f"<b>IMÓVEL:</b> {dados_pdf.get('imovel', '')}", s['Normal']))
    elements.append(Spacer(1, 12))
    
    tabela = [
        ["DESCRIÇÃO", "QTD", "JUROS %", "VALOR BASE", "TOTAL"],
        ["VALOR TOTAL", "-", "-", "-", f"R$ {dados_pdf.get('total', 0):,.2f}"],
        ["ENTRADA", "-", "-", "-", f"R$ {dados_pdf.get('entrada', 0):,.2f}"]
    ]
    
    if 'cap_total' in dados_pdf:
        tabela.append(["VALOR FUTURO", f"{dados_pdf['cap_n']}m", f"{dados_pdf['cap_j']:.2f}%", "-", f"R$ {dados_pdf['cap_total']:,.2f}"])
    
    if 'm_valor' in dados_pdf:
        tabela.append(["MENSALIDADES", f"{dados_pdf['m_qtd']}x", f"{dados_pdf['m_juros']:.2f}%", f"R$ {dados_pdf['m_base']:,.2f}", f"R$ {dados_pdf['m_valor']:,.2f}"])
    
    if 'a_valor' in dados_pdf:
        tabela.append(["ANUAIS", f"{dados_pdf['a_qtd']}x", f"{dados_pdf['a_juros']:.2f}%", f"R$ {dados_pdf['a_base']:,.2f}", f"R$ {dados_pdf['a_valor']:,.2f}"])
    
    t = Table(tabela, colWidths=[100, 50, 70, 110, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t)
    doc.build(elements)
    messagebox.showinfo("Sucesso", "PDF Gerado!")

def gerar_excel():
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if not path: return
    try:
        tabela_dados = [
            {"DESCRIÇÃO": "VALOR TOTAL", "PARCELA C/ JUROS": dados_pdf.get('total', 0)},
            {"DESCRIÇÃO": "ENTRADA", "PARCELA C/ JUROS": dados_pdf.get('entrada', 0)}
        ]
        if 'cap_total' in dados_pdf:
            tabela_dados.append({"DESCRIÇÃO": "VALOR FUTURO", "QTD": f"{dados_pdf['cap_n']}m", "JUROS %": dados_pdf['cap_j'], "PARCELA C/ JUROS": dados_pdf['cap_total']})
        if 'm_valor' in dados_pdf:
            tabela_dados.append({"DESCRIÇÃO": "MENSALIDADES", "QTD": f"{dados_pdf['m_qtd']}x", "JUROS %": dados_pdf['m_juros'], "VALOR BASE": dados_pdf['m_base'], "PARCELA C/ JUROS": dados_pdf['m_valor']})
        if 'a_valor' in dados_pdf:
            tabela_dados.append({"DESCRIÇÃO": "ANUAL", "QTD": f"{dados_pdf['a_qtd']}x", "JUROS %": dados_pdf['a_juros'], "VALOR BASE": dados_pdf['a_base'], "PARCELA C/ JUROS": dados_pdf['a_valor']})
        
        df = pd.DataFrame(tabela_dados)
        df.to_excel(path, index=False)
        messagebox.showinfo("Sucesso", "Excel Gerado!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar Excel: {e}")

# --- UI HELPER ---

def criar_campo(pai, label, cor="#636E72", moeda=False):
    tk.Label(pai, text=label, bg="white", fg=cor, font=("Segoe UI", 7, "bold")).pack(anchor="w")
    ent = ttk.Entry(pai)
    ent.pack(fill="x", pady=(0, 5))
    if moeda: ent.bind("<KeyRelease>", formatar_moeda)
    return ent

def finalizar_fluxo():
    lbl_final.config(text="✓ SIMULAÇÃO PRONTA", fg="#27ae60")
    frame_final_btns.pack(fill="x", pady=15)
    canvas.yview_moveto(1.0)

# --- LAYOUT PRINCIPAL ---

canvas = tk.Canvas(root, bg="#F0F2F5", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#F0F2F5")
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=410)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True, padx=10)
scrollbar.pack(side="right", fill="y")

f1 = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#DCDDE1")
f1.pack(fill="x", pady=5)
e_cliente = criar_campo(f1, "NOME DO CLIENTE")
e_desc = criar_campo(f1, "IMÓVEL")
e_valor_imovel = criar_campo(f1, "VALOR TOTAL", moeda=True)
e_entrada = criar_campo(f1, "VALOR ENTRADA", moeda=True)
btn_calc_1 = tk.Button(f1, text="VALIDAR E VER SALDO", command=etapa_1_entrada, bg="#2c3e50", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_1.pack(fill="x", pady=5)
lbl_saldo_res = tk.Label(f1, text="", bg="white", font=("Segoe UI", 9, "bold"), fg="#e67e22")
lbl_saldo_res.pack()

frame_cap = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#8e44ad")
e_cap_meses = criar_campo(frame_cap, "MESES", "#8e44ad")
e_cap_juros = criar_campo(frame_cap, "JUROS %", "#8e44ad")
tk.Button(frame_cap, text="← VOLTAR", command=voltar_etapa_cap, bg="#95a5a6", fg="white", font=("Segoe UI", 7, "bold"), relief="flat").pack(fill="x", pady=(0,5))
btn_calc_cap = tk.Button(frame_cap, text="CALCULAR VALOR FUTURO", command=etapa_capitalizacao, bg="#8e44ad", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_cap.pack(fill="x", pady=5)
lbl_res_cap = tk.Label(frame_cap, text="", bg="white", font=("Segoe UI", 9, "bold"))
lbl_res_cap.pack()

frame_mensal = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#3498db")
e_m_valor = criar_campo(frame_mensal, "VALOR PARCELA BASE", "#3498db", moeda=True)
e_m_qtd = criar_campo(frame_mensal, "MESES", "#3498db")
e_m_juros = criar_campo(frame_mensal, "JUROS %", "#3498db")
tk.Button(frame_mensal, text="← VOLTAR", command=voltar_etapa_1, bg="#95a5a6", fg="white", font=("Segoe UI", 7, "bold"), relief="flat").pack(fill="x", pady=(0,5))
btn_calc_2 = tk.Button(frame_mensal, text="CALCULAR MENSALIDADES", command=etapa_2_mensal, bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_2.pack(fill="x", pady=5)
lbl_res_mensal = tk.Label(frame_mensal, text="", bg="white", font=("Segoe UI", 9, "bold"))
lbl_res_mensal.pack()

frame_anual = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#e74c3c")
e_a_valor = criar_campo(frame_anual, "VALOR ANUAL BASE", "#e74c3c", moeda=True)
e_a_qtd = criar_campo(frame_anual, "ANUAL", "#e74c3c")
e_a_juros = criar_campo(frame_anual, "JUROS %", "#e74c3c")
tk.Button(frame_anual, text="← VOLTAR", command=voltar_etapa_2, bg="#95a5a6", fg="white", font=("Segoe UI", 7, "bold"), relief="flat").pack(fill="x", pady=(0,5))
btn_calc_3 = tk.Button(frame_anual, text="CALCULAR ANUAL", command=etapa_3_anual, bg="#e74c3c", fg="white", font=("Segoe UI", 8, "bold"), relief="flat")
btn_calc_3.pack(fill="x", pady=5)
lbl_res_anual = tk.Label(frame_anual, text="", bg="white", font=("Segoe UI", 9, "bold"))
lbl_res_anual.pack()

lbl_final = tk.Label(scrollable_frame, text="", bg="#F0F2F5", font=("Segoe UI", 9, "bold"))
lbl_final.pack(pady=5)
frame_final_btns = tk.Frame(scrollable_frame, bg="#F0F2F5")
tk.Button(frame_final_btns, text="PDF", command=gerar_pdf, bg="#27ae60", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", width=12).pack(side="left", expand=True, padx=2)
tk.Button(frame_final_btns, text="EXCEL", command=gerar_excel, bg="#107c41", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", width=12).pack(side="left", expand=True, padx=2)
tk.Button(frame_final_btns, text="RESET", command=reset_geral, bg="#e67e22", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", width=12).pack(side="left", expand=True, padx=2)

root.mainloop()