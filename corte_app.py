import streamlit as st
from datetime import datetime
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Corte de Caja", layout="centered")
st.title("💰 Sistema de Corte de Caja")

# --- Inicialización de estado ---
if 'movimientos' not in st.session_state:
    st.session_state.movimientos = []

if 'caja_registrada' not in st.session_state:
    st.session_state.caja_registrada = False

if 'df_csv' not in st.session_state:
    st.session_state.df_csv = pd.DataFrame(columns=["tipo", "concepto", "monto", "fecha"])

if 'df_formulario' not in st.session_state:
    st.session_state.df_formulario = pd.DataFrame(columns=["tipo", "concepto", "monto", "fecha"])

# Lista de proveedores (esta lista se puede modificar según lo necesites)
proveedores = ["Proveedor A", "Proveedor B", "Proveedor C", "Proveedor D", "Proveedor E"]

# --- Función para actualizar totales ---
def actualizar_totales():
    ingresos = sum(m["monto"] for m in st.session_state.movimientos if m["tipo"] == "Ingreso")
    egresos = sum(m["monto"] for m in st.session_state.movimientos if m["tipo"] == "Egreso")
    
    # Sumar ingresos del CSV al total
    if not st.session_state.df_csv.empty:
        ingresos_csv = st.session_state.df_csv["monto"].sum()
        ingresos += ingresos_csv

    total = ingresos - egresos
    return ingresos, egresos, total

# --- Sidebar: Totales ---
st.sidebar.title("📊 Totales del Corte")
ingresos, egresos, total = actualizar_totales()

st.sidebar.markdown(f"**💵 Ingresos:** ${ingresos:.2f}")
st.sidebar.markdown(f"**💸 Egresos:** ${egresos:.2f}")
st.sidebar.markdown(f"**🧾 Total Final:** ${total:.2f}")

# --- Caja inicial ---
st.checkbox("💼 Caja", key="activar_caja")

if st.session_state.activar_caja:
    monto_caja = st.number_input("Monto inicial de caja", min_value=0.0, format="%.2f", key="monto_caja", step=500.0)
    if not st.session_state.caja_registrada and monto_caja > 0:
        st.session_state.movimientos.append({
            "tipo": "Ingreso",
            "concepto": "Caja inicial",
            "monto": monto_caja,
            "fecha": datetime.today().strftime("%Y-%m-%d")
        })
        # Agregar el movimiento de caja inicial al df_formulario
        new_mov = pd.DataFrame([{"tipo": "Ingreso", "concepto": "Caja inicial", "monto": monto_caja, "fecha": datetime.today().strftime("%Y-%m-%d")}])
        st.session_state.df_formulario = pd.concat([st.session_state.df_formulario, new_mov], ignore_index=True)
        
        st.session_state.caja_registrada = True
        st.success("Caja inicial registrada correctamente.")
        # Actualizar los totales después de agregar la caja inicial
        ingresos, egresos, total = actualizar_totales()

# --- Registrar Movimiento Manual ---
st.checkbox("📝 Registrar Movimiento", key="activar_formulario")

if st.session_state.activar_formulario:
    st.header("Registrar Movimiento")

    with st.form("form_movimiento"):
        tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Egreso"])
        
        # Lista desplegable para seleccionar proveedor
        concepto = st.selectbox("Proveedor", proveedores)
        
        monto = st.number_input("Monto", min_value=0.0, format="%.2f")
        fecha = st.date_input("Fecha", value=datetime.today())
        submit = st.form_submit_button("Agregar")

        if submit:
            if concepto and monto > 0:
                # Agregar movimiento a df_formulario usando pd.concat()
                new_mov = pd.DataFrame([{"tipo": tipo, "concepto": concepto, "monto": monto, "fecha": fecha.strftime("%Y-%m-%d")}])
                st.session_state.df_formulario = pd.concat([st.session_state.df_formulario, new_mov], ignore_index=True)
                # Agregar movimiento a la lista de movimientos
                st.session_state.movimientos.append({
                    "tipo": tipo,
                    "concepto": concepto,
                    "monto": monto,
                    "fecha": fecha.strftime("%Y-%m-%d")
                })
                st.success("Movimiento agregado correctamente.")
                # Actualizar los totales después de agregar el movimiento
                ingresos, egresos, total = actualizar_totales()
            else:
                st.warning("Por favor, ingresa un concepto y un monto válido.")

