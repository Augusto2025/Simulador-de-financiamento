import os
import re
from kivy.utils import platform

# Fix para Windows OpenGL 1.1 - Deve ser a primeira configuração
if platform == 'win':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp

# Bibliotecas de Exportação
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
from plyer import storagepath

Window.clearcolor = (1, 1, 1, 1) # Fundo Branco da Janela
if platform == 'win':
    Window.size = (400, 720)

class WhiteCard(BoxLayout):
    """Componente visual para destacar as seções (Cards)"""
    def __init__(self, title, color_hex, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = dp(15)
        self.spacing = dp(8)
        self.bind(minimum_height=self.setter('height'))
        with self.canvas.before:
            Color(0.96, 0.97, 0.98, 1) # Cor de fundo do card (cinza muito claro)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.add_widget(Label(text=title, bold=True, color=get_color_from_hex(color_hex),
                             size_hint_y=None, height=dp(30), font_size='16sp', halign='left'))

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class SaldoZeroApp(App):
    def build(self):
        self.saldo_devedor = 0.0
        self.total_mensal_acumulado = 0.0
        self.dados_pdf = {}

        self.root_scroll = ScrollView(do_scroll_x=False)
        self.container = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(15), spacing=dp(15))
        self.container.bind(minimum_height=self.container.setter('height'))

        # --- ETAPA 1: DADOS INICIAIS ---
        self.card1 = WhiteCard("1. DADOS DO NEGÓCIO", "#2c3e50")
        self.e_cliente = self.criar_input("NOME DO CLIENTE")
        self.e_desc = self.criar_input("DESCRIÇÃO DO IMÓVEL")
        self.e_total = self.criar_input("VALOR TOTAL DO IMÓVEL", moeda=True)
        self.e_entrada = self.criar_input("VALOR DE ENTRADA", moeda=True)
        self.btn_validar = self.criar_botao("AVANÇAR PARA MENSALIDADES", "#2c3e50", self.validar_etapa_1)
        self.lbl_saldo = Label(text="", color=get_color_from_hex('#e67e22'), bold=True, size_hint_y=None, height=dp(30))
        
        for w in [self.e_cliente, self.e_desc, self.e_total, self.e_entrada, self.btn_validar, self.lbl_saldo]:
            self.card1.add_widget(w)
        self.container.add_widget(self.card1)

        # --- ETAPA 2: MENSALIDADES ---
        self.card2 = WhiteCard("2. PLANO MENSAL", "#3498db")
        self.e_m_valor = self.criar_input("PARCELA MENSAL BASE", moeda=True)
        self.e_m_qtd = self.criar_input("QUANTIDADE DE MESES", 'int')
        self.e_m_juros = self.criar_input("JUROS MENSAIS (%)", 'float')
        self.e_m_juros.bind(text=self.calc_mensal_realtime) 
        
        self.lbl_res_m = Label(text="", color=(0,0,0,1), size_hint_y=None, height=dp(50), font_size='14sp', halign='center')
        self.btn_avancar_ou_final = self.criar_botao("VERIFICAR PRÓXIMA ETAPA", "#3498db", self.decidir_proxima_etapa)
        self.btn_voltar_1 = self.criar_botao("← ALTERAR DADOS INICIAIS", "#95a5a6", self.voltar_1)

        for w in [self.e_m_valor, self.e_m_qtd, self.e_m_juros, self.lbl_res_m, self.btn_avancar_ou_final, self.btn_voltar_1]:
            self.card2.add_widget(w)

        # --- ETAPA 3: REFORÇOS ANUAIS ---
        self.card3 = WhiteCard("3. PLANO ANUAL", "#e74c3c")
        self.e_a_valor = self.criar_input("VALOR ANUAL BASE", moeda=True)
        self.e_a_qtd = self.criar_input("QUANTIDADE DE ANOS", 'int')
        self.e_a_juros = self.criar_input("JUROS ANUAIS (%)", 'float')
        self.e_a_juros.bind(text=self.calc_anual_realtime)
        
        self.lbl_res_a = Label(text="", color=(0,0,0,1), size_hint_y=None, height=dp(50), font_size='14sp', halign='center')
        self.btn_voltar_2 = self.criar_botao("← VOLTAR PARA MENSAL", "#95a5a6", self.voltar_2)
        
        for w in [self.e_a_valor, self.e_a_qtd, self.e_a_juros, self.lbl_res_a, self.btn_voltar_2]:
            self.card3.add_widget(w)

        # --- BOTÕES DE FECHAMENTO ---
        self.box_final = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=[0, dp(10)])
        self.box_final.bind(minimum_height=self.box_final.setter('height'))
        self.box_final.add_widget(self.criar_botao("GERAR PDF", "#27ae60", self.gerar_pdf))
        self.box_final.add_widget(self.criar_botao("GERAR EXCEL", "#1f6e43", self.gerar_excel))
        self.box_final.add_widget(self.criar_botao("LIMPAR TUDO", "#d35400", self.reset_total))

        self.root_scroll.add_widget(self.container)
        return self.root_scroll

    def criar_input(self, p, f=None, moeda=False):
        txt = TextInput(hint_text=p, multiline=False, size_hint_y=None, height=dp(48),
                        background_normal='', background_color=(1,1,1,1), padding=[dp(10), dp(12)])
        if moeda: txt.bind(text=self.aplicar_mascara_moeda)
        return txt

    def criar_botao(self, t, c, a):
        btn = Button(text=t, size_hint_y=None, height=dp(52), background_color=get_color_from_hex(c),
                     background_normal='', bold=True, font_size='13sp')
        btn.bind(on_press=a)
        return btn

    def aplicar_mascara_moeda(self, instance, value):
        num = re.sub(r'\D', '', value)
        if num:
            v = float(num) / 100
            instance.text = f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def converter_valor(self, t):
        l = re.sub(r'[R$\s.]', '', t).replace(',', '.')
        return float(l) if l else 0.0

    # --- LÓGICA DE TRANSIÇÃO E CÁLCULOS ---
    def validar_etapa_1(self, *args):
        try:
            total = self.converter_valor(self.e_total.text)
            entrada = self.converter_valor(self.e_entrada.text)
            self.saldo_devedor = total - entrada
            self.lbl_saldo.text = f"SALDO A QUITAR: R$ {self.saldo_devedor:,.2f}"
            if self.card2 not in self.container.children: self.container.add_widget(self.card2)
        except: pass

    def calc_mensal_realtime(self, *args):
        try:
            p_base = self.converter_valor(self.e_m_valor.text)
            n = int(self.e_m_qtd.text or 0)
            i = float(self.e_m_juros.text.replace(',', '.') or 0) / 100
            if n > 0:
                parc = p_base * (i * (1+i)**n) / ((1+i)**n - 1) if i > 0 else p_base/n
                self.total_mensal_acumulado = parc * n
                self.lbl_res_m.text = f"PARCELA: R$ {parc:,.2f}\nTOTAL MENSAL: R$ {self.total_mensal_acumulado:,.2f}"
                self.dados_pdf['m'] = [n, i*100, p_base, parc, self.total_mensal_acumulado]
        except: self.lbl_res_m.text = ""

    def decidir_proxima_etapa(self, *args):
        # Se as mensais já cobrem o saldo, pula para o final
        if self.total_mensal_acumulado >= self.saldo_devedor:
            if self.card3 in self.container.children: self.container.remove_widget(self.card3)
            if self.box_final not in self.container.children: self.container.add_widget(self.box_final)
        else:
            if self.card3 not in self.container.children: self.container.add_widget(self.card3)
            if self.box_final in self.container.children: self.container.remove_widget(self.box_final)

    def calc_anual_realtime(self, *args):
        try:
            p_base = self.converter_valor(self.e_a_valor.text)
            n = int(self.e_a_qtd.text or 0)
            i = float(self.e_a_juros.text.replace(',', '.') or 0) / 100
            if n > 0:
                parc = p_base * (i * (1+i)**n) / ((1+i)**n - 1) if i > 0 else p_base/n
                total_a = parc * n
                self.lbl_res_a.text = f"ANUAL: R$ {parc:,.2f}\nTOTAL ANUAL: R$ {total_a:,.2f}"
                self.dados_pdf['a'] = [n, i*100, p_base, parc, total_a]
                if self.box_final not in self.container.children: self.container.add_widget(self.box_final)
        except: self.lbl_res_a.text = ""

    # --- NAVEGAÇÃO E RESET ---
    def voltar_1(self, *args):
        # Resetar dados da Etapa 2 e 3 ao voltar para a 1
        for i in [self.e_m_valor, self.e_m_qtd, self.e_m_juros, self.e_a_valor, self.e_a_qtd, self.e_a_juros]:
            i.text = ""
        self.lbl_res_m.text = ""
        self.lbl_res_a.text = ""
        self.total_mensal_acumulado = 0.0
        for c in [self.card2, self.card3, self.box_final]:
            if c in self.container.children: self.container.remove_widget(c)

    def voltar_2(self, *args):
        # Resetar dados da Etapa 3 ao voltar para a 2
        for i in [self.e_a_valor, self.e_a_qtd, self.e_a_juros]:
            i.text = ""
        self.lbl_res_a.text = ""
        if self.card3 in self.container.children: self.container.remove_widget(self.card3)
        if self.box_final in self.container.children: self.container.remove_widget(self.box_final)

    def reset_total(self, *args):
        for i in [self.e_cliente, self.e_desc, self.e_total, self.e_entrada]:
            i.text = ""
        self.voltar_1()

    # --- EXPORTAÇÃO ---
    def gerar_pdf(self, *args):
        try:
            nome = f"Proposta_{self.e_cliente.text.replace(' ','_')}.pdf"
            folder = storagepath.get_downloads_dir() if platform == 'android' else "."
            path = os.path.join(folder, nome)
            doc = SimpleDocTemplate(path, pagesize=A4)
            elements = []
            s = getSampleStyleSheet()
            elements.append(Paragraph(f"PROPOSTA: {self.e_cliente.text}", s['Title']))
            elements.append(Paragraph(f"Imóvel: {self.e_desc.text}", s['Normal']))
            
            data = [["TIPO", "QTD", "JUROS", "BASE", "PARCELA", "TOTAL"]]
            if 'm' in self.dados_pdf:
                m = self.dados_pdf['m']
                data.append(["MENSAL", f"{m[0]}x", f"{m[1]:.2f}%", f"R$ {m[2]:,.2f}", f"R$ {m[3]:,.2f}", f"R$ {m[4]:,.2f}"])
            if 'a' in self.dados_pdf:
                a = self.dados_pdf['a']
                data.append(["ANUAL", f"{a[0]}x", f"{a[1]:.2f}%", f"R$ {a[2]:,.2f}", f"R$ {a[3]:,.2f}", f"R$ {a[4]:,.2f}"])
            
            table = Table(data)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.gray),('GRID',(0,0),(-1,-1),1,colors.black)]))
            elements.append(table)
            doc.build(elements)
            self.lbl_res_a.text = "PDF SALVO!"
        except: self.lbl_res_a.text = "Erro ao gerar PDF"

    def gerar_excel(self, *args):
        try:
            nome = f"Planilha_{self.e_cliente.text.replace(' ','_')}.xlsx"
            folder = storagepath.get_downloads_dir() if platform == 'android' else "."
            path = os.path.join(folder, nome)
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Cliente", "Imóvel", "Saldo"])
            ws.append([self.e_cliente.text, self.e_desc.text, self.saldo_devedor])
            wb.save(path)
            self.lbl_res_a.text = "EXCEL SALVO!"
        except: self.lbl_res_a.text = "Erro ao gerar Excel"

if __name__ == '__main__':
    SaldoZeroApp().run()