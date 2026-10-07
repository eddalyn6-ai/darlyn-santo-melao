import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# Configuración de la página
st.set_page_config(page_title="Control de Ventas - Leguminaz", layout="wide")

st.title("📊 Control de Ventas Diarias - Leguminaz / Santo Melao")
st.markdown("Sistema de gestión de itinerarios, clientes, inventario y control de metas.")

# --- METAS CORPORATIVAS (SEGÚN DOCUMENTO) ---
METAS = {
    "AZÚCAR": {"mensual": 5500, "diaria": 229},
    "ARROZ POPULAR": {"mensual": 900, "diaria": 38},
    "ARROZ SANTO MELAO": {"mensual": 900, "diaria": 37},
    "CAFÉ": {"mensual": 400, "diaria": 17},
    "HARINA": {"mensual": 800, "diaria": 33}
}

# Inicializar Estado de la Sesión
if "pedidos" not in st.session_state:
    st.session_state.pedidos = []

# --- PESTAÑAS DEL SISTEMA ---
tab1, tab2, tab3 = st.tabs(["📝 Registro Diario y Ventas", "📊 Gráficas de Metas", "📄 Exportar Excel / Reporte"])

with tab1:
    st.subheader("1. Datos Generales de la Jornada")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        fecha_jornada = st.date_input("Fecha", datetime.now())
        vendedor_nombre = st.text_input("Vendedor", value="Darlyn Parejo")
    with col_info2:
        zona_jornada = st.text_input("Zona / Rutagrama", value="Maracay / Acarigua")
        clientes_itinerario = st.number_input("Clientes en Itinerario", min_value=0, value=11)
    with col_info3:
        clientes_nuevos = st.number_input("Clientes Nuevos Atendidos", min_value=0, value=1)
        clientes_por_atender = st.number_input("Clientes Por Atender / Pendientes", min_value=0, value=3)

    st.markdown("---")
    st.subheader("2. Registrar Venta a Cliente")
    
    with st.form("form_pedido"):
        col1, col2, col3 = st.columns(3)
        with col1:
            razon_social = st.text_input("Código - Razón Social - RIF", placeholder="Ej: 2219 Inversiones Multiexitos J-12345678")
            sunagro = st.text_input("SUNAGRO", placeholder="Opcional")
            zona = st.text_input("Zona Cliente", value=zona_jornada)
        with col2:
            rubro = st.selectbox("Rubro", [
                "Azúcar 500g", "Azúcar 900g", "Azúcar 1kg",
                "Café", "Harina", 
                "Arroz Popular", "Arroz Santo Melao"
            ])
            cant = st.number_input("Cantidad (Bultos / Fardos)", min_value=1, value=10)
            precio1 = st.number_input("Precio 1 ($)", min_value=0.0, value=0.67, step=0.01)
        with col3:
            precio2_bcv = st.number_input("Precio 2 (BCV)", min_value=0.0, value=0.0, step=0.01)
            precio_fardo = st.number_input("Precio por Fardo ($)", min_value=0.0, value=0.0, step=0.01)
            status = st.selectbox("Status", ["Activo", "Pendiente Factura", "Stock Alto", "Sin Venta"])
            condicion = st.selectbox("Condición", ["Crédito 15 días", "Contado", "Otro"])
            
        observaciones = st.text_input("Observaciones del Cliente", placeholder="Ej: Tiene factura pendiente o aún posee stock alto")
        btn_agregar = st.form_submit_button("➕ Agregar Registro de Venta")

        if btn_agregar:
            st.session_state.pedidos.append({
                "FECHA": fecha_jornada.strftime("%d/%m/%Y"),
                "CÓDIGO - RAZÓN SOCIAL - RIF": razon_social,
                "SUNAGRO": sunagro,
                "RUBRO": rubro,
                "PRECIO 1 $": precio1 if precio1 > 0 else None,
                "PRECIO 2 BCV": precio2_bcv if precio2_bcv > 0 else None,
                "PRECIO POR FARDO": precio_fardo if precio_fardo > 0 else None,
                "CANT": cant,
                "ZONA": zona,
                "STATUS": status,
                "CONDICIÓN": condicion,
                "OBSERVACIÓN": observaciones
            })
            st.success(f"Venta registrada a {razon_social} exitosamente.")

    # Muestra de datos registrados en la sesión
    if st.session_state.pedidos:
        st.subheader("📋 Ventas Registradas en el Día")
        df_pedidos = pd.DataFrame(st.session_state.pedidos)
        st.dataframe(df_pedidos, use_container_width=True)
        if st.button("🗑️ Borrar Todos los Registros"):
            st.session_state.pedidos = []
            st.rerun()

