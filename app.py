import streamlit as st
import pandas as pd
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Set page config
st.set_page_config(
    page_title="Analizador de Datos Excel",
    page_icon="📊",
    layout="wide"
)

# Create directories if they don't exist
UPLOAD_DIR = Path("uploaded_files")
DATA_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Function to load Excel file
@st.cache_data
def load_excel(file_path):
    try:
        # Read both sheets
        entradas_df = pd.read_excel(file_path, sheet_name='Entradas')
        familias_df = pd.read_excel(file_path, sheet_name='Familias')
        
        # Convert date columns
        date_columns = ['fecha_entrada_caja', 'fecha_preparación_caja']
        for col in date_columns:
            entradas_df[col] = pd.to_datetime(entradas_df[col], format='%d/%m/%y')
        
        # Merge dataframes
        merged_df = pd.merge(entradas_df, familias_df, left_on='codigo', right_on='CODIGO', how='left')
        
        return entradas_df, familias_df, merged_df
    except Exception as e:
        st.error(f"Error al cargar el archivo Excel: {str(e)}")
        return None, None, None

# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    try:
        file_path = UPLOAD_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"Error al guardar el archivo: {str(e)}")
        return None

# Sidebar for file management
st.sidebar.title("Gestión de Archivos")

# Check for default file in data folder
default_file = DATA_DIR / "data.xlsx"
if default_file.exists():
    st.sidebar.info("Archivo por defecto encontrado en la carpeta data")
    entradas_df, familias_df, merged_df = load_excel(default_file)
else:
    st.sidebar.warning("No se encontró el archivo por defecto en la carpeta data")
    entradas_df, familias_df, merged_df = None, None, None

# File uploader
uploaded_file = st.sidebar.file_uploader("Subir archivo Excel", type=['xlsx'])

# List previously uploaded files
previous_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.xlsx')]
if previous_files:
    st.sidebar.subheader("Archivos subidos anteriormente")
    selected_file = st.sidebar.selectbox("Seleccionar archivo", previous_files)
    if selected_file:
        file_path = UPLOAD_DIR / selected_file
        entradas_df, familias_df, merged_df = load_excel(file_path)

# Main content
st.title("Analizador de Datos Excel")

if uploaded_file:
    file_path = save_uploaded_file(uploaded_file)
    if file_path:
        entradas_df, familias_df, merged_df = load_excel(file_path)

if entradas_df is not None and familias_df is not None and merged_df is not None:
    # Display data preview
    st.subheader("Vista Previa de Datos")
    
    tab1, tab2, tab3 = st.tabs(["Entradas", "Familias", "Datos Combinados"])
    
    with tab1:
        st.dataframe(entradas_df)
        st.write("Información de Columnas:")
        st.write(entradas_df.dtypes)
    
    with tab2:
        st.dataframe(familias_df)
        st.write("Información de Columnas:")
        st.write(familias_df.dtypes)
    
    with tab3:
        st.dataframe(merged_df)
        st.write("Información de Columnas:")
        st.write(merged_df.dtypes)
    
    # Statistics and Visualizations
    st.subheader("Análisis de Datos")
    
    # Add month column for analysis
    merged_df['mes'] = merged_df['fecha_entrada_caja'].dt.strftime('%Y-%m')
    merged_df['año'] = merged_df['fecha_entrada_caja'].dt.year
    
    # Plot selection
    plot_type = st.selectbox(
        "Seleccionar Tipo de Gráfico",
        [
            "Distribución de Calidad por Mes",
            "Distribución de Calidad por Origen",
            "Distribución de Valores por Calidad",
            "Valor por Mes",
            "Distribución de Calidad por Familia",
            "Valor Promedio por Origen y Calidad"
        ]
    )
    
    if plot_type == "Distribución de Calidad por Mes":
        # Calculate proportions
        quality_by_month = merged_df.groupby(['mes', 'CALIDAD']).size().unstack(fill_value=0)
        quality_by_month = quality_by_month.div(quality_by_month.sum(axis=1), axis=0)
        
        fig = px.bar(quality_by_month, 
                    title="Proporción de valores de CALIDAD por Mes",
                    labels={'value': 'Proporción', 'mes': 'Mes', 'CALIDAD': 'Calidad'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == "Distribución de Calidad por Origen":
        # Calculate proportions
        quality_by_origin = merged_df.groupby(['ORIGEN', 'CALIDAD']).size().unstack(fill_value=0)
        quality_by_origin = quality_by_origin.div(quality_by_origin.sum(axis=1), axis=0)
        
        fig = px.bar(quality_by_origin,
                    title="Proporción de valores de CALIDAD por Origen",
                    labels={'value': 'Proporción', 'ORIGEN': 'Origen', 'CALIDAD': 'Calidad'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == "Distribución de Valores por Calidad":
        fig = px.box(merged_df, x='CALIDAD', y='valor',
                    title="Distribución de Valores por Calidad",
                    labels={'valor': 'Valor', 'CALIDAD': 'Calidad'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == "Valor por Mes":
        # Calculate average value by month
        value_by_month = merged_df.groupby('mes')['valor'].agg(['mean', 'sum']).reset_index()
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add average value line
        fig.add_trace(
            go.Scatter(
                x=value_by_month['mes'],
                y=value_by_month['mean'],
                name="Valor Promedio",
                line=dict(color='blue')
            )
        )
        
        # Add total value bars
        fig.add_trace(
            go.Bar(
                x=value_by_month['mes'],
                y=value_by_month['sum'],
                name="Valor Total",
                yaxis="y2",
                opacity=0.5
            )
        )
        
        # Update layout
        fig.update_layout(
            title="Valor por Mes",
            xaxis_title="Mes",
            yaxis_title="Valor Promedio",
            yaxis2=dict(
                title="Valor Total",
                overlaying="y",
                side="right"
            ),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == "Distribución de Calidad por Familia":
        quality_by_family = merged_df.groupby(['FAMILIA', 'CALIDAD']).size().unstack(fill_value=0)
        quality_by_family = quality_by_family.div(quality_by_family.sum(axis=1), axis=0)
        
        fig = px.bar(quality_by_family,
                    title="Distribución de Calidad por Familia",
                    labels={'value': 'Proporción', 'FAMILIA': 'Familia', 'CALIDAD': 'Calidad'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == "Valor Promedio por Origen y Calidad":
        avg_value = merged_df.groupby(['ORIGEN', 'CALIDAD'])['valor'].mean().reset_index()
        fig = px.bar(avg_value, x='ORIGEN', y='valor', color='CALIDAD',
                    title="Valor Promedio por Origen y Calidad",
                    labels={'valor': 'Valor Promedio', 'ORIGEN': 'Origen', 'CALIDAD': 'Calidad'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Download options
    st.subheader("Descargar Datos")
    if st.button("Descargar Datos Combinados como CSV"):
        csv = merged_df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="datos_combinados.csv",
            mime="text/csv"
        )
else:
    st.info("Por favor, suba un archivo Excel para comenzar el análisis.") 