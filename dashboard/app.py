import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="Sniper Intelligence Dashboard", layout="wide")

@st.cache_data(ttl=300) # Atualiza a cada 5 minutos
def carregar_dados():
    conn = sqlite3.connect("sniper_v10.db")
    df = pd.read_sql_query("SELECT * FROM projetos", conn)
    conn.close()
    return df

st.title("🎯 Sniper Intelligence V10")
st.subheader("Análise de Mercado Freelancer em Tempo Real")

try:
    df = carregar_dados()
    
    # 1. KPIs Rápidos
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Vagas", len(df))
    col2.metric("Score Médio", f"{df['score_sniper'].mean():.1f}")
    col3.metric("Vagas Sniper (80+)", len(df[df['score_sniper'] >= 80]))

    st.divider()

    # 2. Distribuição de Scores
    st.write("### 📈 Distribuição de Qualidade (Score)")
    fig_hist = px.histogram(df, x="score_sniper", nbins=20, color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig_hist, use_container_width=True)

    # 3. Projetos por Fonte (Marketplace)
    st.write("### 🌐 Volume por Marketplace")
    fonte_counts = df['fonte'].value_counts().reset_index()
    fig_pie = px.pie(fonte_counts, values='count', names='fonte', hole=.4)
    st.plotly_chart(fig_pie, use_container_width=True)

    # 4. Tabela de Oportunidades de Elite
    st.write("### 🏆 Top 10 Oportunidades Detectadas")
    top_vagas = df.sort_values(by="score_sniper", ascending=False).head(10)
    st.table(top_vagas[['titulo', 'score_sniper', 'fonte', 'status']])

except Exception as e:
    st.error(f"Aguardando dados... (Ou erro no banco: {e})")
    st.info("Dica: Rode o `main.py` primeiro para popular o banco de dados!")