with tab2:
    st.subheader("📈 Control de Metas Diarias y Mensuales")
    
    if st.session_state.pedidos:
        df_p = pd.DataFrame(st.session_state.pedidos)
        
        # Mapeo de rubros a las categorías de metas
        def categorizar_rubro(r):
            if "Azúcar" in r: return "AZÚCAR"
            if "Café" in r: return "CAFÉ"
            if "Harina" in r: return "HARINA"
            if "Arroz Popular" in r: return "ARROZ POPULAR"
            if "Arroz Santo Melao" in r: return "ARROZ SANTO MELAO"
            return "OTROS"

        df_p["CATEGORIA"] = df_p["RUBRO"].apply(categorizar_rubro)
        resumen_ventas = df_p.groupby("CATEGORIA")["CANT"].sum().to_dict()
    else:
        resumen_ventas = {}

    # Construir dataframe de comparación con metas
    data_metas = []
    for cat, valores in METAS.items():
        vendido = resumen_ventas.get(cat, 0)
        meta_d = valores["diaria"]
        cumplimiento = (vendido / meta_d) * 100 if meta_d > 0 else 0
        data_metas.append({
            "Rubro": cat,
            "Vendido Hoy (Bultos)": vendido,
            "Meta Diaria": meta_d,
            "% Cumplimiento Diario": round(cumplimiento, 1)
        })

    df_metas_comp = pd.DataFrame(data_metas)
    
    st.dataframe(df_metas_comp, use_container_width=True)

    # Gráfica de Barras Comparativa
    fig = px.bar(
        df_metas_comp, 
        x="Rubro", 
        y=["Vendido Hoy (Bultos)", "Meta Diaria"],
        barmode="group",
        title="Comparativo: Ventas del Día vs Meta Diaria Corporativa",
        color_discrete_sequence=["#1f77b4", "#ff7f0e"]
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("📄 Exportar Excel de Referencia y Resumen Corporativo")
    
    if st.session_state.pedidos:
        df_export = pd.DataFrame(st.session_state.pedidos)
        
        # 1. Generar Excel en memoria con formato profesional Leguminaz
        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Santo Melao"
        
        # Título y Encabezados del Excel
        ws.merge_cells("A1:J1")
        ws["A1"] = "TRILLADORA, EMPAQUETADORA Y DISTRIBUIDORA LEGUMINAZ C.A."
        ws["A1"].font = Font(size=14, bold=True, color="1F4E78")
        ws["A1"].alignment = Alignment(horizontal="center")
        
        ws["A2"] = f"VENDEDOR: {vendedor_nombre}"
        ws["A2"].font = Font(size=11, bold=True)
        
        headers = ["CÓDIGO - RAZÓN SOCIAL - RIF", "SUNAGRO", "RUBRO", "PRECIO 1 $", "PRECIO 2 BCV", "PRECIO POR FARDO", "CANT", "ZONA", "STATUS", "CONDICIÓN"]
        ws.append([]) # Línea vacía
        ws.append(headers)
        
        # Estilo Encabezado Tabla
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=4, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Agregar Filas
        for row in df_export.iterrows():
            r = row[1]
            ws.append([
                r["CÓDIGO - RAZÓN SOCIAL - RIF"],
                r["SUNAGRO"],
                r["RUBRO"],
                r["PRECIO 1 $"],
                r["PRECIO 2 BCV"],
                r["PRECIO POR FARDO"],
                r["CANT"],
                r["ZONA"],
                r["STATUS"],
                r["CONDICIÓN"]
            ])

        wb.save(output)
        output.seek(0)
        
        st.download_button(
            label="📥 Descargar Archivo Excel (Formato Oficial Leguminaz)",
            data=output,
            file_name=f"Reporte_Ventas_{fecha_jornada.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        st.subheader("📲 Formato de Reporte Diarios para WhatsApp / Correo")
        
        total_bultos = df_export["CANT"].sum()
        clientes_visitados = len(df_export["CÓDIGO - RAZÓN SOCIAL - RIF"].unique())
        clientes_activos = len(df_export[df_export["CANT"] > 0]["CÓDIGO - RAZÓN SOCIAL - RIF"].unique())
        
        obs_texto = "\n".join([f"- {r['CÓDIGO - RAZÓN SOCIAL - RIF']}: {r['OBSERVACIÓN']}" for _, r in df_export.iterrows() if r['OBSERVACIÓN']])
        
        resumen_texto = f"""
*FECHA:* {fecha_jornada.strftime('%d/%m/%Y')}
*ZONA:* {zona_jornada}
*ITINERARIO:* {clientes_itinerario} clientes
*CLIENTES VISITADOS:* {clientes_visitados}
*CLIENTES ACTIVOS:* {clientes_activos}
*CLIENTES NUEVOS:* {clientes_nuevos}
*CLIENTES POR ATENDER:* {clientes_por_atender}
*BULTOS VENDIDOS:* {total_bultos}
*OBSERVACIONES:*
{obs_texto if obs_texto else 'Sin observaciones adicionales.'}
        """
        
        st.code(resumen_texto, language="markdown")
    else:
        st.info("Agregue ventas en la primera pestaña para poder exportar el reporte o generar el texto.")