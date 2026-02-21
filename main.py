import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json, subprocess, os, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- FUNÇÃO PARA RESOLVER CAMINHOS DE RECURSOS ---
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# --- SISTEMA DE VERIFICAÇÃO DE LICENÇA ---
def verificar_ativacao():
    try:
        # Captura o HWID da máquina atual
        cmd = 'wmic csproduct get uuid'
        hwid_atual = str(subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip())
        
        # Tenta ler o arquivo de licença
        if not os.path.exists("config.json"):
            messagebox.showerror("Licença", "Arquivo de licença (config.json) não encontrado!")
            return False
            
        with open("config.json", "r") as f:
            dados = json.load(f)
            hwid_autorizado = dados.get("hwid_autorizado")
            
        if hwid_atual == hwid_autorizado:
            return True
        else:
            messagebox.showerror("Acesso Negado", "Este computador não está autorizado a usar este software.")
            return False
    except Exception as e:
        messagebox.showerror("Erro de Segurança", f"Falha na verificação: {e}")
        return False

# --- SE A LICENÇA FOR VÁLIDA, INICIA O PROGRAMA ---
if not verificar_ativacao():
    exit() # Encerra o script se não houver licença

# --- VARIÁVEIS GLOBAIS E LÓGICA DO SIMULADOR ---
saldo_atual = 0.0
dados_pdf = {}

root = tk.Tk()
root.title("Saldo Zero - Simulador de Proposta Comercial")
root.geometry("420x600")
root.configure(bg="#F0F2F5")

try:
    icon_path = resource_path("img/Saldo-Zero-Logo.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
except Exception:
    # Se falhar, o programa continua sem o ícone personalizado
    pass

# --- ESTRUTURA DE SCROLL ---
canvas = tk.Canvas(root, bg="#F0F2F5", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#F0F2F5")

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=380)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True, padx=10)
scrollbar.pack(side="right", fill="y")

# --- FUNÇÕES ---

def etapa_1_entrada():
    global saldo_atual
    try:
        total = float(e_valor_imovel.get().replace(',', '.'))
        entrada = float(e_entrada.get().replace(',', '.'))
        if entrada > total:
            messagebox.showerror("Erro", "A entrada não pode ser maior que o imóvel!")
            return
        saldo_atual = total - entrada
        dados_pdf.update({'total': total, 'entrada': entrada, 'cliente': e_cliente.get().upper(), 'imovel': e_desc.get().upper()})
        lbl_saldo_1.config(text=f"Saldo Restante: R$ {saldo_atual:,.2f}", fg="#2c3e50")
        btn_calc_1.config(state="disabled", text="✓ ETAPA CONCLUÍDA")
        frame_mensal.pack(fill="x", pady=10)
        canvas.yview_moveto(0.3)
    except:
        messagebox.showerror("Erro", "Dados inválidos.")

def etapa_2_mensal():
    global saldo_atual
    try:
        qtd = int(e_m_qtd.get() or 0)
        valor = float(e_m_valor.get() or 0)
        total_m = qtd * valor
        if total_m > (saldo_atual + 0.01):
            messagebox.showerror("Erro", "Valor excede o saldo!")
            return
        saldo_atual -= total_m
        dados_pdf.update({'m_qtd': qtd, 'm_valor': valor, 'm_juros': e_m_juros.get()})
        lbl_saldo_2.config(text=f"Saldo Restante: R$ {saldo_atual:,.2f}", fg="#2c3e50")
        btn_calc_2.config(state="disabled", text="✓ MENSALIDADES OK")
        if saldo_atual > 0.01:
            frame_anual.pack(fill="x", pady=10)
            canvas.yview_moveto(1.0)
        else:
            finalizar_fluxo()
    except:
        messagebox.showerror("Erro", "Dados inválidos.")

def etapa_3_anual():
    global saldo_atual
    try:
        qtd = int(e_a_qtd.get() or 0)
        valor = float(e_a_valor.get() or 0)
        if abs((qtd * valor) - saldo_atual) > 0.05:
            messagebox.showwarning("Atenção", "O valor não zera o saldo!")
            return
        saldo_atual = 0
        dados_pdf.update({'a_qtd': qtd, 'a_valor': valor, 'a_juros': e_a_juros.get()})
        btn_calc_3.config(state="disabled", text="✓ ANUAIS OK")
        finalizar_fluxo()
    except:
        messagebox.showerror("Erro", "Dados inválidos.")

