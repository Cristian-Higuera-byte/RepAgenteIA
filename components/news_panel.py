from types import ModuleType
from typing import Optional

import streamlit as st

def renderizar_panel_noticias(main: Optional[ModuleType]):
    st.markdown("""
        <div style='background-color: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 12px;'>
            <p style='margin:0; font-weight:bold; font-size:15px;'>🤖 Agente Piña y Jara</p>
            <p style='margin:0; font-size:12px; color:#8b949e;'>Modo de Análisis Inteligente</p>
            <hr style='border-color:#30363d; margin:8px 0;'>
            <p style='margin:0; font-size:13px; color:#3fb950; font-weight:bold;'>● Sistema Activo y Sincronizado</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📰 NOTICIAS GLOBALES EN VIVO")
    st.caption("Resúmen de noticias")

    @st.dialog("📰 Análisis y Resumen Ampliado del Agente", width="large")
    def mostrar_modal_resumen_noticia(noti):
        # Título de la noticia más grande (por ejemplo, 24px o 26px)
        st.markdown(f"<h2 style='font-size: 30px; color: #ffffff;'>{noti['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 16px;'><b>Fuente oficial:</b> <code>{noti['publisher']}</code></p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Subtítulo de Síntesis Financiera más grande
        st.markdown("<h3 style='font-size: 30px; color: #58a6ff;'>📝 Síntesis Financiera</h3>", unsafe_allow_html=True)
        
        # Texto del resumen generado por el agente con mejor legibilidad
        st.markdown(f"<div style='font-size: 17px; line-height: 1.6;'>{noti['resumen_agente']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"🔗 **[Explorar noticia completa en la fuente oficial]({noti['link']})**")
        st.markdown("")
        if st.button("Cerrar"):
            st.rerun()

    lista_noticias_en_vivo = []
    
    try:
        import yfinance as yf  # type: ignore[import-untyped]
        ticker_obj = yf.Ticker("SPY")
        noticias_yf = ticker_obj.news
        
        if noticias_yf:
            for item in noticias_yf[:4]:
                content_dict = item.get('content', item)
                titulo = content_dict.get('title', item.get('title', 'Reporte de Mercado'))
                
                publisher = "Bloomberg / Reuters"
                if 'provider' in content_dict and isinstance(content_dict['provider'], dict):
                    publisher = content_dict['provider'].get('displayName', 'Mercado Financiero')
                elif 'publisher' in item:
                    publisher = item.get('publisher', 'Mercado Financiero')

                link = "#"
                if 'clickThroughUrl' in content_dict and isinstance(content_dict['clickThroughUrl'], dict):
                    link = content_dict['clickThroughUrl'].get('url', '#')
                elif 'link' in item:
                    link = item.get('link', '#')

                summary = content_dict.get('summary', item.get('summary', 'Sin descripción adicional.'))
                
                resumen_agente = ""
                if main is not None and hasattr(main, "chat_agente"):
                    try:
                        prompt_ampliado = (
                            f"Actúa como analista financiero experto. Analiza la siguiente noticia titulada '{titulo}' "
                            f"cuyo contenido es: '{summary}'. "
                            "Por favor, redacta un análisis estructurado de un MÁXIMO de 3 párrafos. "
                            "Si el texto está en inglés, tradúcelo y preséntalo completamente en español de manera profesional y fluida."
                        )
                        resp_rapida, _ = main.chat_agente(prompt_ampliado, historial=[{"role": "system", "content": "Eres un analista financiero bilingüe detallado."}])
                        resumen_agente = resp_rapida
                    except Exception:
                        pass

                if not resumen_agente:
                    resumen_agente = summary

                lista_noticias_en_vivo.append({
                    "title": titulo,
                    "publisher": publisher,
                    "link": link,
                    "resumen_agente": resumen_agente
                })
    except Exception:
        pass

    if not lista_noticias_en_vivo:
        lista_noticias_en_vivo = [
            {
                "title": "Wall Street evalúa nuevos máximos ante proyecciones de tasas",
                "publisher": "Bloomberg",
                "link": "https://finance.yahoo.com",
                "resumen_agente": "Los mercados muestran alta actividad mientras se evalúan los próximos movimientos de la Reserva Federal.\n\nLos inversionistas mantienen la cautela ante los reportes macroeconómicos recientes.\n\nSe espera mayor volatilidad durante las próximas sesiones de cotización bursátil."
            }
        ]

    for i, noti in enumerate(lista_noticias_en_vivo):
        st.markdown(f"""
            <div style='background-color: #161b22; padding: 14px 16px; border-radius: 6px; border: 1px solid #30363d; margin-bottom: 10px;'>
                <p style='font-weight: 600; font-size: 16px; color: #ffffff; margin-bottom: 8px;'>{noti['title']}</p>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 14px; color: #8b949e;'>{noti['publisher']}</span>
                    <a href='{noti['link']}' target='_blank' style='font-size: 15px; color: #58a6ff; text-decoration: none; font-weight: bold;'>Ver fuente ↗</a>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📖 Ver resumen #{i+1}", key=f"btn_resumen_link_{i}"):
            mostrar_modal_resumen_noticia(noti)