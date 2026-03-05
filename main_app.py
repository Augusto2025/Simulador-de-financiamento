import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.utils import platform
from kivy.metrics import dp  # Fundamental para escala no celular

# Correção para o Windows não bugar no teste local
if platform == 'win':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# Configurações de visualização
Window.clearcolor = get_color_from_hex('#F0F2F5')

class SaldoZeroApp(App):
    def build(self):
        # ScrollView ocupando a tela toda com suporte a gestos
        self.root_scroll = ScrollView(do_scroll_x=False, size_hint=(1, 1))
        
        # Layout Principal (o container que vai dentro do scroll)
        # Usamos size_hint_y=None para o scroll funcionar corretamente
        self.container = BoxLayout(
            orientation='vertical', 
            size_hint=(1, None), 
            padding=dp(15), 
            spacing=dp(12)
        )
        self.container.bind(minimum_height=self.container.setter('height'))
        
        # --- ETAPA 1: DADOS INICIAIS ---
        self.box1 = self.criar_card("DADOS INICIAIS", '#2c3e50')
        self.e_cliente = self.criar_input("Nome do Cliente")
        self.e_desc = self.criar_input("Descrição do Imóvel")
        self.e_total = self.criar_input("Valor Total (R$)", 'float')
        self.e_entrada = self.criar_input("Valor Entrada (R$)", 'float')
        self.btn_etapa1 = self.criar_botao("VALIDAR E VER SALDO", '#2c3e50', self.ir_etapa_2)
        self.lbl_saldo = Label(text="", color=get_color_from_hex('#e67e22'), bold=True, size_hint_y=None, height=dp(40), font_size='16sp')
        
        self.adicionar_ao_card(self.box1, [self.e_cliente, self.e_desc, self.e_total, self.e_entrada, self.btn_etapa1, self.lbl_saldo])
        self.container.add_widget(self.box1)

        # --- ETAPA 2: MENSALIDADES (Inicia fora da tela) ---
        self.box2 = self.criar_card("MENSALIDADES", '#3498db')
        self.e_m_valor = self.criar_input("Valor Parcela Base", 'float')
        self.e_m_qtd = self.criar_input("Meses", 'int')
        self.e_m_juros = self.criar_input("Juros Mensais (%)", 'float')
        self.btn_voltar1 = self.criar_botao("← VOLTAR", '#95a5a6', self.voltar_etapa_1)
        self.btn_etapa2 = self.criar_botao("CALCULAR MENSALIDADES", '#3498db', self.ir_etapa_3)
        self.lbl_res_m = Label(text="", color=(0,0,0,1), size_hint_y=None, height=dp(65), halign='center', font_size='15sp')
        self.adicionar_ao_card(self.box2, [self.e_m_valor, self.e_m_qtd, self.e_m_juros, self.btn_voltar1, self.btn_etapa2, self.lbl_res_m])

        # --- ETAPA 3: ANUAIS (Inicia fora da tela) ---
        self.box3 = self.criar_card("REFORÇOS ANUAIS", '#e74c3c')
        self.e_a_valor = self.criar_input("Valor Anual Base", 'float')
        self.e_a_qtd = self.criar_input("Qtd Anos", 'int')
        self.e_a_juros = self.criar_input("Juros Anuais (%)", 'float')
        self.btn_voltar2 = self.criar_botao("← VOLTAR", '#95a5a6', self.voltar_etapa_2)
        self.btn_etapa3 = self.criar_botao("CALCULAR ANUAL", '#e74c3c', self.finalizar)
        self.lbl_res_a = Label(text="", color=(0,0,0,1), size_hint_y=None, height=dp(65), halign='center', font_size='15sp')
        self.adicionar_ao_card(self.box3, [self.e_a_valor, self.e_a_qtd, self.e_a_juros, self.btn_voltar2, self.btn_etapa3, self.lbl_res_a])

        # --- FINAL ---
        self.btn_reset = self.criar_botao("RESET GERAL", '#e67e22', self.reset_geral)

        self.root_scroll.add_widget(self.container)
        return self.root_scroll

    # --- FUNÇÕES DE INTERFACE COM CORREÇÃO DE ESCALA ---
    def criar_card(self, titulo, cor):
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=dp(10))
        box.bind(minimum_height=box.setter('height'))
        box.add_widget(Label(text=titulo, bold=True, color=get_color_from_hex(cor), size_hint_y=None, height=dp(35), font_size='18sp'))
        return box

    def adicionar_ao_card(self, card, widgets):
        for w in widgets: card.add_widget(w)

    def criar_input(self, placeholder, f_type=None):
        return TextInput(hint_text=placeholder, multiline=False, size_hint_y=None, height=dp(50), 
                         input_filter=f_type, padding_y=[dp(12), dp(12)], font_size='16sp')

    def criar_botao(self, texto, cor, acao):
        btn = Button(text=texto, size_hint_y=None, height=dp(55), 
                      background_color=get_color_from_hex(cor), background_normal='', bold=True, font_size='15sp')
        btn.bind(on_press=acao)
        return btn

    # --- LÓGICA DE NAVEGAÇÃO E CÁLCULO ---
    def ir_etapa_2(self, instance):
        try:
            val_total = float(self.e_total.text)
            val_entrada = float(self.e_entrada.text)
            saldo = val_total - val_entrada
            self.lbl_saldo.text = f"SALDO A FINANCIAR: R$ {saldo:,.2f}"
            if self.box2 not in self.container.children:
                self.container.add_widget(self.box2)
        except: self.lbl_saldo.text = "Preencha os valores iniciais!"

    def ir_etapa_3(self, instance):
        try:
            p = float(self.e_m_valor.text)
            n = int(self.e_m_qtd.text)
            i = float(self.e_m_juros.text)/100
            parcela = p * (i * (1 + i) ** n) / ((1 + i) ** n - 1) if i > 0 else p/n
            self.lbl_res_m.text = f"PARCELA C/ JUROS: R$ {parcela:,.2f}\nTOTAL MENSAL: R$ {parcela*n:,.2f}"
            if self.box3 not in self.container.children:
                self.container.add_widget(self.box3)
        except: self.lbl_res_m.text = "Erro nos dados mensais!"

    def finalizar(self, instance):
        try:
            p = float(self.e_a_valor.text)
            n = int(self.e_a_qtd.text)
            i = float(self.e_a_juros.text)/100
            parcela = p * (i * (1 + i) ** n) / ((1 + i) ** n - 1) if i > 0 else p/n
            self.lbl_res_a.text = f"ANUAL C/ JUROS: R$ {parcela:,.2f}\nTOTAL ANUAL: R$ {parcela*n:,.2f}"
            if self.btn_reset not in self.container.children:
                self.container.add_widget(self.btn_reset)
        except: self.lbl_res_a.text = "Erro nos dados anuais!"

    def voltar_etapa_1(self, instance):
        if self.box2 in self.container.children: self.container.remove_widget(self.box2)
        if self.box3 in self.container.children: self.container.remove_widget(self.box3)
        if self.btn_reset in self.container.children: self.container.remove_widget(self.btn_reset)

    def voltar_etapa_2(self, instance):
        if self.box3 in self.container.children: self.container.remove_widget(self.box3)
        if self.btn_reset in self.container.children: self.container.remove_widget(self.btn_reset)

    def reset_geral(self, instance):
        inputs = [self.e_cliente, self.e_desc, self.e_total, self.e_entrada, 
                  self.e_m_valor, self.e_m_qtd, self.e_m_juros, 
                  self.e_a_valor, self.e_a_qtd, self.e_a_juros]
        for i in inputs: i.text = ""
        self.lbl_saldo.text = ""
        self.lbl_res_m.text = ""
        self.lbl_res_a.text = ""
        self.voltar_etapa_1(None)
        self.root_scroll.scroll_y = 1

if __name__ == '__main__':
    SaldoZeroApp().run()