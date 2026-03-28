import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  ScrollView, 
  Alert, 
  StyleSheet, 
  KeyboardAvoidingView, 
  Platform,
  SafeAreaView 
} from 'react-native';

const FinanceApp = () => {
  const [etapa, setEtapa] = useState(1);
  const [dados, setDados] = useState({
    cliente: '', imovel: '', valorTotal: '', entrada: '',
    capMeses: '', capJuros: '',
    mValorBase: '', mQtd: '', mJuros: '',
    aValorBase: '', aQtd: '', aJuros: ''
  });

  const [calculos, setCalculos] = useState({
    saldoDevedor: 0, saldoInicial: 0, valorFuturo: 0, parcelaMensal: 0, parcelaAnual: 0
  });

  const formatarMoeda = (valor) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  const converterParaFloat = (texto) => {
    if (!texto) return 0;
    const limpo = texto.toString().replace(/\D/g, '');
    return parseFloat(limpo) / 100;
  };

  const handleMoedaInput = (valorRaw, campo) => {
    const apenasNumeros = valorRaw.replace(/\D/g, '');
    setDados({ ...dados, [campo]: apenasNumeros });
  };

  const resetGeral = () => {
    setEtapa(1);
    setDados({
      cliente: '', imovel: '', valorTotal: '', entrada: '',
      capMeses: '', capJuros: '',
      mValorBase: '', mQtd: '', mJuros: '',
      aValorBase: '', aQtd: '', aJuros: ''
    });
    setCalculos({
      saldoDevedor: 0, saldoInicial: 0, valorFuturo: 0, parcelaMensal: 0, parcelaAnual: 0
    });
  };

  const validarEtapa1 = () => {
    const total = converterParaFloat(dados.valorTotal);
    const entrada = converterParaFloat(dados.entrada);
    const saldo = total - entrada;
    setCalculos({ ...calculos, saldoDevedor: saldo, saldoInicial: saldo });
    
    Alert.alert("Valor Futuro", "Deseja calcular a capitalização?", [
      { text: "Não", onPress: () => setEtapa(2) },
      { text: "Sim", onPress: () => setEtapa(1.5) }
    ]);
  };

  const calcularCapitalizacao = () => {
    const n = parseInt(dados.capMeses) || 0;
    const i = parseFloat(dados.capJuros.replace(',', '.')) / 100 || 0;
    const vf = calculos.saldoDevedor * Math.pow((1 + i), n);
    setCalculos({ ...calculos, saldoDevedor: vf, valorFuturo: vf });
    setEtapa(2);
  };

  const calcularMensal = () => {
    const pBase = converterParaFloat(dados.mValorBase);
    if (pBase > calculos.saldoDevedor + 0.05) {
      Alert.alert("Erro", "Valor base excede o saldo!");
      return;
    }
    const n = parseInt(dados.mQtd) || 0;
    const i = parseFloat(dados.mJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBase * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBase / n) : 0;
    setCalculos({ ...calculos, parcelaMensal: parcela });
    const falta = calculos.saldoDevedor - pBase;
    if (falta <= 0.05) { setEtapa(4); } 
    else { setDados({ ...dados, aValorBase: (falta * 100).toFixed(0) }); setEtapa(3); }
  };

  const calcularAnual = () => {
    const pBaseA = converterParaFloat(dados.aValorBase);
    const n = parseInt(dados.aQtd) || 0;
    const i = parseFloat(dados.aJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBaseA * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBaseA / n) : 0;
    setCalculos({ ...calculos, parcelaAnual: parcela });
    setEtapa(4);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F0F2F5' }}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.header}>Simulador Saldo Zero</Text>

          <Card title="Dados Iniciais">
            <Input label="CLIENTE" value={dados.cliente} onChangeText={t => setDados({...dados, cliente: t})} />
            <Input label="IMÓVEL" value={dados.imovel} onChangeText={t => setDados({...dados, imovel: t})} />
            <Input label="VALOR TOTAL" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.valorTotal))} onChangeText={t => handleMoedaInput(t, 'valorTotal')} />
            <Input label="ENTRADA" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.entrada))} onChangeText={t => handleMoedaInput(t, 'entrada')} />
            {etapa === 1 && <Btn onPress={validarEtapa1} color="#2c3e50" title="VALIDAR DADOS" />}
            {calculos.saldoInicial > 0 && <Text style={styles.res}>Saldo: {formatarMoeda(calculos.saldoInicial)}</Text>}
          </Card>

          {etapa >= 1.5 && etapa < 2 && (
            <Card title="Valor Futuro" color="#8e44ad">
              <Input label="MESES" keyboardType="numeric" value={dados.capMeses} onChangeText={t => setDados({...dados, capMeses: t})} />
              <Input label="JUROS %" keyboardType="numeric" value={dados.capJuros} onChangeText={t => setDados({...dados, capJuros: t})} />
              <Btn onPress={calcularCapitalizacao} color="#8e44ad" title="CALCULAR VALOR FUTURO" />
            </Card>
          )}

          {etapa >= 2 && (
            <Card title="Mensalidades" color="#3498db">
              <Input label="VALOR BASE" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.mValorBase))} onChangeText={t => handleMoedaInput(t, 'mValorBase')} />
              <Input label="QTD MESES" keyboardType="numeric" value={dados.mQtd} onChangeText={t => setDados({...dados, mQtd: t})} />
              <Input label="JUROS %" keyboardType="numeric" value={dados.mJuros} onChangeText={t => setDados({...dados, mJuros: t})} />
              {etapa === 2 && <Btn onPress={calcularMensal} color="#3498db" title="CÁLCULO MENSAL" />}
              {calculos.parcelaMensal > 0 && <Text style={styles.resBlue}>Parcela: {formatarMoeda(calculos.parcelaMensal)}</Text>}
            </Card>
          )}

          {etapa >= 3 && (
            <Card title="Reforços Anuais" color="#e74c3c">
              <Input label="VALOR ANUAL BASE" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.aValorBase))} onChangeText={t => handleMoedaInput(t, 'aValorBase')} />
              <Input label="QTD ANOS" keyboardType="numeric" value={dados.aQtd} onChangeText={t => setDados({...dados, aQtd: t})} />
              <Input label="JUROS %" keyboardType="numeric" value={dados.aJuros} onChangeText={t => setDados({...dados, aJuros: t})} />
              {etapa === 3 && <Btn onPress={calcularAnual} color="#e74c3c" title="CÁLCULO ANUAL" />}
              {calculos.parcelaAnual > 0 && <Text style={styles.resRed}>Parcela Anual: {formatarMoeda(calculos.parcelaAnual)}</Text>}
            </Card>
          )}

          {etapa === 4 && (
            <View style={styles.footerContainer}>
              <Btn onPress={resetGeral} color="#e67e22" title="RECOMEÇAR SIMULAÇÃO" />
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

const Input = ({ label, ...props }) => (
  <View style={styles.inputGap}>
    <Text style={styles.label}>{label}</Text>
    <TextInput {...props} style={styles.input} />
  </View>
);

const Btn = ({ title, onPress, color }) => (
  <TouchableOpacity onPress={onPress} activeOpacity={0.7} style={[styles.btn, { backgroundColor: color }]}>
    <Text style={styles.btnText}>{title}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  scrollContent: { padding: 20, paddingBottom: 60 }, // Espaço extra no final
  header: { fontSize: 20, fontWeight: 'bold', textAlign: 'center', marginVertical: 20, color: '#2c3e50' },
  card: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 15, borderTopWidth: 4, elevation: 3 },
  cardTitle: { fontWeight: 'bold', marginBottom: 10, fontSize: 14 },
  label: { fontSize: 10, fontWeight: 'bold', color: '#636E72', marginBottom: 2 },
  input: { borderBottomWidth: 1, borderBottomColor: '#ddd', paddingVertical: 8, marginBottom: 10, fontSize: 16, color: '#2d3436' },
  inputGap: { marginBottom: 5 },
  btn: { padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  btnText: { color: 'white', fontWeight: 'bold', fontSize: 14 },
  footerContainer: { 
    marginTop: 30, 
    marginBottom: 50, // Margem grande para não tocar nos botões do sistema
    paddingHorizontal: 10 
  },
  res: { textAlign: 'center', marginTop: 10, fontWeight: 'bold', color: '#e67e22' },
  resBlue: { textAlign: 'center', marginTop: 10, fontWeight: 'bold', color: '#1e3799' },
  resRed: { textAlign: 'center', marginTop: 10, fontWeight: 'bold', color: '#b71540' },
});

export default FinanceApp;