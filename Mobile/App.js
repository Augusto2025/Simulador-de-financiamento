import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, ScrollView, 
  Alert, StyleSheet, KeyboardAvoidingView, Platform, SafeAreaView 
} from 'react-native';

const FinanceApp = () => {
  const [etapa, setEtapa] = useState(1);
  const [dados, setDados] = useState({
    cliente: '', imovel: '', valorTotal: '', entrada: '',
    capMeses: '', capJuros: '', mValorBase: '', mQtd: '', mJuros: '',
    aValorBase: '', aQtd: '', aJuros: ''
  });

  const [calculos, setCalculos] = useState({
    saldoDevedor: 0, saldoInicial: 0, parcelaMensal: 0, parcelaAnual: 0
  });

  // Formatação manual para não quebrar o Android
  const formatarMoeda = (valor) => {
    if (isNaN(valor)) return 'R$ 0,00';
    return 'R$ ' + valor.toFixed(2).replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
  };

  const converterParaFloat = (texto) => {
    if (!texto) return 0;
    const limpo = texto.toString().replace(/\D/g, '');
    return parseFloat(limpo) / 100;
  };

  const handleMoedaInput = (valorRaw, campo) => {
    const apenasNumeros = valorRaw.replace(/\D/g, '');
    setDados(prev => ({ ...prev, [campo]: apenasNumeros }));
  };

  const resetGeral = () => {
    setEtapa(1);
    setDados({
      cliente: '', imovel: '', valorTotal: '', entrada: '',
      capMeses: '', capJuros: '', mValorBase: '', mQtd: '', mJuros: '',
      aValorBase: '', aQtd: '', aJuros: ''
    });
    setCalculos({ saldoDevedor: 0, saldoInicial: 0, parcelaMensal: 0, parcelaAnual: 0 });
  };

  const validarEtapa1 = () => {
    const total = converterParaFloat(dados.valorTotal);
    const entrada = converterParaFloat(dados.entrada);
    const saldo = total - entrada;
    if (total <= 0) return Alert.alert("Atenção", "Informe o valor do imóvel.");
    setCalculos(prev => ({ ...prev, saldoDevedor: saldo, saldoInicial: saldo }));
    setEtapa(2);
  };

  const calcularMensal = () => {
    const pBase = converterParaFloat(dados.mValorBase);
    const n = parseInt(dados.mQtd) || 0;
    const i = parseFloat(dados.mJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBase * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBase / n) : 0;
    setCalculos(prev => ({ ...prev, parcelaMensal: parcela }));
    const falta = calculos.saldoDevedor - pBase;
    if (falta <= 0.10) setEtapa(4); 
    else { setDados(prev => ({ ...prev, aValorBase: (falta * 100).toFixed(0) })); setEtapa(3); }
  };

  const calcularAnual = () => {
    const pBaseA = converterParaFloat(dados.aValorBase);
    const n = parseInt(dados.aQtd) || 0;
    const i = parseFloat(dados.aJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBaseA * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBaseA / n) : 0;
    setCalculos(prev => ({ ...prev, parcelaAnual: parcela }));
    setEtapa(4);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F0F2F5' }}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={styles.header}>Simulador Financeiro</Text>

          <Card title="1. Dados Iniciais">
            <CustomInput label="CLIENTE" value={dados.cliente} onChangeText={t => setDados({...dados, cliente: t})} />
            <CustomInput label="VALOR IMÓVEL" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.valorTotal))} onChangeText={t => handleMoedaInput(t, 'valorTotal')} />
            <CustomInput label="ENTRADA" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.entrada))} onChangeText={t => handleMoedaInput(t, 'entrada')} />
            {etapa === 1 && <Btn onPress={validarEtapa1} color="#2c3e50" title="PRÓXIMO" />}
            {calculos.saldoInicial > 0 && <Text style={styles.res}>Saldo: {formatarMoeda(calculos.saldoInicial)}</Text>}
          </Card>

          {etapa >= 2 && (
            <Card title="2. Mensalidades" color="#3498db">
              <CustomInput label="VALOR BASE MENSAL" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.mValorBase))} onChangeText={t => handleMoedaInput(t, 'mValorBase')} />
              <CustomInput label="QTD MESES" keyboardType="numeric" value={dados.mQtd} onChangeText={t => setDados({...dados, mQtd: t})} />
              <CustomInput label="JUROS %" keyboardType="numeric" value={dados.mJuros} onChangeText={t => setDados({...dados, mJuros: t})} />
              {etapa === 2 && <Btn onPress={calcularMensal} color="#3498db" title="CALCULAR MENSAL" />}
              {calculos.parcelaMensal > 0 && <Text style={styles.resBlue}>Parcela: {formatarMoeda(calculos.parcelaMensal)}</Text>}
            </Card>
          )}

          {etapa >= 3 && (
            <Card title="3. Anuais/Reforços" color="#e74c3c">
              <CustomInput label="VALOR BASE ANUAL" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.aValorBase))} onChangeText={t => handleMoedaInput(t, 'aValorBase')} />
              <CustomInput label="QTD ANOS" keyboardType="numeric" value={dados.aQtd} onChangeText={t => setDados({...dados, aQtd: t})} />
              <CustomInput label="JUROS %" keyboardType="numeric" value={dados.aJuros} onChangeText={t => setDados({...dados, aJuros: t})} />
              {etapa === 3 && <Btn onPress={calcularAnual} color="#e74c3c" title="CALCULAR ANUAL" />}
              {calculos.parcelaAnual > 0 && <Text style={styles.resRed}>Parcela Anual: {formatarMoeda(calculos.parcelaAnual)}</Text>}
            </Card>
          )}

          {etapa === 4 && (
            <View style={styles.footer}>
              <Text style={styles.ok}>Simulação Finalizada!</Text>
              <Btn onPress={resetGeral} color="#e67e22" title="RECOMEÇAR TUDO" />
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const Card = ({ children, title, color = "#2c3e50" }) => (
  <View style={[styles.card, { borderTopColor: color }]}>
    <Text style={[styles.cardTitle, { color }]}>{title}</Text>
    {children}
  </View>
);

const CustomInput = ({ label, ...props }) => (
  <View style={styles.inputGap}>
    <Text style={styles.label}>{label}</Text>
    <TextInput {...props} style={styles.input} />
  </View>
);

const Btn = ({ title, onPress, color }) => (
  <TouchableOpacity onPress={onPress} style={[styles.btn, { backgroundColor: color }]}>
    <Text style={styles.btnText}>{title}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  scrollContent: { padding: 20, paddingBottom: 50 },
  header: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 20, color: '#2c3e50' },
  card: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 15, borderTopWidth: 4, elevation: 3 },
  cardTitle: { fontWeight: 'bold', marginBottom: 10 },
  label: { fontSize: 10, color: '#95a5a6' },
  input: { borderBottomWidth: 1, borderBottomColor: '#eee', paddingVertical: 5, marginBottom: 10, fontSize: 16 },
  inputGap: { marginBottom: 5 },
  btn: { padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  btnText: { color: 'white', fontWeight: 'bold' },
  footer: { marginTop: 20, alignItems: 'center' },
  ok: { color: '#27ae60', fontWeight: 'bold', marginBottom: 10 },
  res: { textAlign: 'center', fontWeight: 'bold', marginTop: 10 },
  resBlue: { textAlign: 'center', color: '#2980b9', fontWeight: 'bold', marginTop: 5 },
  resRed: { textAlign: 'center', color: '#c0392b', fontWeight: 'bold', marginTop: 5 },
});

export default FinanceApp;