# --- Mostrar tabla de movimientos del formulario ---
st.subheader("📄 Movimientos registrados desde el formulario")

if not st.session_state.df_formulario.empty:
    st.dataframe(st.session_state.df_formulario)
else:
    st.info("No hay movimientos registrados desde el formulario.")

# --- Sidebar: Cargar desde CSV ---
st.sidebar.header("📂 Cargar desde CSV")
csv_file = st.sidebar.file_uploader("Selecciona un archivo CSV", type=["csv"])

if csv_file:
    try:
        df = pd.read_csv(csv_file)

        if "Nombre" in df.columns and "Precio" in df.columns:
            # Convertir los datos CSV a un formato adecuado para el dataframe
            fecha_actual = datetime.today().strftime("%Y-%m-%d")
            df_csv = pd.DataFrame(columns=["tipo", "concepto", "monto", "fecha"])

            for _, row in df.iterrows():
                nombre = str(row["Nombre"])
                precio = float(row["Precio"])

                if nombre and precio > 0:
                    new_mov = pd.DataFrame([{"tipo": "Ingreso", "concepto": nombre, "monto": precio, "fecha": fecha_actual}])
                    df_csv = pd.concat([df_csv, new_mov], ignore_index=True)

            # Asignar el dataframe CSV a la sesión
            st.session_state.df_csv = df_csv
            st.sidebar.success(f"{len(df)} ingresos cargados desde el CSV.")
            # Actualizar los totales después de cargar el CSV
            ingresos, egresos, total = actualizar_totales()
        else:
            st.sidebar.error("El archivo debe tener encabezados: 'Nombre' y 'Precio'")
    except Exception as e:
        st.sidebar.error(f"Error al leer el archivo: {e}")

# --- Mostrar tabla de movimientos desde el CSV ---
st.subheader("📄 Movimientos cargados desde el CSV")

if not st.session_state.df_csv.empty:
    st.dataframe(st.session_state.df_csv)
else:
    st.info("No se han cargado movimientos desde un archivo CSV.")

# --- Sidebar: Exportar a PDF ---
st.sidebar.header("📤 Exportar Corte a PDF")
fecha_exportacion = st.sidebar.date_input("Fecha del corte", value=datetime.today())

if st.sidebar.button("Aplicar Cambios"):
    if not st.session_state.df_formulario.empty or not st.session_state.df_csv.empty:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Corte de Caja - {fecha_exportacion.strftime('%Y-%m-%d')}", ln=True, align='C')
        pdf.ln(10)

        pdf.cell(200, 10, txt=f"Total Ingresos: ${ingresos:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Total Egresos: ${egresos:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Total Final: ${total:.2f}", ln=True)
        pdf.ln(10)

        # Agregar datos del formulario
        pdf.cell(200, 10, txt="--- Movimientos desde el formulario ---", ln=True)
        for _, row in st.session_state.df_formulario.iterrows():
            fila = f"{row['fecha']} | {row['tipo']} | {row['concepto']} | ${row['monto']:.2f}"
            pdf.cell(200, 8, txt=fila, ln=True)

        # Agregar datos del CSV
        #pdf.cell(200, 10, txt="--- Movimientos desde el CSV ---", ln=True)
        #for _, row in st.session_state.df_csv.iterrows():
            #fila = f"{row['fecha']} | {row['tipo']} | {row['concepto']} | ${row['monto']:.2f}"
            #pdf.cell(200, 8, txt=fila, ln=True)

        filename = f"corte_caja_{fecha_exportacion.strftime('%Y%m%d')}.pdf"
        pdf.output(filename)
        with open(filename, "rb") as file:
            st.sidebar.download_button("📥 Descargar PDF", file, file_name=filename, mime="application/pdf")
    else:
        st.sidebar.warning("No hay movimientos para exportar.")

# --- Botón para limpiar movimientos ---
st.markdown("---")
if st.button("🧹 Limpiar todos los movimientos"):
    st.session_state.df_formulario = pd.DataFrame(columns=["tipo", "concepto", "monto", "fecha"])
    st.session_state.df_csv = pd.DataFrame(columns=["tipo", "concepto", "monto", "fecha"])
    st.session_state.movimientos = []
    st.session_state.caja_registrada = False
    st.success("Todos los movimientos han sido eliminados.")
