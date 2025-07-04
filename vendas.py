import streamlit as st
import pandas as pd
from datetime import date
import os
import shutil
import altair as alt
import streamlit as st

st.set_page_config(layout="wide")


def formatar_moeda(valor):
    return "R$ {:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_proximo_id(vendas_df, data_venda):
    data_str = data_venda.strftime("%Y%m%d")
    if vendas_df.empty or "ID" not in vendas_df.columns:
        return f"{data_str}-0001"
    existentes = vendas_df[
        vendas_df["ID"].fillna("").astype(str).str.startswith(data_str)
    ]
    contador = 1
    if not existentes.empty:
        ultimos_numeros = (
            existentes["ID"]
            .fillna("")
            .astype(str)
            .str[-4:]
            .astype(int)
        )
        contador = ultimos_numeros.max() + 1
    return f"{data_str}-{contador:04d}"

ARQUIVO_VENDAS = "vendas_registradas.csv"
ARQUIVO_RECEB = "recebimentos_registrados.csv"

def formatar_percentual(valor):
    return f"{valor:.1f}%"

def calcular_despesas(valor_venda, custo):
    icms = custo * 0.10
    simples = valor_venda * 0.045
    royalties = valor_venda * 0.075
    propaganda = valor_venda * 0.015
    valor_corretor = valor_venda * 0.03
    desp_adm = valor_venda * 0.05
    return icms, simples, royalties, propaganda, valor_corretor, desp_adm

def calcular_lucros(valor_venda, custo, total_desp):
    lucro_bruto = valor_venda - custo
    lucro_liquido = lucro_bruto - total_desp
    percentual_lucro = (lucro_liquido / valor_venda * 100) if valor_venda > 0 else 0
    return lucro_bruto, lucro_liquido, percentual_lucro

def formatar_dinheiro_df(df, colunas):
    for col in colunas:
        df[col] = df[col].apply(formatar_moeda)
    return df

# Carregar vendas
if os.path.exists(ARQUIVO_VENDAS):
    vendas_df = pd.read_csv(ARQUIVO_VENDAS)
    if "Venda ID" in vendas_df.columns:
        vendas_df = vendas_df.rename(columns={"Venda ID": "ID"})
    if "ID" not in vendas_df.columns:
        vendas_df["ID"] = None
else:
    vendas_df = pd.DataFrame(columns=[
        "ID", "Data", "Cliente", "Modelo", "Valor da Venda", "Custo", "Valor Frete",
        "ICMS (10%)", "Simples (4,5%)", "Royalties (7,5%)", "Propag. (1,5%)",
        "Corretor (3%)", "Desp. ADM (5%)", "Lucro Bruto", "Total Desp.",
        "Lucro Líquido", "% de Lucro"
    ])

# Carregar recebimentos
if os.path.exists(ARQUIVO_RECEB):
    receb_df = pd.read_csv(ARQUIVO_RECEB)
else:
    receb_df = pd.DataFrame(columns=[
        "ID Venda", "Data", "Cliente", "Modelo", "Valor Recebido", "Forma de Pagamento", "Observação"
    ])

aba = st.sidebar.radio(
    "Navegar",
    [
        "📋 Cadastro de Vendas",
        "💸 Painel de Despesas",
        "💰 Controle de Recebimentos",
        "📊 Dashboards",
        "🏠 Dashboard Consolidado"
    ]
)