def finalizar_fluxo():
    lbl_final.config(text="✓ FLUXO FINALIZADO!", fg="#27ae60")
    frame_final_btns.pack(fill="x", pady=15)
    canvas.yview_moveto(1.0)

def recomecar():
    if messagebox.askyesno("Recomeçar", "Limpar tudo?"):
        root.destroy() # Para resetar tudo de forma limpa, reiniciamos a interface
        os.startfile(__file__) # Reinicia o próprio script

def gerar_pdf():
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path: return
    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []
    s = getSampleStyleSheet()
    elements.append(Paragraph(f"PROPOSTA COMERCIAL: {dados_pdf['cliente']}", s['Title']))
    tabela = [
        ["ETAPA", "DETALHE", "VALOR"],
        ["TOTAL", "-", f"R$ {dados_pdf['total']:,.2f}"],
        ["ENTRADA", "-", f"R$ {dados_pdf['entrada']:,.2f}"],
        ["MENSAIS", f"{dados_pdf['m_qtd']}x", f"R$ {dados_pdf['m_valor']:,.2f}"],
        ["ANUAIS", f"{dados_pdf.get('a_qtd',0)}x", f"R$ {dados_pdf.get('a_valor',0):,.2f}"],
        ["FINAL", "Saldo", "R$ 0,00"]
    ]
    t = Table(tabela, colWidths=[100, 180, 100])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    doc.build(elements)
    messagebox.showinfo("Sucesso", "PDF Gerado!")

# --- UI ---
def criar_campo(pai, label, cor="#636E72"):
    tk.Label(pai, text=label, bg="white", fg=cor, font=("Segoe UI", 7, "bold")).pack(anchor="w")
    ent = ttk.Entry(pai)
    ent.pack(fill="x", pady=(0, 5))
    return ent

frame_base = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#DCDDE1")
frame_base.pack(fill="x", pady=5)
e_cliente = criar_campo(frame_base, "NOME DO CLIENTE")
e_desc = criar_campo(frame_base, "DESCRIÇÃO DO IMÓVEL")
e_valor_imovel = criar_campo(frame_base, "VALOR DO IMÓVEL")
e_entrada = criar_campo(frame_base, "ENTRADA")
btn_calc_1 = tk.Button(frame_base, text="CALCULAR SALDO", command=etapa_1_entrada, bg="#2c3e50", fg="white", relief="flat", font=("Segoe UI", 8, "bold"))
btn_calc_1.pack(fill="x", pady=5)
lbl_saldo_1 = tk.Label(frame_base, text="", bg="white", font=("Segoe UI", 8, "bold"))
lbl_saldo_1.pack()

frame_mensal = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#3498db")
e_m_valor = criar_campo(frame_mensal, "VALOR PARCELA", "#3498db")
e_m_qtd = criar_campo(frame_mensal, "QTD PARCELAS", "#3498db")
e_m_juros = criar_campo(frame_mensal, "JUROS %", "#3498db")
btn_calc_2 = tk.Button(frame_mensal, text="ABATER MENSALIDADES", command=etapa_2_mensal, bg="#3498db", fg="white", relief="flat", font=("Segoe UI", 8, "bold"))
btn_calc_2.pack(fill="x", pady=5)
lbl_saldo_2 = tk.Label(frame_mensal, text="", bg="white", font=("Segoe UI", 8, "bold"))
lbl_saldo_2.pack()

frame_anual = tk.Frame(scrollable_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#e74c3c")
e_a_valor = criar_campo(frame_anual, "VALOR REFORÇO", "#e74c3c")
e_a_qtd = criar_campo(frame_anual, "QTD REFORÇOS", "#e74c3c")
e_a_juros = criar_campo(frame_anual, "JUROS %", "#e74c3c")
btn_calc_3 = tk.Button(frame_anual, text="ABATER ANUAIS", command=etapa_3_anual, bg="#e74c3c", fg="white", relief="flat", font=("Segoe UI", 8, "bold"))
btn_calc_3.pack(fill="x", pady=5)

lbl_final = tk.Label(scrollable_frame, text="", bg="#F0F2F5", font=("Segoe UI", 9, "bold"))
lbl_final.pack(pady=5)
frame_final_btns = tk.Frame(scrollable_frame, bg="#F0F2F5")
tk.Button(frame_final_btns, text="GERAR PDF", command=gerar_pdf, bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15).pack(side="left", expand=True, fill="x", padx=5)
tk.Button(frame_final_btns, text="RECOMECAR", command=recomecar, bg="#95a5a6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15).pack(side="left", expand=True, fill="x", padx=5)

root.mainloop()