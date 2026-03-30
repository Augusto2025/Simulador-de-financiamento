import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, ScrollView, 
  Alert, StyleSheet, KeyboardAvoidingView, Platform, SafeAreaView 
} from 'react-native';

export default function App() {
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

  // --- VALIDAÇÕES E CÁLCULOS ---

  const validarEtapa1 = () => {
    const total = converterParaFloat(dados.valorTotal);
    // Cliente e Imóvel são opcionais, mas Valor Total deve ser > 0
    if (total <= 0) {
      return Alert.alert("Campos Obrigatórios", "Por favor, informe o Valor Total do Imóvel.");
    }

    const entrada = converterParaFloat(dados.entrada);
    const saldo = total - entrada;
    
    setCalculos(prev => ({ ...prev, saldoDevedor: saldo, saldoInicial: saldo }));
    
    Alert.alert(
      "Confirmação", 
      "Deseja capitalizar o saldo?",
      [
        { text: "NÃO", onPress: () => setEtapa(3) },
        { text: "SIM", onPress: () => setEtapa(2) }
      ]
    );
  };

  const calcularCapitalizacao = () => {
    if (!dados.capMeses || !dados.capJuros) {
      return Alert.alert("Campos Obrigatórios", "Preencha a quantidade de meses e a taxa de juros para capitalizar.");
    }

    const n = parseInt(dados.capMeses) || 0;
    const i = parseFloat(dados.capJuros.replace(',', '.')) / 100 || 0;
    const vf = calculos.saldoDevedor * Math.pow((1 + i), n);
    setCalculos(prev => ({ ...prev, valorFuturo: vf, saldoDevedor: vf }));
    setEtapa(3);
  };

  const calcularMensal = () => {
    const pBase = converterParaFloat(dados.mValorBase);
    if (pBase <= 0 || !dados.mQtd || !dados.mJuros) {
      return Alert.alert("Campos Obrigatórios", "Preencha o valor base, a quantidade de meses e os juros das mensalidades.");
    }

    if (pBase > (calculos.saldoDevedor + 0.10)) {
      return Alert.alert("Erro de Valor", "O valor base das mensalidades não pode ser maior que o saldo devedor.");
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
    if (pBaseA <= 0 || !dados.aQtd || !dados.aJuros) {
      return Alert.alert("Campos Obrigatórios", "Preencha todos os campos dos reforços anuais.");
    }

    const n = parseInt(dados.aQtd) || 0;
    const i = parseFloat(dados.aJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBaseA * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBaseA / n) : 0;
    setCalculos(prev => ({ ...prev, parcelaAnual: parcela }));
    setEtapa(5);
  };

  // --- NAVEGAÇÃO ---
  const voltarParaEtapaAnterior = () => {
    if (etapa === 4) {
      setDados(prev => ({ ...prev, aValorBase: '', aQtd: '', aJuros: '' }));
      setCalculos(prev => ({ ...prev, parcelaAnual: 0 }));
      setEtapa(3);
    } 
    else if (etapa === 3) {
      setDados(prev => ({ ...prev, mValorBase: '', mQtd: '', mJuros: '' }));
      setCalculos(prev => ({ ...prev, parcelaMensal: 0 }));
      setEtapa(calculos.valorFuturo > 0 ? 2 : 1);
    }
    else if (etapa === 2) {
      setDados(prev => ({ ...prev, capMeses: '', capJuros: '' }));
      setCalculos(prev => ({ ...prev, valorFuturo: 0 }));
      setEtapa(1);
    }
  };

  const resetGeral = () => {
    setEtapa(1);
    setDados({
      cliente: '', imovel: '', valorTotal: '', entrada: '',
      capMeses: '', capJuros: '', mValorBase: '', mQtd: '', mJuros: '',
      aValorBase: '', aQtd: '', aJuros: ''
    });
    setCalculos({ saldoDevedor: 0, saldoInicial: 0, valorFuturo: 0, parcelaMensal: 0, parcelaAnual: 0 });
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <Text style={styles.header}>Simulador Saldo Zero</Text>

          {/* 1. DADOS INICIAIS */}
          <Card title="1. Dados Iniciais">
            <CustomInput label="CLIENTE (OPCIONAL)" value={dados.cliente} onChangeText={t => setDados({...dados, cliente: t})} />
            <CustomInput label="IMÓVEL (OPCIONAL)" value={dados.imovel} onChangeText={t => setDados({...dados, imovel: t})} />
            <CustomInput label="VALOR TOTAL *" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.valorTotal))} onChangeText={t => handleMoedaInput(t, 'valorTotal')} />
            <CustomInput label="ENTRADA" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.entrada))} onChangeText={t => handleMoedaInput(t, 'entrada')} />
            {etapa === 1 && <Btn onPress={validarEtapa1} color="#2c3e50" title="PRÓXIMO" />}
            {calculos.saldoInicial > 0 && <Text style={styles.res}>Saldo: {formatarMoeda(calculos.saldoInicial)}</Text>}
          </Card>

          {/* 2. CAPITALIZAÇÃO */}
          {etapa === 2 && (
            <Card title="2. Capitalização" color="#8e44ad">
              <CustomInput label="MESES *" keyboardType="numeric" value={dados.capMeses} onChangeText={t => setDados({...dados, capMeses: t})} />
              <CustomInput label="TAXA JUROS % *" keyboardType="numeric" value={dados.capJuros} onChangeText={t => setDados({...dados, capJuros: t})} />
              <View style={styles.row}>
                <Btn onPress={() => setEtapa(1)} color="#95a5a6" title="VOLTAR" half />
                <Btn onPress={calcularCapitalizacao} color="#8e44ad" title="CALCULAR" half />
              </View>
            </Card>
          )}

          {/* 3. MENSALIDADES */}
          {etapa >= 3 && etapa !== 2 && (
            <Card title="3. Mensalidades" color="#3498db">
              {calculos.valorFuturo > 0 && (
                <View style={styles.infoCapBox}><Text style={styles.infoCapText}>Saldo Capitalizado: {formatarMoeda(calculos.valorFuturo)}</Text></View>
              )}
              <CustomInput label="VALOR BASE MENSAL *" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.mValorBase))} onChangeText={t => handleMoedaInput(t, 'mValorBase')} />
              <CustomInput label="QUANTIDADE MESES *" keyboardType="numeric" value={dados.mQtd} onChangeText={t => setDados({...dados, mQtd: t})} />
              <CustomInput label="TAXA JUROS % *" keyboardType="numeric" value={dados.mJuros} onChangeText={t => setDados({...dados, mJuros: t})} />
              {etapa === 3 && (
                <View style={styles.row}>
                  <Btn onPress={voltarParaEtapaAnterior} color="#95a5a6" title="VOLTAR" half />
                  <Btn onPress={calcularMensal} color="#3498db" title="CALCULAR" half />
                </View>
              )}
              {calculos.parcelaMensal > 0 && <Text style={styles.resBlue}>Parcela: {formatarMoeda(calculos.parcelaMensal)}</Text>}
            </Card>
          )}

          {/* 4. ANUAIS */}
          {etapa >= 4 && (
            <Card title="4. Anuais/Reforços" color="#e74c3c">
              <CustomInput label="VALOR BASE ANUAL *" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.aValorBase))} onChangeText={t => handleMoedaInput(t, 'aValorBase')} />
              <CustomInput label="QTD ANUAIS *" keyboardType="numeric" value={dados.aQtd} onChangeText={t => setDados({...dados, aQtd: t})} />
              <CustomInput label="JUROS % *" keyboardType="numeric" value={dados.aJuros} onChangeText={t => setDados({...dados, aJuros: t})} />
              {etapa === 4 && (
                <View style={styles.row}>
                  <Btn onPress={voltarParaEtapaAnterior} color="#95a5a6" title="VOLTAR" half />
                  <Btn onPress={calcularAnual} color="#e74c3c" title="CALCULAR" half />
                </View>
              )}
              {calculos.parcelaAnual > 0 && <Text style={styles.resRed}>Parcela Anual: {formatarMoeda(calculos.parcelaAnual)}</Text>}
            </Card>
          )}

          {/* FINAL */}
          {etapa === 5 && (
            <View style={styles.footer}>
              <Text style={styles.ok}>Simulação Finalizada!</Text>
              <Btn onPress={resetGeral} color="#e67e22" title="NOVA SIMULAÇÃO" />
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// --- COMPONENTES VISUAIS ---
const Card = ({ children, title, color = "#2c3e50" }) => (
  <View style={[styles.card, { borderTopColor: color }]}>
    <Text style={[styles.cardTitle, { color }]}>{title}</Text>
    {children}
  </View>
);

const CustomInput = ({ label, ...props }) => (
  <View style={styles.inputGap}>
    <Text style={styles.label}>{label}</Text>
    <TextInput {...props} style={styles.input} placeholderTextColor="#ccc" />
  </View>
);

const Btn = ({ title, onPress, color, half }) => (
  <TouchableOpacity activeOpacity={0.7} onPress={onPress} style={[styles.btn, { backgroundColor: color, flex: half ? 1 : undefined, marginHorizontal: half ? 5 : 0 }]}>
    <Text style={styles.btnText}>{title}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5' },
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 20, color: '#2c3e50' },
  card: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 15, borderTopWidth: 4, elevation: 4 },
  cardTitle: { fontWeight: 'bold', marginBottom: 10, fontSize: 13, textTransform: 'uppercase' },
  label: { fontSize: 10, color: '#95a5a6', fontWeight: 'bold', marginBottom: 2 },
  input: { borderBottomWidth: 1, borderBottomColor: '#eee', paddingVertical: 8, marginBottom: 10, fontSize: 16, color: '#333' },
  inputGap: { marginBottom: 5 },
  btn: { padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  btnText: { color: 'white', fontWeight: 'bold', fontSize: 13 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginHorizontal: -5 },
  footer: { marginTop: 20, alignItems: 'center', paddingBottom: 50 },
  ok: { color: '#27ae60', fontWeight: 'bold', fontSize: 18, marginBottom: 10 },
  res: { textAlign: 'center', fontWeight: 'bold', marginTop: 10, color: '#2c3e50', fontSize: 15 },
  resBlue: { textAlign: 'center', color: '#2980b9', fontWeight: 'bold', marginTop: 10, fontSize: 16 },
  resRed: { textAlign: 'center', color: '#c0392b', fontWeight: 'bold', marginTop: 10, fontSize: 16 },
  infoCapBox: { backgroundColor: '#f3e5f5', padding: 10, borderRadius: 6, marginBottom: 15, borderLeftWidth: 3, borderLeftColor: '#8e44ad' },
  infoCapText: { color: '#8e44ad', fontWeight: 'bold', fontSize: 12 }
});