if aba == "📋 Cadastro de Vendas":
    st.title("📋 Cadastro de Vendas - MCPF")

    # ━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("📝 Nova Venda")

    with st.form("cadastro_venda"):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("📅 Data da Venda", value=date.today())
            cliente = st.text_input("👤 Nome do Cliente", placeholder="Digite o nome completo")
            modelo = st.text_input("🏠 Modelo do Kit", placeholder="Ex: Chalé Pop 2.0")
            corretor = st.text_input("👔 Nome do Corretor (opcional)", placeholder="Digite o nome do corretor")
        with col2:
            valor_venda = st.number_input("💰 Valor da Venda", min_value=0.0, step=100.0)
            custo = st.number_input("🧾 Custo do Kit", min_value=0.0, step=100.0)
            valor_frete = st.number_input("🚚 Valor do Frete", min_value=0.0, step=50.0)

        st.caption("🛻 O valor do frete é pago diretamente pelo cliente e não entra nos cálculos de lucro.")
        enviado = st.form_submit_button("✅ Salvar Venda")


        if enviado:
            if not cliente.strip():
                st.warning("⚠️ O nome do cliente é obrigatório.")
                st.stop()
            if not modelo.strip():
                st.warning("⚠️ O modelo é obrigatório.")
                st.stop()
            if valor_venda <= 0:
                st.warning("⚠️ O valor da venda deve ser maior que zero.")
                st.stop()
            if custo > valor_venda:
                st.warning("⚠️ O custo é maior que o valor da venda. Verifique se está correto.")

            cliente = cliente.strip().title()
            modelo = modelo.strip().title()

            if os.path.exists(ARQUIVO_VENDAS):
                shutil.copy(ARQUIVO_VENDAS, ARQUIVO_VENDAS + ".bak")

            icms, simples, royalties, propaganda, valor_corretor, desp_adm = calcular_despesas(valor_venda, custo)
            total_desp = icms + simples + royalties + propaganda + valor_corretor + desp_adm
            lucro_bruto, lucro_liquido, percentual_lucro = calcular_lucros(valor_venda, custo, total_desp)
            id_venda = gerar_proximo_id(vendas_df, data)

            nova_venda = {
                    "ID": id_venda,
                    "Data": data.strftime('%d/%m/%Y'),
                    "Cliente": cliente,
                    "Modelo": modelo,
                    "Corretor Nome": str(corretor).strip().title() if pd.notna(corretor) else "",
                    "Corretor (3%)": valor_corretor,
                    "Valor da Venda": valor_venda,
                    "Custo": custo,
                    "Valor Frete": valor_frete,
                    "ICMS (10%)": icms,
                    "Simples (4,5%)": simples,
                    "Royalties (7,5%)": royalties,
                    "Propag. (1,5%)": propaganda,
                    "Desp. ADM (5%)": desp_adm,
                    "Lucro Bruto": lucro_bruto,
                    "Total Desp.": total_desp,
                    "Lucro Líquido": lucro_liquido,
                    "% de Lucro": percentual_lucro
                    
                }    

            # Campos de controle de despesas
            for desp in ["Custo", "Royalties (7,5%)", "Propag. (1,5%)", "ICMS (10%)",
                        "Simples (4,5%)", "Corretor (3%)", "Desp. ADM (5%)"]:
                nova_venda[f"Pago {desp}"] = False
                nova_venda[f"Parcial {desp}"] = 0.0

            vendas_df = pd.concat([vendas_df, pd.DataFrame([nova_venda])], ignore_index=True)
            vendas_df.to_csv(ARQUIVO_VENDAS, index=False)
            st.success("✅ Venda registrada com sucesso!")

    # ━━━━━━━━━━━━━━━━━━━━━━━━
    st.divider()
    st.subheader("📈 Resumo Geral das Vendas")

    vendas_df["ID"] = vendas_df["ID"].astype(str)
    receb_df["ID Venda"] = receb_df["ID Venda"].astype(str)

    # Calcular totais
   # Calcular totais
    total_vendas = vendas_df["Valor da Venda"].sum()
    total_recebido = receb_df["Valor Recebido"].sum() if not receb_df.empty else 0
    total_a_receber = total_vendas - total_recebido
    lucro_medio = vendas_df["% de Lucro"].mean() if not vendas_df.empty else 0

    # Calcular total a pagar (saldo de despesas)
    despesas_saldo = 0
    if not vendas_df.empty:
        for desp in [
            "Custo",
            "Royalties (7,5%)",
            "Propag. (1,5%)",
            "ICMS (10%)",
            "Simples (4,5%)",
            "Corretor (3%)",
            "Desp. ADM (5%)"
        ]:
            col_saldo = f"Saldo {desp}"
            if col_saldo in vendas_df.columns:
                despesas_saldo += vendas_df[col_saldo].sum()

    # Exibir métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total de Vendas", formatar_moeda(total_vendas))
    col2.metric("🟡 Total a Receber", formatar_moeda(total_a_receber))
    col3.metric("🔴 Total a Pagar", formatar_moeda(despesas_saldo))
    col4.metric("📊 Lucro Médio", formatar_percentual(lucro_medio))


    # ━━━━━━━━━━━━━━━━━━━━━━━━
    st.divider()
    st.subheader("🔍 Vendas Registradas")

    termo_busca = st.text_input("🔎 Buscar por cliente ou modelo")

    if termo_busca.strip():
        df_visu = vendas_df[
            vendas_df["Cliente"].str.contains(termo_busca, case=False, na=False) |
            vendas_df["Modelo"].str.contains(termo_busca, case=False, na=False)
        ].copy()
    else:
        df_visu = vendas_df.copy()

    df_visu = df_visu.sort_values(by="Data", ascending=False).reset_index(drop=True)
    mostrar_todas = st.checkbox("Mostrar todas as vendas", value=False)
    if not mostrar_todas and len(df_visu) > 20:
        df_visu = df_visu.head(20)

    df_visu["ID"] = df_visu["ID"].astype(str)

    df_visu["Total Recebido"] = df_visu["ID"].map(
        receb_df.groupby("ID Venda")["Valor Recebido"].sum()
    ).fillna(0)
    df_visu["Saldo a Receber"] = df_visu["Valor da Venda"] - df_visu["Total Recebido"]

    ids_disponiveis = df_visu["ID"].tolist()
    ids_selecionados = st.multiselect("Selecione IDs para excluir", ids_disponiveis)

    st.markdown("### 📋 Detalhes das Vendas")
    num_cols = 3
    cols = st.columns(num_cols)

    for idx, dados in df_visu.iterrows():
        col = cols[idx % num_cols]
        with col:
            status_saldo = "✅ Quitado" if dados["Saldo a Receber"] <= 0.01 else "🔴 Em aberto"
            cor_saldo = "#d4edda" if status_saldo == "✅ Quitado" else "#f8d7da"

            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:8px; padding:10px; margin-bottom:10px; background-color:{cor_saldo};">
                <b>ID:</b> {dados['ID']}<br>
                <b>Data:</b> {dados['Data']}<br>
                <b>Cliente:</b> {dados['Cliente']}<br>
                <b>Modelo:</b> {dados['Modelo']}<br>
                <b>💰 Venda:</b> {formatar_moeda(dados['Valor da Venda'])}<br>
                <b>Lucro Líquido:</b> {formatar_moeda(dados['Lucro Líquido'])}<br>
                <b>% Lucro:</b> {formatar_percentual(dados['% de Lucro'])}<br>
                <b>💵 Recebido:</b> {formatar_moeda(dados['Total Recebido'])}<br>
                <b>Saldo:</b> {formatar_moeda(dados['Saldo a Receber'])} ({status_saldo})
                </div>
                """,
                unsafe_allow_html=True
            )

    if st.button("Excluir Vendas Selecionadas"):
        if not ids_selecionados:
            st.warning("Nenhum ID selecionado.")
        else:
            st.write("IDs marcados:", ids_selecionados)

            if os.path.exists(ARQUIVO_VENDAS):
                shutil.copy(ARQUIVO_VENDAS, ARQUIVO_VENDAS + ".bak")
            if os.path.exists(ARQUIVO_RECEB):
                shutil.copy(ARQUIVO_RECEB, ARQUIVO_RECEB + ".bak")
            if "Corretor Nome" not in vendas_df.columns:
                vendas_df["Corretor Nome"] = ""


            vendas_df = vendas_df[~vendas_df["ID"].isin(ids_selecionados)].reset_index(drop=True)

            if not receb_df.empty and any(receb_df["ID Venda"].isin(ids_selecionados)):
                receb_df = receb_df[~receb_df["ID Venda"].isin(ids_selecionados)].reset_index(drop=True)
                receb_df.to_csv(ARQUIVO_RECEB, index=False)
                st.success("✅ Vendas e recebimentos excluídos com sucesso!")
            else:
                st.success("✅ Vendas excluídas com sucesso!")

            vendas_df.to_csv(ARQUIVO_VENDAS, index=False)
            st.rerun()

    st.divider()
    st.subheader("📊 Tabela Completa")

    df_exib = vendas_df.copy()
    df_exib["% de Lucro"] = df_exib["% de Lucro"].apply(formatar_percentual)
    colunas_moeda = ["Valor da Venda", "Custo", "Valor Frete", "ICMS (10%)",
                     "Simples (4,5%)", "Royalties (7,5%)", "Propag. (1,5%)",
                     "Corretor (3%)", "Desp. ADM (5%)", "Lucro Bruto",
                     "Total Desp.", "Lucro Líquido"]
    df_exib = formatar_dinheiro_df(df_exib, colunas_moeda)
    st.dataframe(df_exib, use_container_width=True)


elif aba == "💸 Painel de Despesas":
    st.title("💸 Painel de Despesas por Venda")
    

    df = vendas_df.copy()

    despesas = [
        "Custo",
        "Royalties (7,5%)",
        "Propag. (1,5%)",
        "ICMS (10%)",
        "Simples (4,5%)",
        "Corretor (3%)",
        "Desp. ADM (5%)"
    ]

    # Inicializa colunas
    for desp in despesas:
        for suffix in ["Pago", "Parcial", "Saldo"]:
            col_name = f"{suffix} {desp}"
            if col_name not in df.columns:
                if suffix == "Pago":
                    df[col_name] = False
                else:
                    df[col_name] = 0.0

    # Força booleano
    for desp in despesas:
        col_pago = f"Pago {desp}"
        if col_pago in df.columns:
            df[col_pago] = df[col_pago].replace({1.0: True, 0.0: False}).astype(bool)

    # Atualiza saldo
    for desp in despesas:
        df[f"Saldo {desp}"] = df[desp] - df[f"Parcial {desp}"]

    # Editor
    df_editado = st.data_editor(
        df,
        column_config={
            f"Pago {desp}": st.column_config.CheckboxColumn(label=f"Pago {desp}")
            for desp in despesas
        },
        use_container_width=True,
        disabled=[col for col in df.columns if "Pago" not in col],
        key="painel_despesas"
    )

    # ✅ AQUI VEM O CÁLCULO DOS TOTAIS
    total_pago = 0
    total_saldo = 0
    for desp in despesas:
        pago_total = df_editado.loc[df_editado[f"Pago {desp}"], desp].sum()
        parcial_pendente = df_editado.loc[~df_editado[f"Pago {desp}"], f"Parcial {desp}"].sum()
        total_pago += pago_total + parcial_pendente
        total_saldo += df_editado[f"Saldo {desp}"].sum()


    st.subheader("💰 Totais Gerais")
    col1, col2 = st.columns(2)
    col1.metric("🟢 Pago Total ou Parcial", formatar_moeda(total_pago))
    col2.metric("🔴 Saldo a Pagar", formatar_moeda(total_saldo))


    st.divider()

    st.subheader("🔍 Detalhes de Cada Venda")
    if "Obs Custo" not in df_editado.columns:
        df_editado["Obs Custo"] = ""

    for idx, row in df_editado.iterrows():
        with st.expander(f"Detalhes da Venda {row['ID']} - Cliente {row['Cliente']}"):
            st.write(f"**Modelo:** {row['Modelo']}")
            for desp in despesas:

                
                # Primeiro, monta obs_texto
                obs_texto = ""
                if desp == "Custo" and row.get("Obs Custo"):
                    obs_texto = f"- Observação: {row['Obs Custo']}"

                # Depois exibe
                st.markdown(f"""
                🧾 **{desp}**
                - Valor Total: {formatar_moeda(row[desp])}
                - Pago Parcial: {formatar_moeda(row[f'Parcial {desp}'])}
                - Saldo: {formatar_moeda(row[f'Saldo {desp}'])}
                - Status: {"✅ Pago" if row[f"Pago {desp}"] else "❌ Pendente"}
                {obs_texto}
                """)



                if not row[f"Pago {desp}"]:
                    if desp == "Custo":
                        col_p1, col_p2 = st.columns([2,1])
                        valor_parcial = col_p1.number_input(
                            f"Registrar pagamento parcial ({desp})",
                            min_value=0.0,
                            max_value=row[f"Saldo {desp}"],
                            step=50.0,
                            key=f"parcial_{desp}_{idx}"
                        )
                        obs_custo = st.text_input(
                            f"Observação do Pagamento ({desp})",
                            value=row.get("Obs Custo", ""),
                            key=f"obs_custo_{idx}"
                        )
                        if col_p2.button(f"Registrar Pagamento ({desp})", key=f"botao_parcial_{desp}_{idx}"):
                            df_editado.at[idx, f"Parcial {desp}"] += valor_parcial
                            df_editado.at[idx, f"Saldo {desp}"] = df_editado.at[idx, desp] - df_editado.at[idx, f"Parcial {desp}"]
                            if df_editado.at[idx, f"Saldo {desp}"] <= 0.01:
                                df_editado.at[idx, f"Pago {desp}"] = True

                            # Concatenar a nova observação
                            observacao_atual = str(row.get("Obs Custo", "")).strip()
                            nova_obs = obs_custo.strip()
                            if observacao_atual:
                                resultado_obs = observacao_atual + " | " + nova_obs
                            else:
                                resultado_obs = nova_obs
                            df_editado.at[idx, "Obs Custo"] = resultado_obs

                            df_editado.to_csv(ARQUIVO_VENDAS, index=False)
                            st.success(f"Pagamento registrado em {desp}.")
                            st.rerun()

                    else:
                        col_p1, col_p2 = st.columns([2,1])
                        valor_parcial = col_p1.number_input(
                            f"Registrar pagamento parcial ({desp})",
                            min_value=0.0,
                            max_value=row[f"Saldo {desp}"],
                            step=50.0,
                            key=f"parcial_{desp}_{idx}"
                        )
                        if col_p2.button(f"Registrar Pagamento ({desp})", key=f"botao_parcial_{desp}_{idx}"):
                            df_editado.at[idx, f"Parcial {desp}"] += valor_parcial
                            df_editado.at[idx, f"Saldo {desp}"] = df_editado.at[idx, desp] - df_editado.at[idx, f"Parcial {desp}"]
                            if df_editado.at[idx, f"Saldo {desp}"] <= 0.01:
                                df_editado.at[idx, f"Pago {desp}"] = True
                            df_editado.to_csv(ARQUIVO_VENDAS, index=False)
                            st.success(f"Pagamento registrado em {desp}.")
                            st.rerun()


                if st.button(f"↩️ Excluir Pagamento Parcial ({desp})", key=f"excluir_parcial_{desp}_{idx}"):
                    df_editado.at[idx, f"Parcial {desp}"] = 0.0
                    df_editado.at[idx, f"Saldo {desp}"] = df_editado.at[idx, desp]
                    df_editado.at[idx, f"Pago {desp}"] = False
                    df_editado.to_csv(ARQUIVO_VENDAS, index=False)
                    st.success(f"Pagamento parcial excluído em {desp}.")
                    st.rerun()


elif aba == "💰 Controle de Recebimentos":
    st.title("💰 Controle de Recebimentos")

    if not vendas_df.empty:
        vendas_df["Identificador"] = vendas_df.apply(
            lambda row: f"{row['Data']} - {row['Cliente']} - {row['Modelo']} - {formatar_moeda(row['Valor da Venda'])}",
            axis=1
        )
        opcoes_vendas = vendas_df["Identificador"].tolist()
    else:
        opcoes_vendas = []

    if opcoes_vendas:
        with st.form("form_receb"):
            col1, col2 = st.columns(2)
            with col1:
                data_receb = st.date_input("Data do Recebimento", value=date.today())
                venda_selecionada = st.selectbox("Selecione a Venda", opcoes_vendas)
            with col2:
                valor_recebido = st.number_input("Valor Recebido", min_value=0.0, step=100.0)
                forma_pagto = st.selectbox("Forma de Pagamento", ["PIX", "Cartão", "Dinheiro", "Transferência", "Outro"])
                obs = st.text_input("Observação (opcional)")

            enviado_receb = st.form_submit_button("Salvar Recebimento")

            if enviado_receb:
                if valor_recebido <= 0:
                    st.warning("⚠️ O valor recebido deve ser maior que zero.")
                    st.stop()

                if os.path.exists(ARQUIVO_RECEB):
                    shutil.copy(ARQUIVO_RECEB, ARQUIVO_RECEB + ".bak")

                linha_venda = vendas_df[vendas_df["Identificador"] == venda_selecionada].iloc[0]
                cliente_receb = linha_venda["Cliente"]
                modelo_receb = linha_venda["Modelo"]
                id_receb = linha_venda["ID"]

                novo = {
                    "ID Venda": id_receb,
                    "Data": data_receb.strftime('%d/%m/%Y'),
                    "Cliente": cliente_receb,
                    "Modelo": modelo_receb,
                    "Valor Recebido": valor_recebido,
                    "Forma de Pagamento": forma_pagto,
                    "Observação": obs
                }
                receb_df = pd.concat([receb_df, pd.DataFrame([novo])], ignore_index=True)
                receb_df.to_csv(ARQUIVO_RECEB, index=False)
                st.success("✅ Recebimento registrado com sucesso!")
    else:
        st.info("Nenhuma venda cadastrada ainda para vincular recebimentos.")

    st.subheader("📄 Recebimentos Registrados")

    if not receb_df.empty:
        df_visual = receb_df.copy()
        df_visual["Valor Recebido"] = df_visual["Valor Recebido"].apply(formatar_moeda)
        st.dataframe(df_visual, use_container_width=True)
        total_recebido_geral = receb_df["Valor Recebido"].sum()
        st.metric("💵 Total Recebido no Período", formatar_moeda(total_recebido_geral))

        st.subheader("🗑️ Excluir Recebimentos Individuais")

        indices_para_excluir = []
        for idx in range(len(receb_df)):
            col1, col2 = st.columns([10, 1])
            dados = receb_df.iloc[idx]
            linha = (
                f"{dados['Data']} | {dados['Cliente']} | {dados['Modelo']} | "
                f"{formatar_moeda(dados['Valor Recebido'])} | {dados['Forma de Pagamento']}"
            )
            with col1:
                st.markdown(linha)
            with col2:
                if st.button("🗑️", key=f"del_rec_{idx}"):
                    indices_para_excluir.append(idx)

        if "indices_excluir_receb" not in st.session_state:
            st.session_state.indices_excluir_receb = []

        if indices_para_excluir:
            st.session_state.indices_excluir_receb = indices_para_excluir

        if st.session_state.indices_excluir_receb:
            st.warning("⚠️ Você marcou registros de recebimentos para exclusão.")
            confirmar = st.checkbox("Confirmar exclusão dos recebimentos selecionados?")
            if confirmar:
                if os.path.exists(ARQUIVO_RECEB):
                    shutil.copy(ARQUIVO_RECEB, ARQUIVO_RECEB + ".bak")
                receb_df = receb_df.drop(index=st.session_state.indices_excluir_receb).reset_index(drop=True)
                receb_df.to_csv(ARQUIVO_RECEB, index=False)
                st.success("✅ Recebimento(s) excluído(s) com sucesso!")
                st.session_state.indices_excluir_receb = []
    else:
        st.info("Nenhum recebimento registrado ainda.")

    st.subheader("💼 Resumo de Saldos por Cliente e Modelo")

    resumo = vendas_df[["ID", "Cliente", "Modelo", "Valor da Venda"]].copy()

    resumo = pd.merge(
        resumo,
        receb_df.groupby("ID Venda")["Valor Recebido"].sum().reset_index().rename(columns={"ID Venda": "ID"}),
        how="left",
        on="ID"
    )

    resumo["Valor Recebido"] = resumo["Valor Recebido"].fillna(0)
    resumo["Saldo Devedor"] = resumo["Valor da Venda"] - resumo["Valor Recebido"]
    resumo["Status"] = resumo["Saldo Devedor"].apply(
        lambda x: "✅ Quitado" if x <= 0 else "🔴 Em Aberto"
    )

    resumo_exibe = resumo.copy()
    resumo_exibe["Valor da Venda"] = resumo_exibe["Valor da Venda"].apply(formatar_moeda)
    resumo_exibe["Valor Recebido"] = resumo_exibe["Valor Recebido"].apply(formatar_moeda)
    resumo_exibe["Saldo Devedor"] = resumo_exibe["Saldo Devedor"].apply(formatar_moeda)

    st.dataframe(
        resumo_exibe[["ID", "Cliente", "Modelo", "Valor da Venda", "Valor Recebido", "Saldo Devedor", "Status"]],
        use_container_width=True
    )


# 📊 Relatórios e Métricas (versão personalizada)
elif aba == "📊 Dashboards":
    st.title("📊 Relatórios e Métricas Financeiras")

    if vendas_df.empty:
        st.info("Nenhuma venda cadastrada ainda.")
    else:
        st.subheader("📋 Tabela Resumo de Métricas")

        # Calcular totais
        total_vendas = vendas_df["Valor da Venda"].sum()
        total_custo = vendas_df["Custo"].sum()
        total_icms = vendas_df["ICMS (10%)"].sum()
        total_simples = vendas_df["Simples (4,5%)"].sum()
        total_royalties = vendas_df["Royalties (7,5%)"].sum()
        total_propaganda = vendas_df["Propag. (1,5%)"].sum()
        total_corretor = vendas_df["Corretor (3%)"].sum()
        total_adm = vendas_df["Desp. ADM (5%)"].sum()

        # Soma das despesas variáveis
        total_despesas_gerais = (
            total_icms + total_simples + total_royalties +
            total_propaganda + total_corretor + total_adm
        )

        lucro_bruto = total_vendas - total_custo
        lucro_liquido = lucro_bruto - total_despesas_gerais

        # Criar DataFrame com nomes igual a imagem
        df_relatorio = pd.DataFrame({
            "MÉTRICAS": [
                "Total Vendas",
                "Total Custo",
                "Total ICMS",
                "Total Simples Nacional",
                "Total Royalties",
                "Total Propaganda",
                "Total Corretagem",
                "Total Despesas ADM",
                "Total Despesas Gerais",
                "Lucro Bruto Acumulado",
                "Lucro Líquido Final"
            ],
            "VALOR R$": [
                formatar_moeda(total_vendas),
                formatar_moeda(total_custo),
                formatar_moeda(total_icms),
                formatar_moeda(total_simples),
                formatar_moeda(total_royalties),
                formatar_moeda(total_propaganda),
                formatar_moeda(total_corretor),
                formatar_moeda(total_adm),
                formatar_moeda(total_despesas_gerais),
                formatar_moeda(lucro_bruto),
                formatar_moeda(lucro_liquido)
            ]
        })

        st.table(df_relatorio)
        st.subheader("📋 Relatório de Despesas Detalhado")

        # Lista das despesas
        despesas = [
            "Custo",
            "Royalties (7,5%)",
            "Propag. (1,5%)",
            "ICMS (10%)",
            "Simples (4,5%)",
            "Corretor (3%)",
            "Desp. ADM (5%)"
        ]

        # Criar DataFrame com totais
        dados_despesas = []
        for desp in despesas:
            valor_total = vendas_df[desp].sum()
            valor_pago = vendas_df[f"Parcial {desp}"].sum()
            saldo_pendente = valor_total - valor_pago
            dados_despesas.append({
                "Despesa": desp,
                "Total Previsto": formatar_moeda(valor_total),
                "Pago Parcial/Total": formatar_moeda(valor_pago),
                "Saldo a Pagar": formatar_moeda(saldo_pendente)
            })

        df_despesas = pd.DataFrame(dados_despesas)

        st.table(df_despesas)


        st.subheader("📈 Gráfico de Lucro Líquido Mensal")

        # Preparar dados
        df_vendas = vendas_df.copy()
        df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True)
        df_vendas["AnoMes"] = df_vendas["Data"].dt.strftime("%Y-%m")
        lucro_mensal = df_vendas.groupby("AnoMes")["Lucro Líquido"].sum().reset_index()

        chart_lucro = alt.Chart(lucro_mensal).mark_bar(color="#4e79a7").encode(
            x=alt.X("AnoMes:N", title="Mês/Ano", sort=None),
            y=alt.Y("Lucro Líquido:Q", title="Lucro Líquido"),
            tooltip=["AnoMes", "Lucro Líquido"]
        ).properties(height=300)

        st.altair_chart(chart_lucro, use_container_width=True)


elif aba == "🏠 Dashboard Consolidado":
    st.title("🏠 Visão Geral Consolidada")

    # Bloco de métricas principais
    st.subheader("📈 Métricas Gerais")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Vendas", formatar_moeda(vendas_df["Valor da Venda"].sum()))
    col2.metric("💵 Total Recebido", formatar_moeda(receb_df["Valor Recebido"].sum() if not receb_df.empty else 0))
    col3.metric("🟡 Saldo a Receber", formatar_moeda(
        vendas_df["Valor da Venda"].sum() - (receb_df["Valor Recebido"].sum() if not receb_df.empty else 0)))
    lucro_liquido_total = vendas_df["Lucro Líquido"].sum()
    col4.metric("📊 Lucro Líquido", formatar_moeda(lucro_liquido_total))

    # Bloco de resumo de despesas
    st.subheader("💸 Resumo de Despesas")
    despesas = [
        "Custo",
        "Royalties (7,5%)",
        "Propag. (1,5%)",
        "ICMS (10%)",
        "Simples (4,5%)",
        "Corretor (3%)",
        "Desp. ADM (5%)"
    ]
    dados_despesas = []
    for desp in despesas:
        # Verificar se coluna existe
        if f"Parcial {desp}" not in vendas_df.columns:
            vendas_df[f"Parcial {desp}"] = 0.0

        valor_total = vendas_df[desp].sum()
        valor_pago = vendas_df[f"Parcial {desp}"].sum()
        saldo_pendente = valor_total - valor_pago
        dados_despesas.append({
            "Despesa": desp,
            "Total Previsto": formatar_moeda(valor_total),
            "Pago": formatar_moeda(valor_pago),
            "Saldo a Pagar": formatar_moeda(saldo_pendente)
        })
    df_despesas = pd.DataFrame(dados_despesas)
    st.table(df_despesas)

    # Bloco de gráfico de lucro mensal
    st.subheader("📊 Lucro Líquido Mensal")
    df_vendas = vendas_df.copy()
    df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True, errors="coerce")
    df_vendas = df_vendas.dropna(subset=["Data"])
    df_vendas["AnoMes"] = df_vendas["Data"].dt.strftime("%Y-%m")
    lucro_mensal = df_vendas.groupby("AnoMes")["Lucro Líquido"].sum().reset_index()

    if not lucro_mensal.empty:
        chart_lucro = alt.Chart(lucro_mensal).mark_bar(color="#4e79a7").encode(
            x=alt.X("AnoMes:N", title="Mês/Ano"),
            y=alt.Y("Lucro Líquido:Q", title="Lucro Líquido"),
            tooltip=["AnoMes", "Lucro Líquido"]
        ).properties(height=300)
        st.altair_chart(chart_lucro, use_container_width=True)
    else:
        st.info("Nenhum dado de lucro mensal para exibir.")


    st.subheader("👔 Comissão Total por Corretor")

    # Agrupar comissão
    comissoes = vendas_df.groupby("Corretor Nome")["Corretor (3%)"].sum().reset_index()
    comissoes = comissoes.rename(columns={"Corretor (3%)": "Comissão Total"})

    # Filtrar só corretores cadastrados
    comissoes = comissoes[comissoes["Corretor Nome"] != ""]

    # Formatar moeda
    comissoes["Comissão Total"] = comissoes["Comissão Total"].apply(formatar_moeda)

    # Exibir
    if not comissoes.empty:
        st.table(comissoes)
    else:
        st.info("Nenhuma comissão cadastrada ainda.")


# Importando bibliotecas necessárias
    # Bloco de alerta de recebimentos pendentes
    st.subheader("🔔 Alertas de Saldos Pendentes")
    resumo = vendas_df[["ID", "Cliente", "Modelo", "Valor da Venda"]].copy()
    resumo = pd.merge(
        resumo,
        receb_df.groupby("ID Venda")["Valor Recebido"].sum().reset_index().rename(columns={"ID Venda": "ID"}),
        how="left",
        on="ID"
    )
    resumo["Valor Recebido"] = resumo["Valor Recebido"].fillna(0)
    resumo["Saldo Devedor"] = resumo["Valor da Venda"] - resumo["Valor Recebido"]
    pendentes = resumo[resumo["Saldo Devedor"] > 0]

    def cor_linha(row):
        if row["Saldo Devedor"] <= 0:
            return ["background-color: #d4edda"] * len(row)  # Verde
        elif row["Valor Recebido"] > 0:
            return ["background-color: #fff3cd"] * len(row)  # Amarelo
        else:
            return ["background-color: #f8d7da"] * len(row)  # Vermelho


    if not pendentes.empty:
        colunas_exibir = ["ID", "Cliente", "Modelo", "Valor da Venda", "Valor Recebido", "Saldo Devedor"]

    # DataFrame com números (para cor_linha)
    df_numerico = pendentes[colunas_exibir].copy()

    # DataFrame formatado em moeda (para exibir)
    df_mostrar = df_numerico.copy()
    for col in ["Valor da Venda", "Valor Recebido", "Saldo Devedor"]:
        df_mostrar[col] = df_mostrar[col].apply(formatar_moeda)

    # Aplicar cores usando o DataFrame numérico
    styled_df = df_mostrar.style.apply(
        lambda row: (
            ["background-color: #d4edda"] * len(row)
            if df_numerico.loc[row.name, "Saldo Devedor"] <= 0
            else (
                ["background-color: #fff3cd"] * len(row)
                if df_numerico.loc[row.name, "Valor Recebido"] > 0
                else ["background-color: #f8d7da"] * len(row)
            )
        ),
        axis=1
    )

    st.dataframe(styled_df, use_container_width=True)

else:
    st.success("🎉 Nenhum saldo pendente!")


