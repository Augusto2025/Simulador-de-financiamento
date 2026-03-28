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

  // Formatação manual de moeda para evitar crash no Android (sem Intl)
  const formatarMoeda = (valor) => {
    if (isNaN(valor) || valor === null) return 'R$ 0,00';
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
    
    if (total <= 0) {
        Alert.alert("Atenção", "Informe o valor total do imóvel.");
        return;
    }

    setCalculos(prev => ({ ...prev, saldoDevedor: saldo, saldoInicial: saldo }));
    
    Alert.alert("Saldo Devedor", `O saldo atual é ${formatarMoeda(saldo)}. Deseja calcular juros de capitalização antes das parcelas?`, [
      { text: "Não (Direto para parcelas)", onPress: () => setEtapa(2) },
      { text: "Sim (Adicionar Juros)", onPress: () => setEtapa(1.5) }
    ]);
  };

  const calcularCapitalizacao = () => {
    const n = parseInt(dados.capMeses) || 0;
    const i = parseFloat(dados.capJuros.replace(',', '.')) / 100 || 0;
    const vf = calculos.saldoDevedor * Math.pow((1 + i), n);
    setCalculos(prev => ({ ...prev, saldoDevedor: vf, valorFuturo: vf }));
    setEtapa(2);
  };

  const calcularMensal = () => {
    const pBase = converterParaFloat(dados.mValorBase);
    if (pBase > calculos.saldoDevedor + 0.10) {
      Alert.alert("Erro", "O valor base das mensais não pode ser maior que o saldo devedor!");
      return;
    }
    const n = parseInt(dados.mQtd) || 0;
    const i = parseFloat(dados.mJuros.replace(',', '.')) / 100 || 0;
    let parcela = n > 0 ? (i > 0 ? pBase * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1) : pBase / n) : 0;
    
    setCalculos(prev => ({ ...prev, parcelaMensal: parcela }));
    
    const falta = calculos.saldoDevedor - pBase;
    if (falta <= 0.10) { 
        setEtapa(4); 
    } else { 
        setDados(prev => ({ ...prev, aValorBase: (falta * 100).toFixed(0) })); 
        setEtapa(3); 
    }
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
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.header}>Simulador de Financiamento</Text>

          <Card title="1. Dados do Contrato">
            <CustomInput label="NOME DO CLIENTE" value={dados.cliente} onChangeText={t => setDados({...dados, cliente: t})} />
            <CustomInput label="IDENTIFICAÇÃO DO IMÓVEL" value={dados.imovel} onChangeText={t => setDados({...dados, imovel: t})} />
            <CustomInput label="VALOR TOTAL DO IMÓVEL" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.valorTotal))} onChangeText={t => handleMoedaInput(t, 'valorTotal')} />
            <CustomInput label="VALOR DA ENTRADA" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.entrada))} onChangeText={t => handleMoedaInput(t, 'entrada')} />
            {etapa === 1 && <Btn onPress={validarEtapa1} color="#2c3e50" title="PRÓXIMO PASSO" />}
            {calculos.saldoInicial > 0 && <Text style={styles.res}>Saldo Inicial: {formatarMoeda(calculos.saldoInicial)}</Text>}
          </Card>

          {etapa >= 1.5 && etapa < 2 && (
            <Card title="2. Capitalização (Opcional)" color="#8e44ad">
              <CustomInput label="QUANTIDADE DE MESES" keyboardType="numeric" value={dados.capMeses} onChangeText={t => setDados({...dados, capMeses: t})} />
              <CustomInput label="TAXA DE JUROS % (ao mês)" keyboardType="numeric" value={dados.capJuros} onChangeText={t => setDados({...dados, capJuros: t})} />
              <Btn onPress={calcularCapitalizacao} color="#8e44ad" title="CALCULAR SALDO ATUALIZADO" />
            </Card>
          )}

          {etapa >= 2 && (
            <Card title="3. Plano de Mensalidades" color="#3498db">
              <CustomInput label="VALOR DO SALDO PARA MENSALIDADES" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.mValorBase))} onChangeText={t => handleMoedaInput(t, 'mValorBase')} />
              <CustomInput label="QTD DE PARCELAS MENSAIS" keyboardType="numeric" value={dados.mQtd} onChangeText={t => setDados({...dados, mQtd: t})} />
              <CustomInput label="TAXA DE JUROS % (ao mês)" keyboardType="numeric" value={dados.mJuros} onChangeText={t => setDados({...dados, mJuros: t})} />
              {etapa === 2 && <Btn onPress={calcularMensal} color="#3498db" title="CALCULAR MENSALIDADES" />}
              {calculos.parcelaMensal > 0 && <Text style={styles.resBlue}>Parcela Mensal: {formatarMoeda(calculos.parcelaMensal)}</Text>}
            </Card>
          )}

          {etapa >= 3 && (
            <Card title="4. Plano de Reforços (Anuais)" color="#e74c3c">
              <CustomInput label="VALOR RESTANTE PARA REFORÇOS" keyboardType="numeric" value={formatarMoeda(converterParaFloat(dados.aValorBase))} onChangeText={t => handleMoedaInput(t, 'aValorBase')} />
              <CustomInput label="QTD DE ANOS (Reforços)" keyboardType="numeric" value={dados.aQtd} onChangeText={t => setDados({...dados, aQtd: t})} />
              <CustomInput label="TAXA DE JUROS % (ao ano)" keyboardType="numeric" value={dados.aJuros} onChangeText={t => setDados({...dados, aJuros: t})} />
              {etapa === 3 && <Btn onPress={calcularAnual} color="#e74c3c" title="CALCULAR ANUAIS" />}
              {calculos.parcelaAnual > 0 && <Text style={styles.resRed}>Parcela Anual: {formatarMoeda(calculos.parcelaAnual)}</Text>}
            </Card>
          )}

          {etapa === 4 && (
            <View style={styles.footerContainer}>
              <Text style={styles.finalMsg}>Simulação Concluída com Sucesso!</Text>
              <Btn onPress={resetGeral} color="#e67e22" title="NOVA SIMULAÇÃO" />
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// Componentes Reutilizáveis
const Card = ({ children, title, color = "#2c3e50" }) => (
  <View style={[styles.card, { borderTopColor: color }]}>
    <Text style={[styles.cardTitle, { color }]}>{title}</Text>
    {children}
  </View>
);

const CustomInput = ({ label, ...props }) => (
  <View style={styles.inputGap}>
    <Text style={styles.label}>{label}</Text>
    <TextInput {...props} style={styles.input} underlineColorAndroid="transparent" />
  </View>
);

const Btn = ({ title, onPress, color }) => (
  <TouchableOpacity onPress={onPress} activeOpacity={0.7} style={[styles.btn, { backgroundColor: color }]}>
    <Text style={styles.btnText}>{title}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginVertical: 20, color: '#2c3e50' },
  card: { backgroundColor: 'white', padding: 18, borderRadius: 12, marginBottom: 15, borderTopWidth: 5, elevation: 4, shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
  cardTitle: { fontWeight: 'bold', marginBottom: 15, fontSize: 16, textTransform: 'uppercase' },
  label: { fontSize: 11, fontWeight: 'bold', color: '#95a5a6', marginBottom: 2 },
  input: { borderBottomWidth: 1, borderBottomColor: '#ecf0f1', paddingVertical: 8, marginBottom: 10, fontSize: 17, color: '#2c3e50' },
  inputGap: { marginBottom: 12 },
  btn: { padding: 16, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  btnText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  footerContainer: { marginTop: 20, marginBottom: 50 },
  finalMsg: { textAlign: 'center', color: '#27ae60', fontWeight: 'bold', marginBottom: 15, fontSize: 16 },
  res: { textAlign: 'center', marginTop: 10, fontWeight: 'bold', color: '#2c3e50', fontSize: 16 },
  resBlue: { textAlign: 'center', marginTop: 10, fontWeight: 'bold', color: '#2980b9', fontSize: 16 },
  resRed: { textAlign: 'center', marginTop: 10, fontWeight: 'bold', color: '#c0392b', fontSize: 16 },
});

export default FinanceApp;