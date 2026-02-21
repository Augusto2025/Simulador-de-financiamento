import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

# --- CONFIGURAÇÃO DA JANELA ---
root = tk.Tk()
root.title("Simulador Progressivo Pro")
root.geometry("420x600")
root.configure(bg="#F0F2F5")

# Variáveis globais
saldo_atual = 0.0
dados_pdf = {}

# --- ESTRUTURA DE SCROLL ---
# Criando um Canvas e uma Scrollbar
canvas = tk.Canvas(root, bg="#F0F2F5", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#F0F2F5")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=380)
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True, padx=10)
scrollbar.pack(side="right", fill="y")

# --- FUNÇÕES DE LÓGICA ---

def etapa_1_entrada():
    global saldo_atual
    try:
        total = float(e_valor_imovel.get().replace(',', '.'))
        entrada = float(e_entrada.get().replace(',', '.'))
        
        if entrada > total:
            messagebox.showerror("Erro", "A entrada não pode ser maior que o imóvel!")
            return

        saldo_atual = total - entrada
        dados_pdf.update({
            'total': total, 'entrada': entrada,
            'cliente': e_cliente.get().upper(), 'imovel': e_desc.get().upper()
        })

        lbl_saldo_1.config(text=f"Saldo Restante: R$ {saldo_atual:,.2f}", fg="#2c3e50")
        frame_mensal.pack(fill="x", pady=10)
        # Auto-scroll para baixo
        canvas.yview_moveto(0.3)
    except:
        messagebox.showerror("Erro", "Insira valores válidos na Etapa 1")

def etapa_2_mensal():
    global saldo_atual
    try:
        qtd = int(e_m_qtd.get() or 0)
        valor = float(e_m_valor.get() or 0)
        total_mensal = qtd * valor
        
        if total_mensal > (saldo_atual + 0.01):
            messagebox.showerror("Erro", "O valor das mensais excede o saldo!")
            return

        saldo_atual -= total_mensal
        dados_pdf.update({'m_qtd': qtd, 'm_valor': valor, 'm_juros': e_m_juros.get()})

        lbl_saldo_2.config(text=f"Saldo Restante: R$ {saldo_atual:,.2f}", fg="#2c3e50")
        
        if saldo_atual > 0.01:
            frame_anual.pack(fill="x", pady=10)
            btn_pdf_final.pack_forget()
            canvas.yview_moveto(1.0)
        else:
            finalizar_fluxo()
    except:
        messagebox.showerror("Erro", "Valores inválidos na Etapa Mensal")

def etapa_3_anual():
    global saldo_atual
    try:
        qtd = int(e_a_qtd.get() or 0)
        valor = float(e_a_valor.get() or 0)
        total_anual = qtd * valor
        
        if abs(total_anual - saldo_atual) > 0.05:
            messagebox.showwarning("Atenção", f"O valor não zera o saldo!\nFalta: R$ {saldo_atual-total_anual:,.2f}")
            return

        saldo_atual = 0 # Zerado
        dados_pdf.update({'a_qtd': qtd, 'a_valor': valor, 'a_juros': e_a_juros.get()})
        finalizar_fluxo()
    except:
        messagebox.showerror("Erro", "Valores inválidos na Etapa Anual")

def finalizar_fluxo():
    lbl_final.config(text="✓ FLUXO FINALIZADO!", fg="#27ae60")
    btn_pdf_final.pack(fill="x", pady=10)
    canvas.yview_moveto(1.0)

