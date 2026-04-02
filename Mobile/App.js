import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, ScrollView, 
  Alert, StyleSheet, KeyboardAvoidingView, Platform, SafeAreaView,
  useColorScheme // 1. Importar o hook de tema
} from 'react-native';

import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';

export default function App() {
  // 2. Detectar se o sistema está no modo 'dark' ou 'light'
  const colorScheme = useColorScheme();
  const isDarkMode = colorScheme === 'dark';

  // 3. Definir paleta de cores dinâmica
  const theme = {
    background: isDarkMode ? '#121212' : '#F0F2F5',
    card: isDarkMode ? '#1E1E1E' : '#FFFFFF',
    text: isDarkMode ? '#FFFFFF' : '#2c3e50',
    inputText: isDarkMode ? '#E0E0E0' : '#333',
    inputBorder: isDarkMode ? '#333' : '#eee',
    label: isDarkMode ? '#bbb' : '#95a5a6',
    placeholder: isDarkMode ? '#666' : '#ccc',
  };

  const [etapa, setEtapa] = useState(1);
  const [dados, setDados] = useState({
    cliente: '', imovel: '', valorTotal: '', entrada: '',
    capMeses: '', capJuros: '', mValorBase: '', mQtd: '', mJuros: '',
    aValorBase: '', aQtd: '', aJuros: ''
  });

  const [calculos, setCalculos] = useState({
    saldoDevedor: 0, saldoInicial: 0, valorFuturo: 0, parcelaMensal: 0, parcelaAnual: 0
  });

  // --- UTILITÁRIOS ---
  const formatarMoeda = (valor) => {
    if (valor === null || valor === undefined || isNaN(valor)) return 'R$ 0,00';
    return 'R$ ' + valor.toFixed(2).replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
  };

  const converterParaFloat = (texto) => {
    if (!texto) return 0;
    const limpo = texto.toString().replace(/\D/g, '');
    return (parseFloat(limpo) / 100) || 0;
  };

  const handleMoedaInput = (valorRaw, campo) => {
    const apenasNumeros = valorRaw.replace(/\D/g, '');
    setDados(prev => ({ ...prev, [campo]: apenasNumeros }));
  };

  const voltarEtapa = () => {
    if (etapa === 2) {
      setDados(prev => ({ ...prev, capMeses: '', capJuros: '' }));
      setCalculos(prev => ({ ...prev, valorFuturo: 0, saldoDevedor: prev.saldoInicial }));
      setEtapa(1);
    } 
    else if (etapa === 3) {
      setDados(prev => ({ ...prev, mValorBase: '', mQtd: '', mJuros: '' }));
      setCalculos(prev => ({ ...prev, parcelaMensal: 0 }));
      setEtapa(calculos.valorFuturo > 0 ? 2 : 1);
    } 
    else if (etapa === 4) {
      setDados(prev => ({ ...prev, aValorBase: '', aQtd: '', aJuros: '' }));
      setCalculos(prev => ({ ...prev, parcelaAnual: 0 }));
      setEtapa(3);
    }
    else if (etapa === 5) {
      setEtapa(calculos.parcelaAnual > 0 ? 4 : 3);
    }
  };

  const gerarPDF = async () => {
    const html = `
      <html>
        <head>
          <style>
            body { font-family: 'Helvetica'; padding: 20px; color: #2c3e50; }
            h1 { text-align: center; color: #2c3e50; }
            .card { border: 1px solid #eee; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
            .row { display: flex; justify-content: space-between; margin-bottom: 5px; border-bottom: 1px solid #f9f9f9; padding-bottom: 5px; }
            .label { font-weight: bold; }
          </style>
        </head>
        <body>
          <h1>Simulação Saldo Zero</h1>
          <div class="card">
            <div class="row"><span class="label">Cliente:</span> <span>${dados.cliente || '---'}</span></div>
            <div class="row"><span class="label">Imóvel:</span> <span>${dados.imovel || '---'}</span></div>
          </div>
          <div class="card">
            <div class="row"><span>Valor do Imóvel:</span> <span>${formatarMoeda(converterParaFloat(dados.valorTotal))}</span></div>
            <div class="row"><span>Entrada:</span> <span>${formatarMoeda(converterParaFloat(dados.entrada))}</span></div>
            ${calculos.valorFuturo > 0 ? `<div class="row"><span>Saldo Capitalizado:</span> <span>${formatarMoeda(calculos.valorFuturo)}</span></div>` : ''}
          </div>
          <div class="card">
            <div class="row"><span class="label">Mensalidades (${dados.mQtd}x):</span> <span>${formatarMoeda(calculos.parcelaMensal)}</span></div>
            ${calculos.parcelaAnual > 0 ? `<div class="row"><span class="label">Reforços Anuais (${dados.aQtd}x):</span> <span>${formatarMoeda(calculos.parcelaAnual)}</span></div>` : ''}
          </div>
        </body>
      </html>
    `;
    try {
      const { uri } = await Print.printToFileAsync({ html });
      await Sharing.shareAsync(uri);
    } catch (e) { Alert.alert("Erro", "Falha ao gerar PDF"); }
  };

  const gerarExcel = async () => {
    try {
      let csv = "\ufeff"; 
      csv += `Cliente;${dados.cliente || '---'}\n`;
      csv += `Imovel;${dados.imovel || '---'}\n\n`;
      csv += "Descricao;Qtd;Juros %;Parcela\n";
      csv += `Mensalidades;${dados.mQtd};${dados.mJuros}%;${calculos.parcelaMensal.toFixed(2).replace('.', ',')}\n`;
      
      if (calculos.parcelaAnual > 0) {
        csv += `Anuais;${dados.aQtd};${dados.aJuros}%;${calculos.parcelaAnual.toFixed(2).replace('.', ',')}\n`;
      }

      const fileUri = FileSystem.cacheDirectory + "Simulacao.csv";
      await FileSystem.writeAsStringAsync(fileUri, csv, { encoding: FileSystem.EncodingType.UTF8 });
      await Sharing.shareAsync(fileUri);
    } catch (e) { 
      Alert.alert("Erro", "Falha ao gerar Excel"); 
    }
  };

  const validarEtapa1 = () => {
    const total = converterParaFloat(dados.valorTotal);
    if (total <= 0) return Alert.alert("Erro", "Informe o Valor Total.");
    const saldo = total - converterParaFloat(dados.entrada);
    setCalculos(prev => ({ ...prev, saldoDevedor: saldo, saldoInicial: saldo }));
    Alert.alert("Confirmação", "Deseja capitalizar o saldo?", [
      { text: "NÃO", onPress: () => setEtapa(3) },
      { text: "SIM", onPress: () => setEtapa(2) }
    ]);
  };

  const calcularCapitalizacao = () => {
    const n = parseInt(dados.capMeses) || 0;
    const i = parseFloat(dados.capJuros.replace(',', '.')) / 100 || 0;
    const vf = calculos.saldoDevedor * Math.pow((1 + i), n);
    setCalculos(prev => ({ ...prev, valorFuturo: vf, saldoDevedor: vf }));
    setEtapa(3);
  };

  const calcularMensal = () => {
    const pBase = converterParaFloat(dados.mValorBase);
    if (pBase > (calculos.saldoDevedor + 0.01)) {
        return Alert.alert("Valor Inválido", "O Valor Base Mensal não pode ser maior que o Saldo Devedor.");
    }
    const n = parseInt(dados.mQtd) || 0;
    const i = parseFloat(dados.mJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBase * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBase / n) : 0;
    setCalculos(prev => ({ ...prev, parcelaMensal: parcela }));
    const falta = calculos.saldoDevedor - pBase;
    if (falta <= 0.10) { 
        setEtapa(5); 
    } else {
        setDados(prev => ({ ...prev, aValorBase: (falta * 100).toFixed(0) }));
        setEtapa(4);
    }
  };

  const calcularAnual = () => {
    const pBaseA = converterParaFloat(dados.aValorBase);
    const saldoRestante = calculos.saldoDevedor - converterParaFloat(dados.mValorBase);
    if (pBaseA > (saldoRestante + 0.05)) {
        return Alert.alert("Valor Inválido", "O Valor Base Anual excede o saldo restante da simulação.");
    }
    const n = parseInt(dados.aQtd) || 0;
    const i = parseFloat(dados.aJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBaseA * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBaseA / n) : 0;
    setCalculos(prev => ({ ...prev, parcelaAnual: parcela }));
    setEtapa(5);
  };

  const resetGeral = () => {
    setEtapa(1);
    setDados({ cliente: '', imovel: '', valorTotal: '', entrada: '', capMeses: '', capJuros: '', mValorBase: '', mQtd: '', mJuros: '', aValorBase: '', aQtd: '', aJuros: '' });
    setCalculos({ saldoDevedor: 0, saldoInicial: 0, valorFuturo: 0, parcelaMensal: 0, parcelaAnual: 0 });
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={[styles.header, { color: theme.text }]}>Simulador Saldo Zero</Text>

          <Card title="1. Dados Iniciais" theme={theme}>
            <CustomInput label="CLIENTE (OPCIONAL)" theme={theme} value={dados.cliente} onChangeText={t => setDados({...dados, cliente: t})} />
            <CustomInput label="IMÓVEL (OPCIONAL)" theme={theme} value={dados.imovel} onChangeText={t => setDados({...dados, imovel: t})} />
            <CustomInput label="VALOR TOTAL *" theme={theme} keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.valorTotal))} onChangeText={t => handleMoedaInput(t, 'valorTotal')} />
            <CustomInput label="ENTRADA" theme={theme} keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.entrada))} onChangeText={t => handleMoedaInput(t, 'entrada')} />
            {etapa === 1 && <Btn onPress={validarEtapa1} color="#2c3e50" title="PRÓXIMO" />}
            {calculos.saldoInicial > 0 && <Text style={[styles.res, {color: theme.text}]}>Saldo Inicial: {formatarMoeda(calculos.saldoInicial)}</Text>}
          </Card>

          {etapa === 2 && (
            <Card title="2. Capitalização" color="#8e44ad" theme={theme}>
              <CustomInput label="MESES *" theme={theme} keyboardType="numeric" value={dados.capMeses} onChangeText={t => setDados({...dados, capMeses: t})} />
              <CustomInput label="TAXA JUROS % *" theme={theme} keyboardType="numeric" value={dados.capJuros} onChangeText={t => setDados({...dados, capJuros: t})} />
              <View style={styles.rowButtons}>
                <Btn onPress={voltarEtapa} color="#95a5a6" title="VOLTAR" half />
                <Btn onPress={calcularCapitalizacao} color="#8e44ad" title="CALCULAR" half />
              </View>
            </Card>
          )}

          {etapa >= 3 && etapa !== 2 && (
            <Card title="3. Mensalidades" color="#3498db" theme={theme}>
              {calculos.valorFuturo > 0 && (
                <View style={[styles.infoCapBox, {backgroundColor: isDarkMode ? '#2d1b33' : '#f3e5f5'}]}><Text style={styles.infoCapText}>Saldo Capitalizado: {formatarMoeda(calculos.valorFuturo)}</Text></View>
              )}
              <CustomInput label="VALOR BASE MENSAL *" theme={theme} keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.mValorBase))} onChangeText={t => handleMoedaInput(t, 'mValorBase')} />
              <CustomInput label="QUANTIDADE MESES *" theme={theme} keyboardType="numeric" value={dados.mQtd} onChangeText={t => setDados({...dados, mQtd: t})} />
              <CustomInput label="TAXA JUROS % *" theme={theme} keyboardType="numeric" value={dados.mJuros} onChangeText={t => setDados({...dados, mJuros: t})} />
              {etapa === 3 && (
                <View style={styles.rowButtons}>
                  <Btn onPress={voltarEtapa} color="#95a5a6" title="VOLTAR" half />
                  <Btn onPress={calcularMensal} color="#3498db" title="CALCULAR" half />
                </View>
              )}
              {calculos.parcelaMensal > 0 && <Text style={styles.resBlue}>Parcela: {formatarMoeda(calculos.parcelaMensal)}</Text>}
            </Card>
          )}

          {(etapa === 4 || (etapa === 5 && calculos.parcelaAnual > 0)) ? (
            <Card title="4. Anuais/Reforços" color="#e74c3c" theme={theme}>
              <CustomInput label="VALOR BASE ANUAL *" theme={theme} keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.aValorBase))} onChangeText={t => handleMoedaInput(t, 'aValorBase')} />
              <CustomInput label="QTD ANUAIS *" theme={theme} keyboardType="numeric" value={dados.aQtd} onChangeText={t => setDados({...dados, aQtd: t})} />
              <CustomInput label="JUROS % *" theme={theme} keyboardType="numeric" value={dados.aJuros} onChangeText={t => setDados({...dados, aJuros: t})} />
              {etapa === 4 && (
                <View style={styles.rowButtons}>
                  <Btn onPress={voltarEtapa} color="#95a5a6" title="VOLTAR" half />
                  <Btn onPress={calcularAnual} color="#e74c3c" title="CALCULAR" half />
                </View>
              )}
              {calculos.parcelaAnual > 0 && <Text style={styles.resRed}>Parcela Anual: {formatarMoeda(calculos.parcelaAnual)}</Text>}
            </Card>
          ) : null}

          {etapa === 5 && (
            <View style={styles.footer}>
              <Text style={styles.ok}>Simulação Finalizada!</Text>
              <View style={styles.rowExport}>
                <Btn onPress={gerarPDF} color="#27ae60" title="PDF" half />
                <Btn onPress={gerarExcel} color="#107c41" title="EXCEL" half />
              </View>
              <View style={styles.rowButtons}>
                <Btn onPress={voltarEtapa} color="#95a5a6" title="CORRIGIR" half />
                <Btn onPress={resetGeral} color="#e67e22" title="NOVA" half />
              </View>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// --- COMPONENTES ATUALIZADOS ---
const Card = ({ children, title, color = "#2c3e50", theme }) => (
  <View style={[styles.card, { backgroundColor: theme.card, borderTopColor: color }]}>
    <Text style={[styles.cardTitle, { color }]}>{title}</Text>
    {children}
  </View>
);

const CustomInput = ({ label, theme, ...props }) => (
  <View style={styles.inputGap}>
    <Text style={[styles.label, { color: theme.label }]}>{label}</Text>
    <TextInput 
      {...props} 
      style={[styles.input, { color: theme.inputText, borderBottomColor: theme.inputBorder }]} 
      placeholderTextColor={theme.placeholder} 
    />
  </View>
);

const Btn = ({ title, onPress, color, half }) => (
  <TouchableOpacity activeOpacity={0.7} onPress={onPress} style={[styles.btn, { backgroundColor: color, flex: half ? 1 : undefined, marginHorizontal: half ? 5 : 0 }]}>
    <Text style={styles.btnText}>{title}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 },
  card: { padding: 15, borderRadius: 10, marginBottom: 15, borderTopWidth: 4, elevation: 4 },
  cardTitle: { fontWeight: 'bold', marginBottom: 10, fontSize: 13, textTransform: 'uppercase' },
  label: { fontSize: 10, fontWeight: 'bold', marginBottom: 2 },
  input: { borderBottomWidth: 1, paddingVertical: 8, marginBottom: 10, fontSize: 16 },
  inputGap: { marginBottom: 5 },
  btn: { padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  btnText: { color: 'white', fontWeight: 'bold', fontSize: 13 },
  rowButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  rowExport: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 5, width: '100%' },
  footer: { marginTop: 20, alignItems: 'center', paddingBottom: 50 },
  ok: { color: '#27ae60', fontWeight: 'bold', fontSize: 18, marginBottom: 10 },
  res: { textAlign: 'center', fontWeight: 'bold', marginTop: 10 },
  resBlue: { textAlign: 'center', color: '#2980b9', fontWeight: 'bold', marginTop: 10, fontSize: 16 },
  resRed: { textAlign: 'center', color: '#c0392b', fontWeight: 'bold', marginTop: 10, fontSize: 16 },
  infoCapBox: { padding: 10, borderRadius: 6, marginBottom: 15, borderLeftWidth: 3, borderLeftColor: '#8e44ad' },
  infoCapText: { color: '#8e44ad', fontWeight: 'bold', fontSize: 12 }
});