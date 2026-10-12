import streamlit as st
import libsql_client
import requests
import base64
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Certificados Escuelas Bíblicas 2026",
    page_icon="📜",
    layout="centered"
)

# Cabecera con logos institucionales desde assets
def render_header():
    assets_dir = Path(__file__).parent / "assets"
    preferred_order = [
        "FedAsambleasLogo.png",
        "MinecLogo.png",
        "CoordEscBiblicasLogo.png"
    ]
    
    images_b64 = []
    if assets_dir.exists():
        found_files = []
        for name in preferred_order:
            file_path = assets_dir / name
            if file_path.exists():
                found_files.append(file_path)
        
        for file_path in assets_dir.glob("*.png"):
            if file_path not in found_files:
                found_files.append(file_path)
        
        for file_path in found_files:
            try:
                with open(file_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    images_b64.append((file_path.stem, encoded))
            except Exception:
                pass
                
    if images_b64:
        imgs_html = "".join(
            f'<div style="flex: 1; text-align: center; display: flex; justify-content: center; align-items: center; min-width: 80px; padding: 0 10px;">'
            f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="max-height: 85px; max-width: 100%; height: auto; object-fit: contain;" />'
            f'</div>'
            for alt, b64 in images_b64
        )
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-around;
                align-items: center;
                gap: 15px;
                padding: 10px 0 15px 0;
            ">
                {imgs_html}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()

render_header()

# Credenciales de Turso (obtenidas desde .streamlit/secrets.toml)
turso_secrets = st.secrets.get("turso", {})
# TURSO_DATABASE_URL = (
#     st.secrets.get("TURSO_DATABASE_URL")
#     or turso_secrets.get("TURSO_DATABASE_URL")
#     or turso_secrets.get("url_re")
#     or "https://regeventos-jluptm.aws-us-east-1.turso.io"
# )
# if TURSO_DATABASE_URL.startswith("libsql://"):
#     TURSO_DATABASE_URL = TURSO_DATABASE_URL.replace("libsql://", "https://", 1)
# TURSO_AUTH_TOKEN = (
#     st.secrets.get("TURSO_AUTH_TOKEN")
#     or turso_secrets.get("TURSO_AUTH_TOKEN")
#     or turso_secrets.get("auth_token_re")
#     or ""
# )

@st.cache_resource
def get_db_client():
    return libsql_client.create_client_sync(
        #url=TURSO_DATABASE_URL,
        #auth_token=TURSO_AUTH_TOKEN
        url = st.secrets["turso"]["TURSO_DATABASE_URL"],
        auth_token = st.secrets["turso"]["TURSO_AUTH_TOKEN"]
    )

st.title("📜 Consulta de Certificados")
st.subheader("Encuentro de Maestros y Líderes de Escuela Bíblica")
st.write("Ingresa tu número de cédula (solo números) para consultar tu certificado:")

cedula_input = st.text_input("Número de Cédula (C.I.):", placeholder="Ejemplo: 11273248")

if st.button("Buscar Certificado", type="primary"):
    cedula_limpia = cedula_input.strip().replace(".", "").replace(" ", "").replace("V-", "").replace("V", "")
    
    if not cedula_limpia:
        st.warning("Por favor, ingresa un número de cédula válido.")
    else:
        try:
            client = get_db_client()
            result = client.execute("SELECT nombre, url_certif FROM escbib2026 WHERE cedula = ?", [cedula_limpia])
            
            if len(result.rows) > 0:
                row = result.rows[0]
                nombre = row[0]
                url_certif = row[1]

                st.success(f"¡Certificado encontrado para **{nombre}**!")
                
                # Vista previa de la imagen
                st.image(url_certif, caption=f"Certificado - {nombre}", use_container_width=True)

                # Descarga directa
                img_data = requests.get(url_certif).content
                st.download_button(
                    label="📥 Descargar Certificado (PNG)",
                    data=img_data,
                    file_name=f"Certificado_{nombre}.png",
                    mime="image/png"
                )
            else:
                st.error("No se encontró ningún certificado asociado a la cédula ingresada. Verifica los datos o comunícate con la coordinación.")
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")