def gerar_pdf():
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path: return
    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []
    s = getSampleStyleSheet()
    
    elements.append(Paragraph(f"PROPOSTA COMERCIAL: {dados_pdf['cliente']}", s['Title']))
    elements.append(Spacer(1, 15))

    tabela = [
        ["ETAPA", "DETALHE", "VALOR"],
        ["VALOR TOTAL", "-", f"R$ {dados_pdf['total']:,.2f}"],
        ["ENTRADA", "-", f"R$ {dados_pdf['entrada']:,.2f}"],
        ["MENSAIS", f"{dados_pdf['m_qtd']}x (Juros: {dados_pdf.get('m_juros',0)}%)", f"R$ {dados_pdf['m_valor']:,.2f}"],
        ["ANUAIS", f"{dados_pdf.get('a_qtd',0)}x (Juros: {dados_pdf.get('a_juros',0)}%)", f"R$ {dados_pdf.get('a_valor',0):,.2f}"],
        ["RESULTADO", "Saldo Final", "R$ 0,00"]
    ]
    
    t = Table(tabela, colWidths=[100, 180, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (2,0), (2,-1), 'RIGHT')
    ]))
    elements.append(t)
    doc.build(elements)
    messagebox.showinfo("Sucesso", "PDF Gerado!")

# --- UI INTERFACE ---

def criar_campo(pai, label, cor_label="#636E72"):
    lbl = tk.Label(pai, text=label, bg="white", fg=cor_label, font=("Segoe UI", 7, "bold"))
    lbl.pack(anchor="w")
    ent = ttk.Entry(pai)
    ent.pack(fill="x", pady=(0, 5))
    return ent

# ETAPA 1: BASE
frame_base = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#DCDDE1")
frame_base.pack(fill="x", pady=5)

e_cliente = criar_campo(frame_base, "NOME DO CLIENTE")
e_desc = criar_campo(frame_base, "DESCRIÇÃO DO IMÓVEL")
e_valor_imovel = criar_campo(frame_base, "VALOR DO IMÓVEL (R$)")
e_entrada = criar_campo(frame_base, "VALOR DA ENTRADA (R$)")

tk.Button(frame_base, text="CALCULAR SALDO", command=etapa_1_entrada, bg="#2c3e50", fg="white", relief="flat", font=("Segoe UI", 8, "bold")).pack(fill="x", pady=5)
lbl_saldo_1 = tk.Label(frame_base, text="", bg="white", font=("Segoe UI", 8, "bold"))
lbl_saldo_1.pack()

# ETAPA 2: MENSAL (Oculta)
frame_mensal = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#3498db")
e_m_qtd = criar_campo(frame_mensal, "QTD MENSALIDADES", "#3498db")
e_m_valor = criar_campo(frame_mensal, "VALOR DA PARCELA", "#3498db")
e_m_juros = criar_campo(frame_mensal, "JUROS MENSAL %", "#3498db")
tk.Button(frame_mensal, text="ABATER MENSALIDADES", command=etapa_2_mensal, bg="#3498db", fg="white", relief="flat", font=("Segoe UI", 8, "bold")).pack(fill="x", pady=5)
lbl_saldo_2 = tk.Label(frame_mensal, text="", bg="white", font=("Segoe UI", 8, "bold"))
lbl_saldo_2.pack()

# ETAPA 3: ANUAL (Oculta)
frame_anual = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#e74c3c")
e_a_qtd = criar_campo(frame_anual, "QTD ANUAIS/REFORÇOS", "#e74c3c")
e_a_valor = criar_campo(frame_anual, "VALOR DO REFORÇO", "#e74c3c")
e_a_juros = criar_campo(frame_anual, "JUROS ANUAL %", "#e74c3c")
tk.Button(frame_anual, text="ABATER ANUAIS", command=etapa_3_anual, bg="#e74c3c", fg="white", relief="flat", font=("Segoe UI", 8, "bold")).pack(fill="x", pady=5)

# FINALIZAÇÃO
lbl_final = tk.Label(scrollable_frame, text="", bg="#F0F2F5", font=("Segoe UI", 9, "bold"))
lbl_final.pack(pady=5)
btn_pdf_final = tk.Button(scrollable_frame, text="GERAR PDF OFICIAL", command=gerar_pdf, bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), relief="flat")

root.mainloop()