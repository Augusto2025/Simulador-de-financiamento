import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

# --- CONFIGURAÇÃO DA JANELA ---
root = tk.Tk()
root.title("Simulador Imobiliário")
root.geometry("420x550")
root.configure(bg="#F0F2F5")
root.resizable(False, False)

# Estilo para os inputs
style = ttk.Style()
style.theme_use('clam')

# Variável global para armazenar os dados validados
dados_validos = None

# --- FUNÇÕES ---
def calcular():
    global dados_validos
    try:
        v_imovel = float(e_valor_imovel.get().replace(',', '.'))
        entrada = float(e_entrada.get().replace(',', '.'))
        m_qtd = int(e_m_qtd.get() or 0)
        m_valor = float(e_m_valor.get() or 0)
        a_qtd = int(e_a_qtd.get() or 0)
        a_valor = float(e_a_valor.get() or 0)

        # Validação da Soma: Entrada + valor total das parcelas mensais + valor total dos reforços anuais deve ser igual ao valor do imóvel
        soma = entrada + m_valor + a_valor
        
        # Tolerância de 1 centavo para dízimas
        if abs(soma - v_imovel) < 0.01:
            dados_validos = {
                "cliente": e_cliente.get().upper(),
                "imovel": e_desc.get().upper(),
                "v_imovel": v_imovel,
                "entrada": entrada,
                "m_qtd": m_qtd, "m_valor": m_valor, "m_juros": e_m_juros.get(),
                "a_qtd": a_qtd, "a_valor": a_valor, "a_juros": e_a_juros.get()
            }
            lbl_status.config(text=f"CONFERE! Total: R$ {soma:,.2f}", fg="#27ae60")
            btn_pdf.config(state="normal", bg="#27ae60")
        else:
            dif = v_imovel - soma
            lbl_status.config(text=f"ERRO: Falta R$ {dif:,.2f}", fg="#d35400")
            btn_pdf.config(state="disabled", bg="#bdc3c7")
            messagebox.showerror("Erro de Soma", f"A soma (R$ {soma:,.2f}) não bate com o valor do imóvel.")
    except ValueError:
        messagebox.showerror("Erro", "Preencha todos os campos com números válidos.")

def gerar_pdf():
    if not dados_validos: return
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path: return
    
    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []
    s = getSampleStyleSheet()
    
    elements.append(Paragraph(f"PROPOSTA: {dados_validos['cliente']}", s['Title']))
    elements.append(Paragraph(f"Imóvel: {dados_validos['imovel']}", s['Normal']))
    elements.append(Spacer(1, 15))

    tabela_data = [
        ["CONDIÇÃO", "DETALHE", "VALOR"],
        ["VALOR TOTAL", "-", f"R$ {dados_validos['v_imovel']:,.2f}"],
        ["ENTRADA", "-", f"R$ {dados_validos['entrada']:,.2f}"],
        ["MENSAIS", f"{dados_validos['m_qtd']}x (Juros: {dados_validos['m_juros']}%)", f"R$ {dados_validos['m_valor']:,.2f}"],
        ["ANUAIS", f"{dados_validos['a_qtd']}x (Juros: {dados_validos['a_juros']}%)", f"R$ {dados_validos['a_valor']:,.2f}"]
    ]
    
    t = Table(tabela_data, colWidths=[120, 180, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0984E3")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 8)
    ]))
    elements.append(t)
    doc.build(elements)
    messagebox.showinfo("Sucesso", "PDF Gerado com sucesso!")

# --- UI (INTERFACE) ---
main_frame = tk.Frame(root, bg="white", padx=15, pady=10, highlightthickness=1, highlightbackground="#DCDDE1")
main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

def criar_campo(pai, label, row, col, colspan=1, width=20):
    lbl = tk.Label(pai, text=label, bg="white", fg="#636E72", font=("Segoe UI", 8))
    lbl.grid(row=row, column=col, columnspan=colspan, sticky="w", pady=(2,0))
    ent = ttk.Entry(pai, width=width)
    ent.grid(row=row+1, column=col, columnspan=colspan, sticky="we", pady=(0,5), padx=2)
    return ent

# Identificação
e_cliente = criar_campo(main_frame, "Nome do Cliente", 0, 0, 2)
e_desc = criar_campo(main_frame, "Empreendimento / Unidade", 2, 0, 2)

# Valores Base
e_valor_imovel = criar_campo(main_frame, "Valor Total do Imóvel", 4, 0)
e_entrada = criar_campo(main_frame, "Valor da Entrada", 4, 1)

# Divisão Mensal e Anual
tk.Label(main_frame, text="CONDIÇÕES MENSAIS", bg="white", fg="#0984E3", font=("Segoe UI", 8, "bold")).grid(row=6, column=0, sticky="w", pady=(10,0))
e_m_qtd = criar_campo(main_frame, "Qtd Parcelas", 7, 0)
e_m_valor = criar_campo(main_frame, "Valor Parcela", 9, 0)
e_m_juros = criar_campo(main_frame, "Juros %", 11, 0)

tk.Label(main_frame, text="CONDIÇÕES ANUAIS", bg="white", fg="#D63031", font=("Segoe UI", 8, "bold")).grid(row=6, column=1, sticky="w", pady=(10,0))
e_a_qtd = criar_campo(main_frame, "Qtd Reforços", 7, 1)
e_a_valor = criar_campo(main_frame, "Valor Reforço", 9, 1)
e_a_juros = criar_campo(main_frame, "Juros %", 11, 1)

# Botões e Status
btn_calc = tk.Button(main_frame, text="CONFERIR SOMA", command=calcular, bg="#2D3436", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", pady=5)
btn_calc.grid(row=13, column=0, columnspan=2, sticky="we", pady=15)

lbl_status = tk.Label(main_frame, text="Aguardando cálculo...", bg="#F1F2F6", font=("Segoe UI", 8, "bold"))
lbl_status.grid(row=14, column=0, columnspan=2, sticky="we", pady=2)

btn_pdf = tk.Button(main_frame, text="GERAR PDF", command=gerar_pdf, bg="#bdc3c7", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", state="disabled", pady=5)
btn_pdf.grid(row=15, column=0, columnspan=2, sticky="we", pady=5)

root.mainloop()