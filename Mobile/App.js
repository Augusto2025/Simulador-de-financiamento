import React, { useState, useRef } from 'react';
import { 
  StyleSheet, Text, View, TextInput, TouchableOpacity, 
  ScrollView, Alert, SafeAreaView, KeyboardAvoidingView, Platform 
} from 'react-native';

export default function App() {
  // --- ESTADOS (VARIÁVEIS) ---
  const [cliente, setCliente] = useState('');
  const [imovel, setImovel] = useState('');
  const [valorTotal, setValorTotal] = useState('');
  const [entrada, setEntrada] = useState('');
  const [saldoDevedorBase, setSaldoDevedorBase] = useState(0);
  const [saldoInicialBackup, setSaldoInicialBackup] = useState(0);

  // Capitalização
  const [capMeses, setCapMeses] = useState('');
  const [capJuros, setCapJuros] = useState('');
  const [valorFuturo, setValorFuturo] = useState(0);

  // Mensalidades
  const [mVaiorBase, setMValorBase] = useState('');
  const [mQtd, setMQtd] = useState('');
  const [mJuros, setMJuros] = useState('');
  const [mParcelaComJuros, setMParcelaComJuros] = useState(0);

  // Anuais
  const [aValorBase, setAValorBase] = useState('');
  const [aQtd, setAQtd] = useState('');
  const [aJuros, setAJuros] = useState('');
  const [aParcelaComJuros, setAParcelaComJuros] = useState(0);

  // Controle de Telas (Etapas)
  const [etapa, setEtapa] = useState(1); // 1: Inicial, 2: Cap, 3: Mensal, 4: Anual, 5: Final

  const scrollViewRef = useRef();

  // --- FUNÇÕES DE AUXÍLIO ---
  const formatMoeda = (valor) => {
    let v = valor.replace(/\D/g, '');
    v = (v / 100).toFixed(2) + '';
    v = v.replace(".", ",");
    v = v.replace(/(\d)(\d{3})(\d{3})/, "$1.$2.$3");
    v = v.replace(/(\d)(\d{3})/, "$1.$2");
    return "R$ " + v;
  };

  const parseMoeda = (texto) => {
    if (!texto) return 0;
    return parseFloat(texto.replace(/[R$\s.]/g, '').replace(',', '.'));
  };

  // --- LÓGICA DE CÁLCULO (ETAPAS) ---

  const calcularEtapa1 = () => {
    const total = parseMoeda(valorTotal);
    const ent = parseMoeda(entrada);
    const saldo = total - ent;

    if (saldo <= 0) {
      Alert.alert("Erro", "Valor da entrada não pode ser maior que o total.");
      return;
    }

    setSaldoDevedorBase(saldo);
    setSaldoInicialBackup(saldo);

    Alert.alert(
      "Sucesso", 
      `Saldo inicial: R$ ${saldo.toFixed(2)}. Deseja calcular Valor Futuro (Juros de Obra)?`,
      [
        { text: "Não", onPress: () => setEtapa(3) },
        { text: "Sim", onPress: () => setEtapa(2) }
      ]
    );
  };

  const calcularCapitalizacao = () => {
    const n = parseInt(capMeses) || 0;
    const i = parseFloat(capJuros.replace(',', '.')) / 100 || 0;
    const vf = saldoDevedorBase * Math.pow((1 + i), n);
    
    setValorFuturo(vf);
    setSaldoDevedorBase(vf);
    setEtapa(3);
  };

  const calcularMensal = () => {
    const pBase = parseMoeda(mVaiorBase);
    if (pBase > (saldoDevedorBase + 0.05)) {
      Alert.alert("Atenção", "O valor base não pode exceder o saldo devedor!");
      return;
    }

    const n = parseInt(mQtd) || 0;
    const i = parseFloat(mJuros.replace(',', '.')) / 100 || 0;
    let parcela = 0;

    if (n > 0) {
      parcela = i > 0 ? (pBase * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1)) : (pBase / n);
    }

    setMParcelaComJuros(parcela);
    
    const falta = (saldoDevedorBase - pBase).toFixed(2);
    if (falta <= 0.05) {
      setEtapa(5);
    } else {
      setAValorBase(formatMoeda(falta.replace('.', '')));
      setEtapa(4);
    }
  };

  const calcularAnual = () => {
    const pBaseA = parseMoeda(aValorBase);
    const n = parseInt(aQtd) || 0;
    const i = parseFloat(aJuros.replace(',', '.')) / 100 || 0;
    let parcela = 0;

    if (n > 0) {
      parcela = i > 0 ? (pBaseA * (i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1)) : (pBaseA / n);
    }

    setAParcelaComJuros(parcela);
    setEtapa(5);
  };

  const reset = () => {
    setEtapa(1);
    setCliente(''); setImovel(''); setValorTotal(''); setEntrada('');
    setCapMeses(''); setCapJuros(''); setMValorBase(''); setMQtd('');
    setMJuros(''); setAValorBase(''); setAQtd(''); setAJuros('');
  };

  // --- RENDERIZAÇÃO ---
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{flex: 1}}>
        <ScrollView ref={scrollViewRef} contentContainerStyle={styles.scrollContent}>
          
          <Text style={styles.title}>Simulador Saldo Zero</Text>

          {/* ETAPA 1: DADOS INICIAIS */}
          <View style={styles.card}>
            <Text style={styles.label}>NOME DO CLIENTE</Text>
            <TextInput style={styles.input} value={cliente} onChangeText={setCliente} placeholder="Ex: João Silva" />
            
            <Text style={styles.label}>VALOR TOTAL DO IMÓVEL</Text>
            <TextInput style={styles.input} value={valorTotal} onChangeText={(t) => setValorTotal(formatMoeda(t))} keyboardType="numeric" />
            
            <Text style={styles.label}>VALOR ENTRADA</Text>
            <TextInput style={styles.input} value={entrada} onChangeText={(t) => setEntrada(formatMoeda(t))} keyboardType="numeric" />

            <TouchableOpacity style={styles.btnPrimary} onPress={calcularEtapa1} disabled={etapa > 1}>
              <Text style={styles.btnText}>{etapa > 1 ? "✓ VALIDADO" : "VALIDAR DADOS"}</Text>
            </TouchableOpacity>
            {saldoDevedorBase > 0 && <Text style={styles.resSub}>Saldo: R$ {saldoDevedorBase.toLocaleString('pt-BR')}</Text>}
          </View>

          {/* ETAPA 2: CAPITALIZAÇÃO */}
          {etapa >= 2 && etapa !== 3 && etapa !== 4 && etapa !== 5 && (
            <View style={[styles.card, {borderColor: '#8e44ad', borderLeftWidth: 5}]}>
              <Text style={styles.labelColor}>VALOR FUTURO (JUROS DE OBRA)</Text>
              <TextInput style={styles.input} placeholder="Meses" value={capMeses} onChangeText={setCapMeses} keyboardType="numeric" />
              <TextInput style={styles.input} placeholder="Taxa %" value={capJuros} onChangeText={setCapJuros} keyboardType="numeric" />
              <TouchableOpacity style={[styles.btnPrimary, {backgroundColor: '#8e44ad'}]} onPress={calcularCapitalizacao}>
                <Text style={styles.btnText}>CALCULAR VALOR FUTURO</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* ETAPA 3: MENSALIDADES */}
          {etapa >= 3 && (
            <View style={[styles.card, {borderColor: '#3498db', borderLeftWidth: 5}]}>
              <Text style={styles.labelColor}>MENSALIDADES</Text>
              <TextInput style={styles.input} value={mVaiorBase} onChangeText={(t) => setMValorBase(formatMoeda(t))} placeholder="Valor Base para Mensais" keyboardType="numeric" />
              <TextInput style={styles.input} placeholder="Qtd Meses" value={mQtd} onChangeText={setMQtd} keyboardType="numeric" />
              <TextInput style={styles.input} placeholder="Taxa Mensal %" value={mJuros} onChangeText={setMJuros} keyboardType="numeric" />
              <TouchableOpacity style={[styles.btnPrimary, {backgroundColor: '#3498db'}]} onPress={calcularMensal} disabled={etapa > 3}>
                <Text style={styles.btnText}>{etapa > 3 ? "✓ CALCULADO" : "CALCULAR MENSAL"}</Text>
              </TouchableOpacity>
              {mParcelaComJuros > 0 && <Text style={styles.resSub}>Parcela: R$ {mParcelaComJuros.toFixed(2)}</Text>}
            </View>
          )}

          {/* ETAPA 4: ANUAIS */}
          {etapa >= 4 && (
            <View style={[styles.card, {borderColor: '#e74c3c', borderLeftWidth: 5}]}>
              <Text style={styles.labelColor}>ANUAIS / REFORÇOS</Text>
              <TextInput style={styles.input} value={aValorBase} onChangeText={(t) => setAValorBase(formatMoeda(t))} keyboardType="numeric" />
              <TextInput style={styles.input} placeholder="Qtd Anos" value={aQtd} onChangeText={setAQtd} keyboardType="numeric" />
              <TextInput style={styles.input} placeholder="Taxa Anual %" value={aJuros} onChangeText={setAJuros} keyboardType="numeric" />
              <TouchableOpacity style={[styles.btnPrimary, {backgroundColor: '#e74c3c'}]} onPress={calcularAnual} disabled={etapa > 4}>
                <Text style={styles.btnText}>{etapa > 4 ? "✓ CALCULADO" : "CALCULAR ANUAL"}</Text>
              </TouchableOpacity>
              {aParcelaComJuros > 0 && <Text style={styles.resSub}>Anual: R$ {aParcelaComJuros.toFixed(2)}</Text>}
            </View>
          )}

          {/* FINALIZAÇÃO */}
          {etapa === 5 && (
            <View style={styles.cardFinal}>
              <Text style={styles.finalTitle}>✓ SIMULAÇÃO CONCLUÍDA</Text>
              <Text>Cliente: {cliente}</Text>
              <Text>Saldo Final Zerado com sucesso.</Text>
              <TouchableOpacity style={styles.btnReset} onPress={reset}>
                <Text style={styles.btnText}>NOVA SIMULAÇÃO</Text>
              </TouchableOpacity>
            </View>
          )}

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5' },
  scrollContent: { padding: 20 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#2c3e50', textAlign: 'center', marginBottom: 20 },
  card: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 15, elevation: 3 },
  cardFinal: { backgroundColor: '#dff9fb', padding: 20, borderRadius: 10, alignItems: 'center' },
  label: { fontSize: 12, fontWeight: 'bold', color: '#636e72', marginBottom: 5 },
  labelColor: { fontSize: 14, fontWeight: 'bold', marginBottom: 10 },
  input: { backgroundColor: '#f9f9f9', borderWidth: 1, borderColor: '#ddd', borderRadius: 5, padding: 10, marginBottom: 10 },
  btnPrimary: { backgroundColor: '#2c3e50', padding: 15, borderRadius: 5, alignItems: 'center' },
  btnReset: { backgroundColor: '#e67e22', padding: 15, borderRadius: 5, alignItems: 'center', marginTop: 15, width: '100%' },
  btnText: { color: 'white', fontWeight: 'bold' },
  resSub: { marginTop: 10, fontSize: 16, fontWeight: 'bold', color: '#2c3e50', textAlign: 'center' },
  finalTitle: { fontSize: 18, fontWeight: 'bold', color: '#27ae60', marginBottom: 10 }
});