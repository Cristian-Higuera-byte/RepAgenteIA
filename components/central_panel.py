import os

from types import ModuleType
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import streamlit as st

def renderizar_panel_central(main: Optional[ModuleType]):
    info_activos_real = st.session_state.datos_mercado_real
    activo_actual = st.session_state.get("activo_seleccionado", "NVDA")
    datos_activo = info_activos_real.get(activo_actual, {"nombre": activo_actual, "mercado": "NASDAQ", "precio": 100.0, "var": "0.00%", "sube": True})
    color_var_activo = "#3fb950" if datos_activo.get("sube", True) else "#f85149"

    # Cabecera
    st.markdown(f"""
        <div style='background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 12px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 24px; font-weight: bold; color: #ffffff;'>{datos_activo['nombre']}</span>
                    <span style='background: #30363d; color: #8b949e; padding: 4px 10px; border-radius: 4px; font-size: 14px; margin-left: 10px;'>{activo_actual} &nbsp; {datos_activo['mercado']} &nbsp; USD</span>
                </div>
                <div style='font-size: 18px; color: #8b949e; font-weight: 600; display: flex; align-items: center; gap: 8px;'>
                    Actualizado en tiempo real <span style='color: #3fb950; font-size: 20px;'>●</span>
                </div>
            </div>
            <div style='margin-top: 12px;'>
                <span style='font-size: 42px; font-weight: bold; font-family: monospace; color: #ffffff;'>${datos_activo['precio']:,.2f}</span>
                <span style='font-size: 18px; font-weight: bold; color: {color_var_activo}; margin-left: 14px;'>{datos_activo['var']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_peridos, col_tipos = st.columns([1.5, 1])

    with col_peridos:
        opciones_meses = ["1M", "2M", "3M", "4M", "5M", "6M", "7M", "8M", "9M", "10M", "11M", "1A"]
        rango_tiempo = st.select_slider(
            "Rango Temporal",
            options=opciones_meses,
            value="1M",
            key=f"rango_temporal_{activo_actual}"
        )

    with col_tipos:
        # Menú actualizado sin la opción "Torta"
        tipo_grafico = st.selectbox(
            "Tipo de Gráfico",
            options=["Velas", "Líneas", "Barras"],
            key=f"tipo_grafico_{activo_actual}"
        )

    # Renderizado de gráfico técnico principal
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')

    num_meses = 1 if rango_tiempo == "1M" else (int(rango_tiempo.replace("M", "")) if "M" in rango_tiempo else 12)
    puntos = num_meses * 4

    np.random.seed(sum(ord(c) for c in activo_actual) + num_meses)
    x_vals = pd.date_range(end=pd.Timestamp.today(), periods=puntos, freq="W")
    
    precio_actual_base = datos_activo['precio']
    precios_base = np.cumprod(1 + np.random.randn(puntos) * 0.008) 
    precios_base = precios_base / precios_base[-1] * precio_actual_base 

    if tipo_grafico == "Velas":
        apertura = precios_base + np.random.randn(puntos) * (precio_actual_base * 0.003)
        cierre = precios_base + np.random.randn(puntos) * (precio_actual_base * 0.003)
        cierre[-1] = precio_actual_base 
        maximos = np.maximum(apertura, cierre) + np.abs(np.random.randn(puntos) * (precio_actual_base * 0.002))
        minimos = np.minimum(apertura, cierre) - np.abs(np.random.randn(puntos) * (precio_actual_base * 0.002))
        
        for i in range(puntos):
            color = '#3fb950' if cierre[i] >= apertura[i] else '#f85149'
            ax.vlines(x=i, ymin=minimos[i], ymax=maximos[i], color=color, linewidth=1.5)
            ax.bar(i, height=abs(cierre[i] - apertura[i]), bottom=min(apertura[i], cierre[i]), color=color, width=0.6)
            
        ax.set_title(f"Gráfico de Velas — {activo_actual} ({rango_tiempo})", color='#ffffff', fontsize=14, fontweight='bold', pad=12)
        ax.set_ylabel("Precio en USD ($)", color='#8b949e', fontsize=12, fontweight='bold')
        ax.set_xlabel("Período de Cotización", color='#8b949e', fontsize=12, fontweight='bold')

    elif tipo_grafico == "Líneas":
        ax.plot(x_vals, precios_base, color='#3fb950', linewidth=2.2, label=f"Cierre {activo_actual}")
        ax.fill_between(x_vals, precios_base, precios_base.min() * 0.95, color='#238636', alpha=0.15)
        ax.set_title(f"Evolución de Línea Temporal — {activo_actual} ({rango_tiempo})", color='#ffffff', fontsize=14, fontweight='bold', pad=12)
        ax.set_ylabel("Precio en USD ($)", color='#8b949e', fontsize=12, fontweight='bold')
        ax.set_xlabel(f"Línea de Tiempo ({rango_tiempo})", color='#8b949e', fontsize=12, fontweight='bold')
        ax.legend(loc='upper left', frameon=True, facecolor='#161b22', edgecolor='#30363d')

    elif tipo_grafico == "Barras":
        volumenes = np.random.randint(20000, 150000, size=puntos)
        ax.bar(range(puntos), volumenes, color='#58a6ff', alpha=0.8, width=0.6)
        ax.set_title(f"Volumen Operativo — {activo_actual} ({rango_tiempo})", color='#ffffff', fontsize=14, fontweight='bold', pad=12)
        ax.set_ylabel("Volumen Negociado (Acciones)", color='#8b949e', fontsize=12, fontweight='bold')
        ax.set_xlabel("Sesiones Bursátiles", color='#8b949e', fontsize=12, fontweight='bold')

    ax.grid(True, color='#30363d', linestyle='--', alpha=0.5)
    ax.tick_params(colors='#8b949e', labelsize=11)
    for spine in ax.spines.values():
        spine.set_edgecolor('#30363d')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # --- ZONA DE CHAT INFERIOR CONECTADA A main.py ---
    st.markdown("---")
    st.markdown("### 🤖 Asistente IA Analítico (Consola, Gráficos e Imágenes)")
    st.caption("Interactúa libremente con el agente bursátil. Mantiene contexto, herramientas, gráficos interactivos e imágenes renderizadas.")

    if "mensajes_ui" not in st.session_state:
        st.session_state.mensajes_ui = [
            {"role": "assistant", "content": "¡Hola! Estoy listo. Pregúntame sobre cualquier activo, mercado o pídeme gráficos y su respectiva imagen renderizada."}
        ]
    
    if "historial_tecnico_agente" not in st.session_state:
        st.session_state.historial_tecnico_agente = None

    contenedor_chat_central = st.container(height=450)
    with contenedor_chat_central:
        for mensaje in st.session_state.mensajes_ui:
            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])
                if "chart_data" in mensaje and mensaje["chart_data"] is not None:
                    st.line_chart(mensaje["chart_data"])
                if "imagen_path" in mensaje and mensaje["imagen_path"] is not None:
                    st.image(mensaje["imagen_path"], caption="Imagen renderizada del análisis técnico", use_container_width=True)

    if prompt_usuario := st.chat_input("Escribe tu consulta o pide un gráfico en imagen..."):
        st.session_state.mensajes_ui.append({"role": "user", "content": prompt_usuario})
        with contenedor_chat_central:
            with st.chat_message("user"):
                st.markdown(prompt_usuario)

        with contenedor_chat_central:
            with st.chat_message("assistant"):
                with st.spinner("El agente está procesando la solicitud y generando la imagen del gráfico..."):
                    
                    respuesta_final = ""
                    chart_data_resultado = None
                    imagen_resultado_path = None
                    prompt_lower = prompt_usuario.lower()

                    if main is not None and hasattr(main, "chat_agente"):
                        try:
                            respuesta_final, st.session_state.historial_tecnico_agente = main.chat_agente(
                                prompt_usuario, 
                                st.session_state.historial_tecnico_agente
                            )
                        except Exception as e:
                            respuesta_final = f"Error al ejecutar el agente en main.py: {str(e)}"
                    else:
                        respuesta_final = "No se pudo importar la función `chat_agente` desde `main.py`."

                    if any(kw in prompt_lower for kw in ["gráfico", "grafico", "graficar", "imagen", "figura", "tendencia", "rendimiento", "evolución"]):
                        activo_encontrado = "ACTIVO"
                        for act in ["tesla", "tsla", "apple", "aapl", "nvidia", "nvda", "spy", "qqq", "bitcoin", "btc"]:
                            if act in prompt_lower:
                                activo_encontrado = act.upper()
                                break
                        
                        np.random.seed(len(prompt_usuario) + 7)
                        valores = np.random.randn(30).cumsum() + 100
                        chart_data_resultado = pd.DataFrame(valores, columns=[f'Rendimiento - {activo_encontrado}'])

                        plt.style.use('dark_background')
                        fig, ax = plt.subplots(figsize=(8, 4))
                        ax.plot(valores, color='#3fb950', linewidth=2, label=f'Tendencia {activo_encontrado}')
                        ax.fill_between(range(len(valores)), valores, float(np.min(valores) - 5), color='#238636', alpha=0.2)
                        ax.set_title(f"Análisis Técnico y Gráfico Renderizado - {activo_encontrado}", color='white', fontsize=12, fontweight='bold')
                        ax.set_xlabel("Sesiones", color='#8b949e')
                        ax.set_ylabel("Valor (USD)", color='#8b949e')
                        ax.grid(True, color='#30363d', linestyle='--', alpha=0.5)
                        ax.legend(loc='upper left')
                        
                        os.makedirs("downloads", exist_ok=True)
                        imagen_filename = f"downloads/grafico_{activo_encontrado.lower()}.png"
                        plt.savefig(imagen_filename, dpi=200, bbox_inches='tight')
                        plt.close(fig)
                        
                        imagen_resultado_path = imagen_filename
                        respuesta_final += f"\n\n*Gráfico interactivo e imagen renderizada con éxito para **{activo_encontrado}**.*"

                    st.markdown(respuesta_final)
                    if chart_data_resultado is not None:
                        st.line_chart(chart_data_resultado)
                    if imagen_resultado_path is not None:
                        st.image(imagen_resultado_path, caption=f"Imagen renderizada del análisis", use_container_width=True)

                    st.session_state.mensajes_ui.append({
                        "role": "user", 
                        "content": prompt_usuario
                    })
                    st.session_state.mensajes_ui.append({
                        "role": "assistant", 
                        "content": respuesta_final,
                        "chart_data": chart_data_resultado,
                        "imagen_path": imagen_resultado_path
                    })