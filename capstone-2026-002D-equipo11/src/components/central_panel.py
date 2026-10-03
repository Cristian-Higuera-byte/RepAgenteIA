import json
import os
import time
from html import escape
from types import ModuleType
from typing import Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import MetaTrader5 as mt5  # type: ignore[import-untyped]
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import streamlit as st
import streamlit.components.v1 as components

# Importar las funciones del puente de MetaTrader 5
from tools.mt5_bridge import (
    inicializar_mt5,
    obtener_datos_historicos,
    obtener_precio_actual,
)

# URL de la API que sirve las velas al gráfico (/velas y /ultima).
API_URL = os.environ.get("MT5_API_URL", "http://localhost:8000")

# ==========================================================================
# Plantilla HTML del gráfico con Menú Desplegable de Líneas y Herramientas Pro
# ==========================================================================
_CHART_TEMPLATE = """
<style>
    body { background-color: #0d1117; margin: 0; padding: 0; color: #d1d4dc; }
    #tv-wrap { background:#0d1117; border:1px solid #30363d; border-radius:8px; overflow:hidden; display:flex; flex-direction:column; height:100vh; box-sizing:border-box; }
    
    #tv-wrap:fullscreen {
        border: none; border-radius: 0; width: 100vw; height: 100vh; background: #0d1117;
    }
    #tv-wrap:-webkit-full-screen {
        border: none; border-radius: 0; width: 100vw; height: 100vh; background: #0d1117;
    }

    #tv-topbar {
        display:flex; align-items:center; justify-content:space-between;
        padding:10px 14px; border-bottom:1px solid #1b2430; background:#0d1117;
        font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
        flex-shrink: 0; z-index: 50;
    }
    #tv-legend {
        position:absolute; top:8px; left:12px; z-index:15; pointer-events:none;
        display:flex; flex-direction:column; gap:3px;
        font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
        text-shadow:0 0 6px #0d1117, 0 0 3px #0d1117;
    }
    #tv-legend .lg-line { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:12px; }
    #tv-legend .lg-sym { font-size:14px; font-weight:700; color:#ffffff; }
    #tv-legend .lg-dot { color:#484f58; }
    #tv-legend .lg-tf, #tv-legend .lg-feed { color:#8b949e; font-weight:500; }
    #tv-legend .tv-ohlc { color:#8b949e; font-family:ui-monospace,Consolas,monospace; font-size:12px; }
    #tv-legend .tv-ohlc b { font-weight:600; margin-right:8px; }
    #tv-legend .tv-vol { color:#8b949e; font-family:ui-monospace,Consolas,monospace; font-size:12px; }

    #tv-actions { display:flex; align-items:center; gap:8px; }
    .tvbtn {
        display:flex; align-items:center; gap:7px;
        background:rgba(255,255,255,0.04); border:1px solid #30363d; color:#c9d1d9;
        font-size:13px; font-weight:500; padding:6px 11px; border-radius:6px; cursor:pointer;
        transition: background .15s ease, color .15s ease, border-color .15s ease;
    }
    .tvbtn svg {
        width:17px; height:17px; fill:none; stroke:currentColor;
        stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0;
    }
    .tvbtn svg.caret { width:10px; height:10px; stroke-width:1.8; opacity:.7; }
    .tvbtn.icon { padding:6px 8px; }
    .tvbtn:hover { background:rgba(255,255,255,0.08); color:#ffffff; border-color:#8b949e; }
    .tvbtn.activo { background:rgba(139,92,246,0.2); color:#a78bfa; border-color:rgba(139,92,246,0.5); }
    .tv-drop-item .lbl { display:flex; align-items:center; gap:10px; }
    .tv-drop-item svg {
        width:16px; height:16px; fill:none; stroke:currentColor;
        stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0;
    }

    /* Menús desplegables superiores */
    .tv-dropdown { position: relative; display: inline-block; }
    .tv-dropdown-content {
        display: none; position: absolute; right: 0; top: 100%;
        background-color: #161b22; min-width: 210px;
        box-shadow: 0px 8px 24px rgba(0,0,0,0.6);
        z-index: 1000; border: 1px solid #30363d; border-radius: 6px; padding: 4px 0;
    }
    .tv-dropdown-content.show { display: block; }
    .tv-drop-item {
        color: #d1d4dc; padding: 9px 14px; text-decoration: none; display: flex;
        align-items: center; justify-content: space-between; font-size: 13px; cursor: pointer;
        transition: background 0.1s;
    }
    .tv-drop-item:hover { background-color: rgba(139,92,246,0.2); color: #a78bfa; }

    #tv-body { display:flex; flex: 1; position: relative; overflow: hidden; flex-direction: column; }
    #tv-main-canvas-area { display: flex; flex: 1; position: relative; overflow: hidden; }
    
    #tv-toolbar-left {
        display:flex; flex-direction:column; align-items:center; gap:4px;
        padding:8px 4px; border-right:1px solid #1b2430; background:#0d1117;
        flex-shrink: 0; z-index: 20;
    }
    .tvtool {
        width:34px; height:34px; display:flex; align-items:center; justify-content:center;
        background:transparent; border:none; color:#8b949e; padding:0;
        border-radius:6px; cursor:pointer; transition: background .15s ease, color .15s ease;
        position: relative;
    }
    .tvtool svg {
        width:20px; height:20px; fill:none; stroke:currentColor;
        stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round;
        pointer-events:none;
    }
    .tvtool:hover { background:rgba(255,255,255,0.08); color:#ffffff; }
    .tvtool.active { background:rgba(139,92,246,0.18); color:#a78bfa; }
    .tvsep { width:22px; height:1px; background:#1b2430; margin:4px 0; flex-shrink:0; }

    /* Menú flotante lateral para herramientas de línea */
    .tvtool-group { position: relative; display: flex; align-items: center; }
    .tvtool-arrow {
        position: absolute; right: 2px; bottom: 2px; width: 8px; height: 8px;
        font-size: 8px; color: #8b949e; pointer-events: none;
    }
    .tvtool-flyout {
        display: none; position: absolute; left: 42px; top: 0;
        background-color: #161b22; min-width: 200px;
        box-shadow: 0px 8px 24px rgba(0,0,0,0.7);
        z-index: 2000; border: 1px solid #30363d; border-radius: 6px; padding: 6px 0;
        max-height: calc(100vh - 24px); overflow-y: auto;
    }
    .tvtool-flyout.show { display: block; }
    .tvtool-flyout-item {
        color: #d1d4dc; padding: 8px 14px; display: flex; align-items: center; gap: 10px;
        font-size: 13px; cursor: pointer; white-space: nowrap; transition: background 0.1s;
    }
    .tvtool-flyout-item:hover { background-color: rgba(139,92,246,0.2); color: #a78bfa; }
    .tvtool-flyout-item svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 1.5; flex-shrink:0; }

    #chart-wrapper { flex:1; position: relative; width: 100%; height: 100%; display: flex; flex-direction: column; }
    #c { flex:1; width: 100%; height: 100%; }
    
    #drawing-canvas {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 10;
    }

    #rsi-container { height: 110px; width: 100%; border-top: 1px solid #1b2430; display: none; }

    #tv-rangebar {
        display:flex; align-items:center; gap:4px; padding:8px 12px;
        border-top:1px solid #1b2430; background:#0d1117;
        font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
        flex-shrink: 0; overflow-x: auto; z-index: 20;
    }
    .tvrange {
        background:transparent; border:1px solid transparent; color:#8b949e; font-size:13px;
        font-weight:600; padding:6px 12px; border-radius:6px; cursor:pointer; white-space: nowrap;
        transition: background .15s ease, color .15s ease, border-color .15s ease;
    }
    .tvrange:hover { background:rgba(255,255,255,0.08); color:#ffffff; }
    .tvrange.active { background:rgba(88,166,255,0.18); color:#58a6ff; border-color:rgba(88,166,255,0.3); }
    #tv-tf { display:flex; align-items:center; gap:2px; font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }
    .tvtf {
        background:transparent; border:1px solid transparent; color:#8b949e; font-size:12px;
        font-weight:600; padding:5px 8px; border-radius:6px; cursor:pointer; white-space:nowrap;
        transition: background .15s ease, color .15s ease, border-color .15s ease;
    }
    .tvtf:hover { background:rgba(255,255,255,0.08); color:#ffffff; }
    .tvtf.active { background:rgba(88,166,255,0.18); color:#58a6ff; border-color:rgba(88,166,255,0.3); }
    .tv-rangelabel { color:#6e7681; font-size:12px; font-weight:600; padding:0 8px 0 2px; white-space:nowrap; }
</style>

<div id="tv-wrap">
    <div id="tv-topbar">
        <div id="tv-tf" title="Temporalidad">
            <button class="tvtf" data-tf="M1" data-n="1500">M1</button>
            <button class="tvtf" data-tf="M5" data-n="1500">M5</button>
            <button class="tvtf" data-tf="M15" data-n="1500">M15</button>
            <button class="tvtf" data-tf="M30" data-n="1500">M30</button>
            <button class="tvtf active" data-tf="H1" data-n="1500">H1</button>
            <button class="tvtf" data-tf="H4" data-n="1500">H4</button>
            <button class="tvtf" data-tf="D1" data-n="1000">D1</button>
            <button class="tvtf" data-tf="W1" data-n="520">W1</button>
            <button class="tvtf" data-tf="MN1" data-n="180">MN</button>
        </div>
        <div id="tv-actions">
            <!-- Selector Tipo de Gráfico -->
            <div class="tv-dropdown" id="type-dropdown">
                <button class="tvbtn activo" id="btn-type-select" title="Cambiar tipo de gráfico">
                    <svg viewBox="0 0 20 20"><path d="M6 3v3M6 14v3M14 5v2M14 15v2"/><rect x="4" y="6" width="4" height="8" rx=".6" fill="currentColor"/><rect x="12" y="7" width="4" height="8" rx=".6" fill="currentColor"/></svg>
                    <span>Velas</span>
                    <svg class="caret" viewBox="0 0 10 10"><path d="M2 3.5L5 6.5L8 3.5"/></svg>
                </button>
                <div class="tv-dropdown-content" id="type-menu">
                    <div class="tv-drop-item" data-type="candlestick" data-label="Velas"><span class="lbl">
                        <svg viewBox="0 0 20 20"><path d="M6 3v3M6 14v3M14 5v2M14 15v2"/><rect x="4" y="6" width="4" height="8" rx=".6" fill="currentColor"/><rect x="12" y="7" width="4" height="8" rx=".6" fill="currentColor"/></svg>
                        Velas Japonesas</span></div>
                    <div class="tv-drop-item" data-type="hollow" data-label="Velas huecas"><span class="lbl">
                        <svg viewBox="0 0 20 20"><path d="M6 3v3M6 14v3M14 5v2M14 15v2"/><rect x="4" y="6" width="4" height="8" rx=".6"/><rect x="12" y="7" width="4" height="8" rx=".6"/></svg>
                        Velas Huecas</span></div>
                    <div class="tv-drop-item" data-type="bars" data-label="Barras"><span class="lbl">
                        <svg viewBox="0 0 20 20"><path d="M6 3v14M6 7H3.5M6 13h2.5M14 4v13M14 8h-2.5M14 13h2.5"/></svg>
                        Barras (OHLC)</span></div>
                    <div class="tv-drop-item" data-type="line" data-label="Línea"><span class="lbl">
                        <svg viewBox="0 0 20 20"><path d="M2.5 14l4.5-5 3.5 3L17.5 5"/></svg>
                        Línea</span></div>
                    <div class="tv-drop-item" data-type="area" data-label="Área"><span class="lbl">
                        <svg viewBox="0 0 20 20"><path d="M2.5 14l4.5-5 3.5 3L17.5 5V17H2.5z" fill="currentColor" fill-opacity=".18" stroke="none"/><path d="M2.5 14l4.5-5 3.5 3L17.5 5"/></svg>
                        Área</span></div>
                    <div class="tv-drop-item" data-type="heikin" data-label="Heikin Ashi"><span class="lbl">
                        <svg viewBox="0 0 20 20"><path d="M4.5 4v2M4.5 13v3M10 3v3M10 12v2M15.5 6v2M15.5 15v2"/><rect x="3" y="6" width="3" height="7" rx=".5"/><rect x="8.5" y="6" width="3" height="6" rx=".5" fill="currentColor"/><rect x="14" y="8" width="3" height="7" rx=".5"/></svg>
                        Heikin Ashi</span></div>
                </div>
            </div>

            <!-- Selector de Indicadores Funcionales (Estilo Modal Búsqueda) -->
            <div class="tv-dropdown" id="ind-dropdown">
                <button class="tvbtn" id="btn-ind-select" title="Añadir indicadores técnicos">
                    <svg viewBox="0 0 20 20"><path d="M2.5 11c1.8-6 3.6-6 5.4 0s3.6 6 5.4 0 2.4-3 4.2-3"/></svg>
                    <span>Indicadores</span>
                    <svg class="caret" viewBox="0 0 10 10"><path d="M2 3.5L5 6.5L8 3.5"/></svg>
                </button>
            </div>

            <button class="tvbtn icon" id="btn-shot" title="Descargar imagen del gráfico">
                <svg viewBox="0 0 20 20"><path d="M3 7h2.8l1.2-2h6l1.2 2H17v9H3z"/><circle cx="10" cy="11.2" r="2.8"/></svg>
            </button>
            <button class="tvbtn icon" id="btn-full" title="Pantalla completa">
                <svg viewBox="0 0 20 20"><path d="M3 7.5V3h4.5M12.5 3H17v4.5M17 12.5V17h-4.5M7.5 17H3v-4.5"/></svg>
            </button>
        </div>
    </div>
    
    <div id="tv-body">
        <div id="tv-main-canvas-area">
            <div id="tv-toolbar-left">
                <button class="tvtool active" id="tool-cross" data-tool="cross" title="Cursor / Cruz">
                    <svg viewBox="0 0 20 20"><path d="M10 2.5v5M10 12.5v5M2.5 10h5M12.5 10h5"/></svg>
                </button>
                <div class="tvsep"></div>
                
                <!-- HERRAMIENTAS DE DIBUJO -->
                <div class="tvtool-group" id="group-lines">
                    <button class="tvtool" id="tool-trend" data-tool="trend" title="Herramientas de líneas">
                        <svg viewBox="0 0 20 20"><path d="M5.2 14.8L14.8 5.2"/><circle cx="4" cy="16" r="1.9"/><circle cx="16" cy="4" r="1.9"/></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="lines-flyout">
                        <div class="tvtool-flyout-item" data-tool="trend"><svg viewBox="0 0 20 20"><path d="M5.2 14.8L14.8 5.2"/><circle cx="4" cy="16" r="1.5"/><circle cx="16" cy="4" r="1.5"/></svg>Línea de tendencia</div>
                        <div class="tvtool-flyout-item" data-tool="ray"><svg viewBox="0 0 20 20"><path d="M4 16L16 4M16 4h-4M16 4v4"/><circle cx="4" cy="16" r="1.5"/></svg>Rayo</div>
                        <div class="tvtool-flyout-item" data-tool="extended"><svg viewBox="0 0 20 20"><path d="M2 17L18 3"/><circle cx="6" cy="14" r="1.5"/><circle cx="14" cy="6" r="1.5"/></svg>Línea extendida</div>
                        <div class="tvtool-flyout-item" data-tool="angle"><svg viewBox="0 0 20 20"><path d="M4 16L16 6M4 16h13"/><path d="M8 16a4 4 0 0 1 2.5-3.7"/></svg>Ángulo de tendencia</div>
                        <div class="tvtool-flyout-item" data-tool="hline"><svg viewBox="0 0 20 20"><path d="M2 10h16"/></svg>Línea horizontal</div>
                        <div class="tvtool-flyout-item" data-tool="hray"><svg viewBox="0 0 20 20"><path d="M4 10h12M16 10l-3-2M16 10l-3 2"/><circle cx="4" cy="10" r="1.5"/></svg>Rayo horizontal</div>
                        <div class="tvtool-flyout-item" data-tool="vline"><svg viewBox="0 0 20 20"><path d="M10 2v16"/></svg>Línea vertical</div>
                        <div class="tvtool-flyout-item" data-tool="crossline"><svg viewBox="0 0 20 20"><path d="M10 2v16M2 10h16"/><circle cx="10" cy="10" r="2"/></svg>Cruz</div>
                        <div class="tvtool-flyout-item" data-tool="channel"><svg viewBox="0 0 20 20"><path d="M3 12L15 4M5 16L17 8"/></svg>Canal paralelo</div>
                    </div>
                </div>

                <div class="tvtool-group" id="group-fibonacci">
                    <button class="tvtool" id="tool-fib" data-tool="fib" title="Herramientas Fibonacci">
                        <svg viewBox="0 0 20 20"><path d="M3 4h14M3 9h14M3 14h14"/><path d="M5 17.5L15 2.5" stroke-dasharray="2 2"/></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="fib-flyout">
                        <div class="tvtool-flyout-item" data-tool="fib"><svg viewBox="0 0 20 20"><path d="M3 4h14M3 9h14M3 14h14"/><path d="M5 17.5L15 2.5" stroke-dasharray="2 2"/></svg>Retrocesos de Fibonacci</div>
                        <div class="tvtool-flyout-item" data-tool="fib_extension"><svg viewBox="0 0 20 20"><path d="M3 14L8 7l5 4 4-6"/><path d="M3 4h14M3 9h14M3 14h14"/></svg>Extensión de Fibonacci</div>
                        <div class="tvtool-flyout-item" data-tool="fib_channel"><svg viewBox="0 0 20 20"><path d="M3 14L16 6M3 17L16 9"/><path d="M5 14v3M9 11v3M13 8v3"/></svg>Canal de Fibonacci</div>
                    </div>
                </div>

                <div class="tvtool-group" id="group-geometry">
                    <button class="tvtool" id="tool-geometry" data-tool="rectangle" title="Formas geométricas">
                        <svg viewBox="0 0 20 20"><rect x="3" y="4" width="14" height="12" rx="1"/></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="geometry-flyout">
                        <div class="tvtool-flyout-item" data-tool="rectangle"><svg viewBox="0 0 20 20"><rect x="3" y="4" width="14" height="12" rx="1"/></svg>Rectángulo</div>
                        <div class="tvtool-flyout-item" data-tool="ellipse"><svg viewBox="0 0 20 20"><ellipse cx="10" cy="10" rx="7" ry="5.5"/></svg>Elipse</div>
                        <div class="tvtool-flyout-item" data-tool="triangle"><svg viewBox="0 0 20 20"><path d="M10 3L17 16H3z"/></svg>Triángulo</div>
                        <div class="tvtool-flyout-item" data-tool="arrow"><svg viewBox="0 0 20 20"><path d="M3 16L16 4M16 4h-5M16 4v5"/></svg>Flecha</div>
                    </div>
                </div>

                <div class="tvtool-group" id="group-annotations">
                    <button class="tvtool" id="tool-text" data-tool="text" title="Anotaciones">
                        <svg viewBox="0 0 20 20"><path d="M4.5 4.5h11M10 4.5v11M7.5 15.5h5"/></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="annotations-flyout">
                        <div class="tvtool-flyout-item" data-tool="text"><svg viewBox="0 0 20 20"><path d="M4.5 4.5h11M10 4.5v11M7.5 15.5h5"/></svg>Texto</div>
                    </div>
                </div>

                <div class="tvtool-group" id="group-brush">
                    <button class="tvtool" id="tool-brush" data-tool="brush" title="Pincel (Alt+B)">
                        <svg viewBox="0 0 20 20"><path d="M16.3 3.7l-7.1 7.1"/><path d="M9.2 10.8l1.9 1.9c0 2.3-1.7 3.8-4.1 3.8H3.6c1 0 1.7-.8 1.7-1.9 0-2.2.8-3.8 3.9-3.8z"/></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="brush-flyout">
                        <div class="tvtool-flyout-item" data-tool="brush"><svg viewBox="0 0 20 20"><path d="M16.3 3.7l-7.1 7.1"/><path d="M9.2 10.8l1.9 1.9c0 2.3-1.7 3.8-4.1 3.8H3.6c1 0 1.7-.8 1.7-1.9 0-2.2.8-3.8 3.9-3.8z"/></svg>Pincel</div>
                        <div class="tvtool-flyout-item" data-tool="highlighter"><svg viewBox="0 0 20 20"><rect x="3" y="8" width="14" height="7" rx="1.5" fill="currentColor" fill-opacity=".35"/><rect x="3" y="8" width="14" height="7" rx="1.5"/></svg>Resaltador</div>
                    </div>
                </div>

                <div class="tvtool-group" id="group-arrow-marks">
                    <button class="tvtool" id="tool-arrow_up" data-tool="arrow_up" title="Flechas">
                        <svg viewBox="0 0 20 20"><polygon points="10,4 16,13 4,13" fill="currentColor"/></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="arrow-marks-flyout">
                        <div class="tvtool-flyout-item" data-tool="arrow_up"><svg viewBox="0 0 20 20"><polygon points="10,4 16,13 4,13" fill="currentColor"/></svg>Flecha hacia arriba</div>
                        <div class="tvtool-flyout-item" data-tool="arrow_down"><svg viewBox="0 0 20 20"><polygon points="10,16 4,7 16,7" fill="currentColor"/></svg>Flecha descendente</div>
                        <div class="tvtool-flyout-item" data-tool="arrow_left"><svg viewBox="0 0 20 20"><polygon points="4,10 13,4 13,16" fill="currentColor"/></svg>Flecha hacia la izquierda</div>
                        <div class="tvtool-flyout-item" data-tool="arrow_right"><svg viewBox="0 0 20 20"><polygon points="16,10 7,4 7,16" fill="currentColor"/></svg>Flecha hacia la derecha</div>
                    </div>
                </div>
                <div class="tvsep"></div>

                <div class="tvtool-group" id="group-measure">
                    <button class="tvtool" id="tool-measure" data-tool="measure" title="Herramientas de medición">
                        <svg viewBox="0 0 20 20"><g transform="rotate(-45 10 10)"><rect x="1.5" y="6.5" width="17" height="7" rx="1.2"/><path d="M5.5 6.5v2.6M8.5 6.5v1.6M11.5 6.5v2.6M14.5 6.5v1.6"/></g></svg>
                        <span class="tvtool-arrow">▼</span>
                    </button>
                    <div class="tvtool-flyout" id="measure-flyout">
                        <div class="tvtool-flyout-item" data-tool="measure"><svg viewBox="0 0 20 20"><g transform="rotate(-45 10 10)"><rect x="1.5" y="6.5" width="17" height="7" rx="1.2"/><path d="M5.5 6.5v2.6M8.5 6.5v1.6M11.5 6.5v2.6M14.5 6.5v1.6"/></g></svg>Regla de medición</div>
                    </div>
                </div>

                <button class="tvtool" id="tool-magnet" data-tool="magnet" title="Magnetismo: activado">
                    <svg viewBox="0 0 20 20"><path d="M4 4v7a6 6 0 0 0 12 0V4"/><path d="M4 4h4M12 4h4"/></svg>
                </button>
                <button class="tvtool" id="tool-keep" data-tool="keep" title="Mantener herramienta activa">
                    <svg viewBox="0 0 20 20"><path d="M5 4h10v12H5z"/><path d="M8 4v4h4V4M8 12h4"/></svg>
                </button>
                <div class="tvsep"></div>
                <button class="tvtool" id="tool-lock" data-tool="lock" title="Bloquear dibujos">
                    <svg viewBox="0 0 20 20"><rect x="4.5" y="9" width="11" height="8" rx="1.6"/><path d="M7 9V6.5a3 3 0 0 1 6 0V9"/></svg>
                </button>
                <button class="tvtool" id="tool-clear" data-tool="clear" title="Limpiar elementos">
                    <svg viewBox="0 0 20 20"><path d="M3.5 5.5h13M8 5.5V3.8h4v1.7M5.2 5.5l.8 11h8l.8-11M8.5 8.5v5M11.5 8.5v5"/></svg>
                </button>
            </div>
            <div id="chart-wrapper">
                <div id="c"></div>
                <canvas id="drawing-canvas"></canvas>
                <div id="tv-legend">
                    <div class="lg-line">
                        <span class="lg-sym">__SIMBOLO_HTML__</span><span class="lg-dot">·</span><span class="lg-tf" id="lg-tf">H1</span><span class="lg-dot">·</span><span class="lg-feed">XM</span>
                        <span class="tv-ohlc" id="tv-ohlc-vals">Cargando…</span>
                    </div>
                    <div class="lg-line"><span class="tv-vol" id="tv-vol-val"></span></div>
                </div>
            </div>
        </div>
        <div id="rsi-container"></div>
    </div>

    <div id="tv-rangebar">
        <span class="tv-rangelabel">Rango</span>
        <button class="tvrange" data-tf="M5" data-n="288">1D</button>
        <button class="tvrange" data-tf="M15" data-n="480">5D</button>
        <button class="tvrange" data-tf="H1" data-n="528">1 mes</button>
        <button class="tvrange" data-tf="H4" data-n="400">3 meses</button>
        <button class="tvrange" data-tf="D1" data-n="132">6 meses</button>
        <button class="tvrange" data-tf="D1" data-n="252">1 año</button>
        <button class="tvrange" data-tf="W1" data-n="260">5 años</button>
        <button class="tvrange" data-tf="W1" data-n="2000">Todo</button>
    </div>
</div>

<!-- Modal de Indicadores Estilo TradingView -->
<div id="ind-modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.6); z-index:5000; align-items:center; justify-content:center;">
    <div id="ind-modal-box" style="background:#161b22; border:1px solid #30363d; border-radius:10px; width:480px; max-height:80vh; display:flex; flex-direction:column; box-shadow:0 12px 40px rgba(0,0,0,0.8); font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif; color:#d1d4dc;">
        <div style="display:flex; align-items:center; justify-content:space-between; padding:16px 20px; border-bottom:1px solid #30363d;">
            <span style="font-size:16px; font-weight:bold; color:#ffffff;">Indicadores técnicos</span>
            <button id="ind-modal-close" style="background:transparent; border:none; color:#8b949e; font-size:18px; cursor:pointer;">✕</button>
        </div>
        <div style="padding:14px 20px; border-bottom:1px solid #30363d;">
            <div style="display:flex; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:8px 12px; gap:8px;">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="#8b949e" stroke-width="2"><circle cx="8.5" cy="8.5" r="5.5"/><path d="M13 13l4 4"/></svg>
                <input type="text" id="ind-search-input" placeholder="Buscar indicador (ej. RSI, Media, Bollinger...)" style="background:transparent; border:none; color:#d1d4dc; font-size:14px; outline:none; width:100%;">
            </div>
        </div>
        <div id="ind-list-container" style="overflow-y:auto; padding:8px 0; max-height:380px; flex:1;">
            <!-- Generado dinámicamente -->
        </div>
    </div>
</div>

<script>
window.onerror = function(msg, src, line){
  var e = document.getElementById('tv-ohlc-vals');
  if (e) e.innerText = 'Error JS: ' + msg + ' (línea ' + line + ')';
};
setTimeout(function(){
  var e = document.getElementById('tv-ohlc-vals');
  if (!window.LightweightCharts && e) e.innerText = 'No cargó lightweight-charts (CDN bloqueado o sin internet)';
}, 4000);
</script>

<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
(function(){
  var API = __API_URL_JS__;
  var SIMBOLO = __SIMBOLO_JS__;
  var DIGITS = __DIGITS__;
  var PIP = __PIP__;

  var PF = { type: 'price', precision: DIGITS, minMove: Math.pow(10, -DIGITS) };

  var tfActual = "H1";
  var nBarrasActual = 1500;
  var tipoActual = "candlestick";
  var datosActuales = [];

  var cargaId = 0;
  var cargando = false;
  var pollEnCurso = false;

  // Catálogo completo de indicadores disponibles
  var CATALOGO_INDICADORES = [
    { id: 'sma20', nombre: 'SMA 20 (Media Móvil Simple)', tipo: 'Superposición' },
    { id: 'sma50', nombre: 'SMA 50 (Media Móvil Simple)', tipo: 'Superposición' },
    { id: 'sma200', nombre: 'SMA 200 (Media Móvil Simple)', tipo: 'Superposición' },
    { id: 'ema20', nombre: 'EMA 20 (Media Móvil Exponencial)', tipo: 'Superposición' },
    { id: 'ema50', nombre: 'EMA 50 (Media Móvil Exponencial)', tipo: 'Superposición' },
    { id: 'bollinger', nombre: 'Bandas de Bollinger (20, 2)', tipo: 'Superposición' },
    { id: 'rsi', nombre: 'RSI (Índice de Fuerza Relativa 14)', tipo: 'Oscilador' },
    { id: 'macd', nombre: 'MACD (Convergencia/Divergencia)', tipo: 'Oscilador' },
    { id: 'atr', nombre: 'ATR (Average True Range)', tipo: 'Oscilador' },
    { id: 'stochastic', nombre: 'Oscilador Estocástico', tipo: 'Oscilador' },
    { id: 'parabolic', nombre: 'Parabolic SAR', tipo: 'Superposición' }
  ];

  var indicadores = { 
    sma20: false, sma50: false, sma200: false, 
    ema20: false, ema50: false, bollinger: false, 
    rsi: false, macd: false, atr: false, 
    stochastic: false, parabolic: false 
  };
  var seriesInd = { 
    sma20: null, sma50: null, sma200: null, 
    ema20: null, ema50: null, 
    bolsuper: null, bolmedia: null, bolinf: null,
    atr: null, macdLine: null, macdSignal: null, stoch: null, sar: null
  };

  var chartRsi = null;
  var serieRsi = null;

  function iniciar(){
    if(!window.LightweightCharts){ setTimeout(iniciar, 60); return; }

    var containerEl = document.getElementById('c');
    var chart = LightweightCharts.createChart(containerEl, {
      autoSize: true,
      layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 12 },
      grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
      timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderColor: '#30363d', minimumWidth: 72 },
      crosshair: { mode: 0 }
    });

    var serie = null;
    var serieVolumen = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'vol',
      color: 'rgba(63,185,80,0.5)'
    });
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    function crearSerie(tipo){
      if (serie) { chart.removeSeries(serie); }
      if (tipo === "candlestick") {
        serie = chart.addCandlestickSeries({ priceFormat: PF, upColor:'#3fb950', downColor:'#f85149', borderUpColor:'#3fb950', borderDownColor:'#f85149', wickUpColor:'#3fb950', wickDownColor:'#f85149' });
      } else if (tipo === "hollow") {
        serie = chart.addCandlestickSeries({ priceFormat: PF, upColor:'transparent', downColor:'#f85149', borderUpColor:'#3fb950', borderDownColor:'#f85149', wickUpColor:'#3fb950', wickDownColor:'#f85149' });
      } else if (tipo === "bars") {
        serie = chart.addBarSeries({ priceFormat: PF, upColor: '#3fb950', downColor: '#f85149' });
      } else if (tipo === "line") {
        serie = chart.addLineSeries({ priceFormat: PF, color: '#3fb950', lineWidth: 2 });
      } else if (tipo === "area") {
        serie = chart.addAreaSeries({ priceFormat: PF, lineColor:'#3fb950', lineWidth:2, topColor:'rgba(63,185,80,0.4)', bottomColor:'rgba(63,185,80,0.0)' });
      } else if (tipo === "heikin") {
        serie = chart.addCandlestickSeries({ priceFormat: PF, upColor:'#3fb950', downColor:'#f85149', borderUpColor:'#3fb950', borderDownColor:'#f85149', wickUpColor:'#3fb950', wickDownColor:'#f85149' });
      }
      if (serie) {
        serie.priceScale().applyOptions({ scaleMargins: { top: 0.08, bottom: 0.22 } });
      }
    }

    crearSerie(tipoActual);

    // ==========================================================================
    // SISTEMA DE DIBUJO PROFESIONAL CON MENÚ FLOTANTE DE LÍNEAS
    // ==========================================================================
    var canvas = document.getElementById('drawing-canvas');
    var ctx = canvas.getContext('2d');
    var wrapEl = document.getElementById('chart-wrapper');
    var activeTool = 'cross';
    var bloqueado = false;
    var imanActivo = true;

    var seleccionadoId = null;
    var hoverId = null;
    var dibujoEnCurso = null;
    var esperandoSegundoClick = false;
    var inicioClick = null;
    var arrastre = null;

    var NIVELES_FIB = [
      { val: 0.0,   color: '#f85149' }, { val: 0.236, color: '#ff9800' },
      { val: 0.382, color: '#f5c518' }, { val: 0.5,   color: '#3fb950' },
      { val: 0.618, color: '#58a6ff' }, { val: 0.786, color: '#a78bfa' },
      { val: 1.0,   color: '#f85149' }
    ];

    var estiloCursor = document.createElement('style');
    estiloCursor.textContent =
      '#chart-wrapper.cur-mover, #chart-wrapper.cur-mover * { cursor: move !important; }' +
      '#chart-wrapper.cur-punto, #chart-wrapper.cur-punto * { cursor: pointer !important; }' +
      '#chart-wrapper.cur-dibujar, #chart-wrapper.cur-dibujar * { cursor: crosshair !important; }';
    document.head.appendChild(estiloCursor);
    function setCursor(cls){
      wrapEl.classList.remove('cur-mover', 'cur-punto', 'cur-dibujar');
      if (cls) wrapEl.classList.add(cls);
    }

    var storageKey = 'dibujos_' + SIMBOLO;
    var elementosDibujados = [];
    try {
      var guardados = localStorage.getItem(storageKey);
      if (guardados) { elementosDibujados = JSON.parse(guardados); }
    } catch(e) { elementosDibujados = []; }

    var historial = [JSON.stringify(elementosDibujados)];
    var posHist = 0;

    function guardarDibujosLocal() {
      try { localStorage.setItem(storageKey, JSON.stringify(elementosDibujados)); } catch(e) {}
    }
    function confirmarCambio(){
      historial = historial.slice(0, posHist + 1);
      historial.push(JSON.stringify(elementosDibujados));
      if (historial.length > 60) historial.shift();
      posHist = historial.length - 1;
      guardarDibujosLocal();
      redibujarTodo();
    }
    function restaurarHistorial(){
      elementosDibujados = JSON.parse(historial[posHist]);
      seleccionadoId = null; hoverId = null;
      guardarDibujosLocal();
      redibujarTodo();
    }
    function deshacer(){ if (posHist > 0) { posHist--; restaurarHistorial(); } }
    function rehacer(){ if (posHist < historial.length - 1) { posHist++; restaurarHistorial(); } }

    var cssW = 0, cssH = 0;
    var sucio = true;

    function redibujarTodo(){ sucio = true; }

    function resizeCanvas() {
      var dpr = window.devicePixelRatio || 1;
      cssW = wrapEl.clientWidth;
      cssH = wrapEl.clientHeight;
      canvas.width = Math.max(1, Math.round(cssW * dpr));
      canvas.height = Math.max(1, Math.round(cssH * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      redibujarTodo();
    }

    if (window.ResizeObserver) {
      new ResizeObserver(resizeCanvas).observe(wrapEl);
    } else {
      window.addEventListener('resize', resizeCanvas);
    }
    resizeCanvas();

    function areaTrazado(){
      var anchoEje = 60, altoEje = 28;
      try { anchoEje = chart.priceScale('right').width(); } catch (e) {}
      try { altoEje = chart.timeScale().height(); } catch (e) {}
      return { w: Math.max(0, cssW - anchoEje), h: Math.max(0, cssH - altoEje) };
    }

    chart.timeScale().subscribeVisibleLogicalRangeChange(function(range){
      redibujarTodo();
      if (chartRsi && range) chartRsi.timeScale().setVisibleLogicalRange(range);
    });

    function ok(){
      for (var i = 0; i < arguments.length; i++){
        var v = arguments[i];
        if (v === null || v === undefined || typeof v !== 'number' || !isFinite(v)) return false;
      }
      return true;
    }

    var cacheSeg = { n: -1, t: -1, v: 60 };
    function segBarra(){
      var n = datosActuales.length;
      if (n < 2) return 60;
      var tUlt = datosActuales[n - 1].time;
      if (cacheSeg.n === n && cacheSeg.t === tUlt) return cacheSeg.v;
      var difs = [];
      for (var i = Math.max(1, n - 60); i < n; i++){
        var d = datosActuales[i].time - datosActuales[i - 1].time;
        if (d > 0) difs.push(d);
      }
      difs.sort(function(a, b){ return a - b; });
      cacheSeg = { n: n, t: tUlt, v: difs.length ? difs[Math.floor(difs.length / 2)] : 60 };
      return cacheSeg.v;
    }

    function tiempoALogico(t){
      var n = datosActuales.length;
      if (!n || typeof t !== 'number' || !isFinite(t)) return null;
      var seg = segBarra();
      var primero = datosActuales[0].time, ultimo = datosActuales[n - 1].time;
      if (t <= primero) return (t - primero) / seg;
      if (t >= ultimo) return (n - 1) + (t - ultimo) / seg;
      var lo = 0, hi = n - 1;
      while (hi - lo > 1){
        var mid = (lo + hi) >> 1;
        if (datosActuales[mid].time <= t) lo = mid; else hi = mid;
      }
      var t0 = datosActuales[lo].time, t1 = datosActuales[hi].time;
      return lo + (t - t0) / (t1 - t0);
    }

    function logicoATiempo(l){
      var n = datosActuales.length;
      if (!n || typeof l !== 'number' || !isFinite(l)) return null;
      var seg = segBarra();
      if (l <= 0) return datosActuales[0].time + l * seg;
      if (l >= n - 1) return datosActuales[n - 1].time + (l - (n - 1)) * seg;
      var i = Math.floor(l);
      var t0 = datosActuales[i].time, t1 = datosActuales[i + 1].time;
      return t0 + (l - i) * (t1 - t0);
    }

    function xDeTiempo(t){
      var l = tiempoALogico(t);
      if (l === null) return null;
      return chart.timeScale().logicalToCoordinate(l);
    }
    function yDePrecio(p){
      if (!serie || typeof p !== 'number') return null;
      return serie.priceToCoordinate(p);
    }

    function magnetEfectivo(e){ return imanActivo !== !!(e && e.ctrlKey); }

    function puntoDesdeMouse(x, y, conIman){
      if (!serie || !datosActuales.length) return null;
      var l = chart.timeScale().coordinateToLogical(x);
      var p = serie.coordinateToPrice(y);
      if (l === null || p === null) return null;
      if (conIman){
        var i = Math.round(l);
        if (i >= 0 && i < datosActuales.length){
          var v = datosActuales[i];
          var mejor = null, mejorD = 14;
          [v.open, v.high, v.low, v.close].forEach(function(cand){
            var cy = serie.priceToCoordinate(cand);
            if (cy !== null){
              var d = Math.abs(cy - y);
              if (d < mejorD){ mejorD = d; mejor = cand; }
            }
          });
          l = i;
          if (mejor !== null) p = mejor;
        }
      }
      var t = logicoATiempo(l);
      if (t === null) return null;
      return { l: l, time: t, price: p };
    }

    function puntoVisual(el, n){
      var t = el['time' + n], p = el['price' + n];
      return { x: xDeTiempo(t), y: yDePrecio(p) };
    }

    function geom(el){
      if (el.tipo === 'hline') return { y: yDePrecio(el.price) };
      if (el.tipo === 'vline') return { x: xDeTiempo(el.time) };
      if (el.tipo === 'text') return { x: xDeTiempo(el.time), y: yDePrecio(el.price) };
      if (el.tipo === 'crossline') return { x: xDeTiempo(el.time), y: yDePrecio(el.price) };
      var g = {};
      for (var n = 1; n <= 3; n++) {
        if (el['time' + n] === undefined) break;
        var q = puntoVisual(el, n);
        g['x' + n] = q.x; g['y' + n] = q.y;
      }
      if (!ok(g.x1, g.y1, g.x2, g.y2)) return null;
      return g;
    }

    function distSeg(px, py, x1, y1, x2, y2){
      var dx = x2 - x1, dy = y2 - y1;
      var l2 = dx * dx + dy * dy;
      var t = l2 ? ((px - x1) * dx + (py - y1) * dy) / l2 : 0;
      t = Math.max(0, Math.min(1, t));
      return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
    }

    function offsetCanal(g){
      if (!ok(g.x3, g.y3)) return { dx: 0, dy: g.y2 - g.y1 };
      var dx = g.x2 - g.x1, dy = g.y2 - g.y1;
      var len = Math.hypot(dx, dy) || 1;
      var nx = -dy / len, ny = dx / len;
      var signed = ((g.x3 - g.x1) * nx) + ((g.y3 - g.y1) * ny);
      return { dx: nx * signed, dy: ny * signed };
    }

    function extremosLinea(g, tipo){
      var dx = g.x2 - g.x1, dy = g.y2 - g.y1, len = Math.hypot(dx, dy);
      if (!len) return { ax: g.x1, ay: g.y1, bx: g.x2, by: g.y2 };
      var k = (cssW + cssH + 4000) / len;
      var r = { ax: g.x1, ay: g.y1, bx: g.x2 + dx * k, by: g.y2 + dy * k };
      if (tipo === 'extended') { r.ax = g.x1 - dx * k; r.ay = g.y1 - dy * k; }
      return r;
    }

    function hitTest(el, x, y, seleccionado){
      var g = geom(el);
      if (!g) return null;
      if (el.tipo === 'hline') return Math.abs(y - g.y) <= 6 ? 'body' : null;
      if (el.tipo === 'vline') return Math.abs(x - g.x) <= 6 ? 'body' : null;
      if (el.tipo === 'crossline') return (Math.abs(x - g.x) <= 6 || Math.abs(y - g.y) <= 6) ? 'body' : null;
      if (el.tipo === 'text'){
        ctx.font = fuenteTexto(el);
        var w = ctx.measureText(el.texto || 'Texto').width, sz = el.tamano || 13;
        return (x >= g.x - 4 && x <= g.x + w + 4 && y >= g.y - sz - 3 && y <= g.y + 6) ? 'body' : null;
      }
      if (seleccionado){
        if (Math.hypot(x - g.x1, y - g.y1) <= 10) return 'p1';
        if (Math.hypot(x - g.x2, y - g.y2) <= 10) return 'p2';
        if (ok(g.x3, g.y3) && Math.hypot(x - g.x3, y - g.y3) <= 10) return 'p3';
      }
      if (['trend','angle','arrow'].indexOf(el.tipo) >= 0){
        return distSeg(x, y, g.x1, g.y1, g.x2, g.y2) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'ray' || el.tipo === 'extended'){
        var ex = extremosLinea(g, el.tipo);
        return distSeg(x, y, ex.ax, ex.ay, ex.bx, ex.by) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'hray'){
        if (x < g.x1 - 6) return null;
        return Math.abs(y - g.y1) <= 7 ? 'body' : null;
      }
      if (el.tipo === 'channel'){
        var off = offsetCanal(g);
        var d1 = distSeg(x, y, g.x1, g.y1, g.x2, g.y2);
        var d2 = distSeg(x, y, g.x1 + off.dx, g.y1 + off.dy, g.x2 + off.dx, g.y2 + off.dy);
        return Math.min(d1, d2) <= 7 ? 'body' : null;
      }
      var xa = Math.min(g.x1, g.x2), xb = Math.max(g.x1, g.x2);
      var ya = Math.min(g.y1, g.y2), yb = Math.max(g.y1, g.y2);
      if (['measure', 'rectangle', 'ellipse', 'triangle'].indexOf(el.tipo) >= 0){
        return (x >= xa - 7 && x <= xb + 7 && y >= ya - 7 && y <= yb + 7) ? 'body' : null;
      }
      if (el.tipo === 'fib' || el.tipo === 'fib_extension'){
        if (x < xa - 8 || x > xb + 8) return null;
        var niveles = el.tipo === 'fib' ? NIVELES_FIB : NIVELES_FIB_EXT;
        for (var i = 0; i < niveles.length; i++){
          var yn = el.tipo === 'fib'
            ? g.y1 + (g.y2 - g.y1) * niveles[i].val
            : (ok(g.y3) ? g.y3 + (g.y2 - g.y1) * niveles[i].val : g.y1 + (g.y2 - g.y1) * niveles[i].val);
          if (Math.abs(y - yn) <= 6) return 'body';
        }
        return null;
      }
      return null;
    }

    function elementoBajo(x, y){
      if (seleccionadoId !== null && elementosDibujados[seleccionadoId]){
        var h = hitTest(elementosDibujados[seleccionadoId], x, y, true);
        if (h) return { idx: seleccionadoId, parte: h };
      }
      for (var i = elementosDibujados.length - 1; i >= 0; i--){
        var h2 = hitTest(elementosDibujados[i], x, y, false);
        if (h2) return { idx: i, parte: h2 };
      }
      return null;
    }

    function dibujarHandle(c, x, y, col){
      if (!ok(x,y)) return;
      c.save(); c.fillStyle = '#ffffff'; c.strokeStyle = col; c.lineWidth = 2;
      c.beginPath(); c.arc(x, y, 5, 0, 2 * Math.PI); c.fill(); c.stroke(); c.restore();
    }

    var trazoActual = { ancho: null, estilo: null, hover: 0 };
    function dibujarLinea(c, x1, y1, x2, y2, col, width, dash){
      c.strokeStyle = col; c.lineCap = 'round';
      c.lineWidth = trazoActual.ancho ? trazoActual.ancho + trazoActual.hover : (width || 2);
      var d = dash;
      if (trazoActual.estilo === 'solid') d = [];
      else if (trazoActual.estilo === 'dash') d = [8, 5];
      else if (trazoActual.estilo === 'dot') d = [2, 4];
      if (d) c.setLineDash(d);
      c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
      if (d) c.setLineDash([]);
    }

    function dibujarElemento(c, el, sel, hov){
      var g = geom(el); if (!g) return;
      c.save();
      trazoActual.ancho = el.ancho || null; trazoActual.estilo = el.estilo || null; trazoActual.hover = (hov && !sel) ? 1 : 0;
      var hoverExtra = (hov && !sel) ? 1 : 0;

      if (el.tipo === 'trend'){
        var col = el.color || '#2962ff'; dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,col,(el.ancho||2)+hoverExtra);
        if (sel){ dibujarHandle(c,g.x1,g.y1,col); dibujarHandle(c,g.x2,g.y2,col); }
      } else if (el.tipo === 'ray'){
        var colR = el.color || '#2962ff'; var exR = extremosLinea(g, 'ray');
        dibujarLinea(c,exR.ax,exR.ay,exR.bx,exR.by,colR,(el.ancho||2)+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colR);dibujarHandle(c,g.x2,g.y2,colR);}
      } else if (el.tipo === 'extended'){
        var colE = el.color || '#2962ff'; var exE = extremosLinea(g, 'extended');
        dibujarLinea(c,exE.ax,exE.ay,exE.bx,exE.by,colE,(el.ancho||2)+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colE);dibujarHandle(c,g.x2,g.y2,colE);}
      } else if (el.tipo === 'angle'){
        var colA=el.color||'#a78bfa'; dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colA,(el.ancho||2)+hoverExtra);
        var ang=Math.atan2(-(g.y2-g.y1),g.x2-g.x1)*180/Math.PI;
        c.font='11px sans-serif'; c.fillStyle=colA; c.fillText((ang>=0?'+':'')+ang.toFixed(1)+'°',g.x2+7,g.y2-7);
        if(sel){dibujarHandle(c,g.x1,g.y1,colA);dibujarHandle(c,g.x2,g.y2,colA);}
      } else if (el.tipo === 'hline'){
        var colH=el.color||'#f5c518'; dibujarLinea(c,0,g.y,cssW,g.y,colH,(el.ancho||1.5)+hoverExtra,[6,4]);
        if(sel){c.fillStyle=colH;c.fillRect(0,g.y-4,6,8);}
      } else if (el.tipo === 'hray'){
        var colHR=el.color||'#f5c518'; dibujarLinea(c,g.x1,g.y1,cssW,g.y1,colHR,(el.ancho||1.5)+hoverExtra);
        if(sel)dibujarHandle(c,g.x1,g.y1,colHR);
      } else if (el.tipo === 'vline'){
        var colV=el.color||'#58a6ff'; dibujarLinea(c,g.x,0,g.x,cssH,colV,1.5,[4,4]);
        if(sel){c.fillStyle=colV;c.fillRect(g.x-4,0,8,6);}
      } else if (el.tipo === 'crossline'){
        var colX=el.color||'#8b949e'; dibujarLinea(c,g.x,0,g.x,cssH,colX,1,[4,4]); dibujarLinea(c,0,g.y,cssW,g.y,colX,1,[4,4]);
        if(sel)dibujarHandle(c,g.x,g.y,colX);
      } else if (el.tipo === 'channel'){
        var colC=el.color||'#2962ff', oc=offsetCanal(g);
        c.globalAlpha=.08;c.fillStyle=colC;c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x2+oc.dx,g.y2+oc.dy);c.lineTo(g.x1+oc.dx,g.y1+oc.dy);c.closePath();c.fill();c.globalAlpha=1;
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colC,2+hoverExtra);dibujarLinea(c,g.x1+oc.dx,g.y1+oc.dy,g.x2+oc.dx,g.y2+oc.dy,colC,2+hoverExtra);
        if(sel){dibujarHandle(c,g.x1,g.y1,colC);dibujarHandle(c,g.x2,g.y2,colC);dibujarHandle(c,g.x3,g.y3,colC);}
      } else if (el.tipo === 'fib'){
        var xa=Math.min(g.x1,g.x2), xb=Math.max(g.x1,g.x2), dY=g.y2-g.y1, dP=el.price2-el.price1;
        var nv=NIVELES_FIB.map(function(n){return {n:n,y:g.y1+dY*n.val,precio:el.price1+dP*n.val};});
        c.globalAlpha=.07; for(var fi=0;fi<nv.length-1;fi++){c.fillStyle=nv[fi+1].n.color;c.fillRect(xa,Math.min(nv[fi].y,nv[fi+1].y),xb-xa,Math.abs(nv[fi+1].y-nv[fi].y));} c.globalAlpha=1;
        c.font='11px sans-serif'; nv.forEach(function(q){c.strokeStyle=q.n.color;c.fillStyle=q.n.color;c.beginPath();c.moveTo(xa,q.y);c.lineTo(xb,q.y);c.stroke();c.fillText(String(+q.n.val.toFixed(3))+' ('+q.precio.toFixed(DIGITS)+')',xa+5,q.y-3);});
        dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,'rgba(139,148,158,.8)',1,[4,4]);
        if(sel){dibujarHandle(c,g.x1,g.y1,'#a78bfa');dibujarHandle(c,g.x2,g.y2,'#a78bfa');}
      } else if (el.tipo === 'rectangle'){
        var colG=el.color||'#58a6ff'; var rw=g.x2-g.x1,rh=g.y2-g.y1;
        c.globalAlpha=.08;c.fillStyle=colG;c.fillRect(Math.min(g.x1,g.x2),Math.min(g.y1,g.y2),Math.abs(rw),Math.abs(rh));c.globalAlpha=1;
        c.strokeStyle=colG;c.lineWidth=(el.ancho||2)+hoverExtra;c.strokeRect(Math.min(g.x1,g.x2),Math.min(g.y1,g.y2),Math.abs(rw),Math.abs(rh));
        if(sel){dibujarHandle(c,g.x1,g.y1,colG);dibujarHandle(c,g.x2,g.y2,colG);}
      } else if (el.tipo === 'ellipse'){
        var colEl=el.color||'#58a6ff'; var cx=(g.x1+g.x2)/2,cy=(g.y1+g.y2)/2,rx=Math.abs(g.x2-g.x1)/2,ry=Math.abs(g.y2-g.y1)/2;
        c.globalAlpha=.08;c.fillStyle=colEl;c.beginPath();c.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);c.fill();c.globalAlpha=1;c.strokeStyle=colEl;c.lineWidth=(el.ancho||2)+hoverExtra;c.beginPath();c.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);c.stroke();
        if(sel){dibujarHandle(c,g.x1,g.y1,colEl);dibujarHandle(c,g.x2,g.y2,colEl);}
      } else if (el.tipo === 'triangle'){
        var colT=el.color||'#58a6ff';
        c.globalAlpha=.08;c.fillStyle=colT;c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x1,g.y2);c.closePath();c.fill();c.globalAlpha=1;c.strokeStyle=colT;c.lineWidth=(el.ancho||2)+hoverExtra;c.beginPath();c.moveTo(g.x1,g.y1);c.lineTo(g.x2,g.y2);c.lineTo(g.x1,g.y2);c.closePath();c.stroke();
        if(sel){dibujarHandle(c,g.x1,g.y1,colT);dibujarHandle(c,g.x2,g.y2,colT);}
      } else if (el.tipo === 'arrow'){
        var colAr=el.color||'#3fb950';dibujarLinea(c,g.x1,g.y1,g.x2,g.y2,colAr,2+hoverExtra);var a=Math.atan2(g.y2-g.y1,g.x2-g.x1),hs=10;
        c.fillStyle=colAr;c.beginPath();c.moveTo(g.x2,g.y2);c.lineTo(g.x2-hs*Math.cos(a-Math.PI/6),g.y2-hs*Math.sin(a-Math.PI/6));c.lineTo(g.x2-hs*Math.cos(a+Math.PI/6),g.y2-hs*Math.sin(a+Math.PI/6));c.closePath();c.fill();
        if(sel){dibujarHandle(c,g.x1,g.y1,colAr);dibujarHandle(c,g.x2,g.y2,colAr);}
      } else if (el.tipo === 'text'){
        c.font=fuenteTexto(el);c.fillStyle=el.color||'#ffffff';c.fillText(el.texto||'Texto',g.x,g.y);
        if(sel||hov){var tw=c.measureText(el.texto||'Texto').width,sz=el.tamano||13;c.strokeStyle='rgba(88,166,255,.8)';c.lineWidth=1;c.setLineDash([3,3]);c.strokeRect(g.x-4,g.y-sz-3,tw+8,sz+9);c.setLineDash([]);}
      } else if (el.tipo === 'measure'){
        var sube=el.price2>=el.price1,colM=sube?'#2962ff':'#f23645',mw=g.x2-g.x1,mh=g.y2-g.y1;
        c.globalAlpha=.15;c.fillStyle=colM;c.fillRect(g.x1,g.y1,mw,mh);c.globalAlpha=1;c.strokeStyle=colM;c.lineWidth=1;c.strokeRect(g.x1,g.y1,mw,mh);
        var l1=tiempoALogico(el.time1),l2=tiempoALogico(el.time2),barras=(l1===null||l2===null)?0:Math.abs(Math.round(l2-l1));
        var dif=el.price2-el.price1,pct=el.price1?(dif/el.price1)*100:0,textoDif=PIP>0?(dif/PIP).toFixed(1)+' pips':dif.toFixed(DIGITS);
        var txt=(dif>=0?'+':'')+textoDif+' ('+(pct>=0?'+':'')+pct.toFixed(2)+'%) · '+barras+' barras';c.font='12px sans-serif';var pw=c.measureText(txt).width+16,px0=(g.x1+g.x2)/2-pw/2,py0=sube?Math.min(g.y1,g.y2)-28:Math.max(g.y1,g.y2)+8;
        c.fillStyle=colM;c.fillRect(px0,py0,pw,20);c.fillStyle='#fff';c.textBaseline='middle';c.fillText(txt,px0+8,py0+10);
        if(sel){dibujarHandle(c,g.x1,g.y1,colM);dibujarHandle(c,g.x2,g.y2,colM);}
      }
      c.restore();
    }

    function fmtTiempo(t){
      var d=new Date(t*1000); function p(n){return (n<10?'0':'')+n;}
      return p(d.getUTCDate())+'/'+p(d.getUTCMonth()+1)+' '+p(d.getUTCHours())+':'+p(d.getUTCMinutes());
    }

    function badgePrecio(c,y,precio,fondo,texto,ap){
      if(!ok(y)||y<0||y>ap.h)return;var w=cssW-ap.w;c.save();c.fillStyle=fondo;c.fillRect(ap.w,y-10,w,20);c.fillStyle=texto;c.font='11px sans-serif';c.textBaseline='middle';c.textAlign='left';c.fillText(precio.toFixed(DIGITS),ap.w+6,y);c.restore();
    }
    function badgeTiempo(c,x,t,fondo,ap){
      var h=cssH-ap.h;if(!ok(x)||x<0||x>ap.w||h<10)return;var w=92,bx=Math.max(0,Math.min(ap.w-w,x-w/2));c.save();c.fillStyle=fondo;c.fillRect(bx,ap.h,w,h);c.fillStyle='#fff';c.font='11px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(fmtTiempo(t),bx+w/2,ap.h+h/2);c.restore();
    }
    function etiquetasEje(c,el,ap){
      if(el.tipo==='hline'){badgePrecio(c,yDePrecio(el.price),el.price,el.color||'#f5c518','#fff',ap);return;}
      if(el.tipo==='vline'){badgeTiempo(c,xDeTiempo(el.time),el.time,el.color||'#58a6ff',ap);return;}
      if(el.tipo==='hray'){badgePrecio(c,yDePrecio(el.price1),el.price1,el.color||'#f5c518','#fff',ap);return;}
      if(el.tipo==='crossline'){badgePrecio(c,yDePrecio(el.price),el.price,el.color||'#8b949e','#fff',ap);badgeTiempo(c,xDeTiempo(el.time),el.time,el.color||'#8b949e',ap);return;}
      if(el.tipo==='text')return;
      var col=el.tipo.indexOf('fib')===0?'#7c5cd6':(el.tipo==='measure'?(el.price2>=el.price1?'#2962ff':'#f23645'):(el.color||'#2962ff'));
      if(el.price1!==undefined)badgePrecio(c,yDePrecio(el.price1),el.price1,col,'#fff',ap);
      if(el.price2!==undefined)badgePrecio(c,yDePrecio(el.price2),el.price2,col,'#fff',ap);
      if(el.time1!==undefined)badgeTiempo(c,xDeTiempo(el.time1),el.time1,col,ap);
      if(el.time2!==undefined)badgeTiempo(c,xDeTiempo(el.time2),el.time2,col,ap);
    }

    function pintar(){
      ctx.clearRect(0, 0, cssW, cssH);
      if (!serie || !datosActuales.length) return;
      var ap = areaTrazado();
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, ap.w, ap.h);
      ctx.clip();
      elementosDibujados.forEach(function(el, idx){
        dibujarElemento(ctx, el, idx === seleccionadoId, idx === hoverId);
      });
      if (dibujoEnCurso) dibujarElemento(ctx, dibujoEnCurso, true, false);
      ctx.restore();

      elementosDibujados.forEach(function(el, idx){
        if (idx === seleccionadoId || el.tipo === 'hline' || el.tipo === 'vline') etiquetasEje(ctx, el, ap);
      });
      if (dibujoEnCurso) etiquetasEje(ctx, dibujoEnCurso, ap);
    }

    var ultimaFirma = '';
    function firmaVista(){
      if (!datosActuales.length || !serie) return '';
      var ref = datosActuales[datosActuales.length - 1].close;
      var ts = chart.timeScale();
      return [
        serie.priceToCoordinate(ref),
        serie.priceToCoordinate(ref * 1.01),
        ts.logicalToCoordinate(0),
        ts.logicalToCoordinate(100)
      ].join('|');
    }

    function bucleRedibujo(){
      if (elementosDibujados.length > 0 || dibujoEnCurso) {
        var f = firmaVista();
        if (sucio || f !== ultimaFirma) { ultimaFirma = f; sucio = false; pintar(); }
      } else if (sucio) {
        sucio = false;
        pintar();
      }
      requestAnimationFrame(bucleRedibujo);
    }
    requestAnimationFrame(bucleRedibujo);

    function bloquearGrafico(b){
      try { chart.applyOptions({ handleScroll: !b, handleScale: !b }); } catch (e) {}
    }

    function cancelarDibujoEnCurso(){
      dibujoEnCurso = null; esperandoSegundoClick = false; inicioClick = null;
      redibujarTodo();
    }

    var gruposFlyout = [
      { boton:document.getElementById('tool-trend'), menu:document.getElementById('lines-flyout') },
      { boton:document.getElementById('tool-fib'), menu:document.getElementById('fib-flyout') },
      { boton:document.getElementById('tool-geometry'), menu:document.getElementById('geometry-flyout') },
      { boton:document.getElementById('tool-text'), menu:document.getElementById('annotations-flyout') },
      { boton:document.getElementById('tool-measure'), menu:document.getElementById('measure-flyout') },
      { boton:document.getElementById('tool-brush'), menu:document.getElementById('brush-flyout') },
      { boton:document.getElementById('tool-arrow_up'), menu:document.getElementById('arrow-marks-flyout') }
    ];
    function cerrarFlyouts(excepto){ gruposFlyout.forEach(function(g){if(g.menu&&g.menu!==excepto)g.menu.classList.remove('show');}); }
    gruposFlyout.forEach(function(g){
      g.boton.addEventListener('click',function(e){e.stopPropagation();var abierto=g.menu.classList.contains('show');cerrarFlyouts(g.menu);g.menu.classList.toggle('show',!abierto);});
      g.menu.querySelectorAll('.tvtool-flyout-item').forEach(function(item){
        item.addEventListener('click',function(e){e.stopPropagation();var tool=item.getAttribute('data-tool');g.menu.classList.remove('show');activarHerramienta(tool);var svg=item.querySelector('svg');if(svg)g.boton.innerHTML=svg.outerHTML+'<span class="tvtool-arrow">▼</span>';});
      });
    });
    window.addEventListener('click',function(){cerrarFlyouts(null);});

    var TOOL_POINTS={
      trend:2,ray:2,extended:2,angle:2,hline:1,hray:1,vline:1,crossline:1,channel:3,
      fib:2,fib_extension:3,fib_channel:3,rectangle:2,ellipse:2,triangle:2,arrow:2,
      text:1,measure:2
    };
    function puntosHerramienta(tool){return TOOL_POINTS[tool]||2;}
    var mantenerHerramienta=false;

    function activarHerramienta(toolName){
      if(dibujoEnCurso&&toolName!==activeTool)cancelarDibujoEnCurso();
      activeTool=toolName;
      document.querySelectorAll('.tvtool').forEach(function(b){
        var t=b.getAttribute('data-tool');
        if(t!=='clear'&&t!=='lock'&&t!=='magnet'&&t!=='keep')b.classList.toggle('active',t===toolName);
      });
      setCursor(toolName==='cross'?'':'cur-dibujar');
    }

    document.querySelectorAll('.tvtool').forEach(function(btn){
      btn.addEventListener('click',function(){
        var tool=btn.getAttribute('data-tool');
        if(tool==='clear'){
          if(elementosDibujados.length&&confirm('¿Deseas limpiar todos los dibujos de este gráfico?')){elementosDibujados=[];seleccionadoId=null;hoverId=null;confirmarCambio();}
          return;
        }
        if(tool==='lock'){
          bloqueado=!bloqueado;btn.style.color=bloqueado?'#3fb950':'#8b949e';btn.title=bloqueado?'Desbloquear dibujos':'Bloquear dibujos';
          if(bloqueado){seleccionadoId=null;hoverId=null;activarHerramienta('cross');redibujarTodo();} return;
        }
        if(tool==='magnet'){
          imanActivo=!imanActivo;btn.classList.toggle('active',imanActivo);btn.title='Magnetismo: '+(imanActivo?'activado':'desactivado');return;
        }
        if(tool==='keep'){
          mantenerHerramienta=!mantenerHerramienta;btn.classList.toggle('active',mantenerHerramienta);btn.title=mantenerHerramienta?'Mantener herramienta activa: sí':'Mantener herramienta activa: no';return;
        }
        if(['tool-trend','tool-fib','tool-geometry','tool-text','tool-measure'].indexOf(btn.id)>=0)return;
        activarHerramienta(tool);
      });
    });

    function posMouse(e){var r=wrapEl.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};}

    function crearDibujoInicial(tool,pt){
      var d={tipo:tool,time1:pt.time,price1:pt.price,time2:pt.time,price2:pt.price};
      if(puntosHerramienta(tool)>=3){d.time3=pt.time;d.price3=pt.price;}
      return d;
    }

    function actualizarDibujoEnCurso(pos,e){
      if(!dibujoEnCurso)return;
      var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
      var n=dibujoEnCurso._puntoActual||2;
      dibujoEnCurso['time'+n]=pt.time;dibujoEnCurso['price'+n]=pt.price;redibujarTodo();
    }

    function finalizarDibujo(valido){
      if(!dibujoEnCurso)return;
      var d=dibujoEnCurso;delete d._puntoActual;
      dibujoEnCurso=null;esperandoSegundoClick=false;inicioClick=null;
      var g=geom(d),largo=(g&&ok(g.x1,g.y1,g.x2,g.y2))?Math.hypot(g.x2-g.x1,g.y2-g.y1):0;
      var suficiente=largo>3&&(puntosHerramienta(d.tipo)<3||ok(g.x3,g.y3));
      if(valido&&suficiente){elementosDibujados.push(d);seleccionadoId=elementosDibujados.length-1;confirmarCambio();}
      else redibujarTodo();
      if(mantenerHerramienta){activarHerramienta(d.tipo);}else activarHerramienta('cross');
    }

    function anclasOriginales(el){
      if(el.tipo==='hline')return{price:el.price};
      if(el.tipo==='vline')return{l:tiempoALogico(el.time)};
      if(el.tipo==='crossline')return{l:tiempoALogico(el.time),price:el.price};
      if(el.tipo==='text')return{l:tiempoALogico(el.time),price:el.price};
      return{l1:tiempoALogico(el.time1),price1:el.price1,l2:tiempoALogico(el.time2),price2:el.price2,l3:el.time3!==undefined?tiempoALogico(el.time3):null,price3:el.price3};
    }

    function aplicarArrastre(pos,e){
      var el=elementosDibujados[arrastre.idx];if(!el)return;var o=arrastre.orig;
      if(arrastre.modo==='move'){
        var l=chart.timeScale().coordinateToLogical(pos.x),p=serie.coordinateToPrice(pos.y);if(l===null||p===null)return;
        var dl=l-arrastre.l0,dp=p-arrastre.p0;
        if(el.tipo==='hline')el.price=o.price+dp;
        else if(el.tipo==='vline')el.time=logicoATiempo(o.l+dl);
        else if(el.tipo==='crossline'){el.time=logicoATiempo(o.l+dl);el.price=o.price+dp;}
        else if(el.tipo==='text'){el.time=logicoATiempo(o.l+dl);el.price=o.price+dp;}
        else {el.time1=logicoATiempo(o.l1+dl);el.price1=o.price1+dp;el.time2=logicoATiempo(o.l2+dl);el.price2=o.price2+dp;if(o.l3!==null){el.time3=logicoATiempo(o.l3+dl);el.price3=o.price3+dp;}}
      }else{
        var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
        var n=arrastre.modo==='p1'?1:(arrastre.modo==='p2'?2:3);
        el['time'+n]=pt.time;el['price'+n]=pt.price;
        if(n===1&&el.tipo==='hline')el.price=pt.price;
        if(n===1&&el.tipo==='vline')el.time=pt.time;
        if(n===1&&el.tipo==='crossline'){el.time=pt.time;el.price=pt.price;}
      }
      redibujarTodo();
    }

    wrapEl.addEventListener('mousedown',function(e){
      if(e.target&&e.target.closest&&e.target.closest('.tv-ui'))return;
      if(e.button!==0||bloqueado||!serie)return;
      var pos=posMouse(e),ap=areaTrazado();if(pos.x>ap.w||pos.y>ap.h)return;

      if(dibujoEnCurso&&esperandoSegundoClick){
        e.preventDefault();e.stopPropagation();bloquearGrafico(true);
        actualizarDibujoEnCurso(pos,e);
        var nActual=dibujoEnCurso._puntoActual||2;
        var total=puntosHerramienta(dibujoEnCurso.tipo);
        if(nActual>=total){finalizarDibujo(true);return;}
        dibujoEnCurso._puntoActual=nActual+1;
        esperandoSegundoClick=false;
        inicioClick={x:pos.x,y:pos.y};
        return;
      }

      if(activeTool!=='cross'){
        e.preventDefault();e.stopPropagation();var pt=puntoDesdeMouse(pos.x,pos.y,magnetEfectivo(e));if(!pt)return;
        if(activeTool==='hline'){elementosDibujados.push({tipo:'hline',price:pt.price});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='hray'){elementosDibujados.push({tipo:'hray',time1:pt.time,price1:pt.price,time2:pt.time,price2:pt.price});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='vline'){elementosDibujados.push({tipo:'vline',time:pt.time});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='crossline'){elementosDibujados.push({tipo:'crossline',time:pt.time,price:pt.price});seleccionadoId=elementosDibujados.length-1;confirmarCambio();if(!mantenerHerramienta)activarHerramienta('cross');}
        else if(activeTool==='text'){
          editarTexto(null,pos,pt);
          if(!mantenerHerramienta)activarHerramienta('cross');
        }else{
          bloquearGrafico(true);dibujoEnCurso=crearDibujoInicial(activeTool,pt);dibujoEnCurso._puntoActual=2;inicioClick={x:pos.x,y:pos.y};esperandoSegundoClick=false;seleccionadoId=null;redibujarTodo();
        }
        return;
      }

      var hit=elementoBajo(pos.x,pos.y);
      if(hit){e.preventDefault();e.stopPropagation();bloquearGrafico(true);seleccionadoId=hit.idx;arrastre={modo:hit.parte==='body'?'move':hit.parte,idx:hit.idx,l0:chart.timeScale().coordinateToLogical(pos.x),p0:serie.coordinateToPrice(pos.y),orig:anclasOriginales(elementosDibujados[hit.idx]),movido:false,x0:pos.x,y0:pos.y};redibujarTodo();return;}
      if(seleccionadoId!==null){seleccionadoId=null;redibujarTodo();}
    },true);

    if(window._tvGlobalMousemove){window.removeEventListener('mousemove',window._tvGlobalMousemove);window.removeEventListener('mouseup',window._tvGlobalMouseup);document.removeEventListener('keydown',window._tvGlobalKeydown);}

    window._tvGlobalMousemove=function(e){
      var pos=posMouse(e);
      if(arrastre){if(!arrastre.movido&&Math.hypot(pos.x-arrastre.x0,pos.y-arrastre.y0)<3)return;arrastre.movido=true;aplicarArrastre(pos,e);return;}
      if(dibujoEnCurso){actualizarDibujoEnCurso(pos,e);return;}
      var nuevoHover=null,cls='',dentro=pos.x>=0&&pos.y>=0&&pos.x<=cssW&&pos.y<=cssH;
      if(dentro&&!bloqueado&&activeTool==='cross'){var ap=areaTrazado();if(pos.x<=ap.w&&pos.y<=ap.h){var h=elementoBajo(pos.x,pos.y);if(h){nuevoHover=h.idx;cls=h.parte==='body'?'cur-mover':'cur-punto';}}}
      if(nuevoHover!==hoverId){hoverId=nuevoHover;redibujarTodo();}setCursor(activeTool!=='cross'?'cur-dibujar':cls);
    };
    window.addEventListener('mousemove',window._tvGlobalMousemove);

    window._tvGlobalMouseup=function(e){
      if(arrastre){var huboCambio=arrastre.movido;arrastre=null;if(huboCambio)confirmarCambio();}
      else if(dibujoEnCurso&&!esperandoSegundoClick){
        var pos=posMouse(e),dist=inicioClick?Math.hypot(pos.x-inicioClick.x,pos.y-inicioClick.y):0;
        if(dist>6){
          actualizarDibujoEnCurso(pos,e);
          var nActual=dibujoEnCurso._puntoActual||2,total=puntosHerramienta(dibujoEnCurso.tipo);
          if(total===2 || nActual>=total){finalizarDibujo(true);}
          else{dibujoEnCurso._puntoActual=nActual+1;esperandoSegundoClick=true;inicioClick={x:pos.x,y:pos.y};}
        } else {esperandoSegundoClick=true;}
      }
      bloquearGrafico(false);
    };
    window.addEventListener('mouseup',window._tvGlobalMouseup);

    window.addEventListener('blur',function(){if(arrastre){var huboCambio=arrastre.movido;arrastre=null;if(huboCambio)confirmarCambio();}bloquearGrafico(false);});

    window._tvGlobalKeydown=function(e){
      var tag=(e.target&&e.target.tagName)||'';if(tag==='INPUT'||tag==='TEXTAREA')return;var k=e.key;
      if(k==='Escape'){if(dibujoEnCurso)cancelarDibujoEnCurso();activarHerramienta('cross');if(seleccionadoId!==null){seleccionadoId=null;redibujarTodo();}return;}
      if((k==='Delete'||k==='Backspace')&&seleccionadoId!==null&&!bloqueado){e.preventDefault();elementosDibujados.splice(seleccionadoId,1);seleccionadoId=null;hoverId=null;confirmarCambio();return;}
      if(e.ctrlKey||e.metaKey){var kl=(k||'').toLowerCase();if(kl==='z'&&!e.shiftKey){e.preventDefault();deshacer();}else if(kl==='y'||(kl==='z'&&e.shiftKey)){e.preventDefault();rehacer();}}
    };
    document.addEventListener('keydown',window._tvGlobalKeydown);

    var dibujosVisibles = true;
    var portapapeles = null;

    var PALETA_DIB = ['#2962ff', '#58a6ff', '#089981', '#3fb950', '#f5c518', '#ff9800', '#f23645', '#a78bfa', '#ffffff'];
    var ANCHOS_DIB = [1, 2, 3, 4];
    var COLOR_DEF = { trend: '#2962ff', ray: '#2962ff', extended: '#2962ff', angle: '#a78bfa', hline: '#f5c518',
      hray: '#f5c518', vline: '#58a6ff', crossline: '#8b949e', channel: '#2962ff', rectangle: '#58a6ff',
      ellipse: '#58a6ff', triangle: '#58a6ff', arrow: '#3fb950', text: '#ffffff', brush: '#ff9800', highlighter: 'rgba(255,235,59,0.35)' };
    var ANCHO_DEF = { hline: 1.5, hray: 1.5, vline: 1.5, crossline: 1, brush: 3, highlighter: 18 };
    var ESTILO_DEF = { hline: 'dash', vline: 'dash', crossline: 'dash' };
    var TIPOS_TRAZO = { trend: 1, ray: 1, extended: 1, angle: 1, hline: 1, hray: 1, vline: 1, crossline: 1, channel: 1, arrow: 1 };
    var TIPOS_ANCHO = { trend: 1, ray: 1, extended: 1, angle: 1, hline: 1, hray: 1, vline: 1, crossline: 1, channel: 1, arrow: 1,
      rectangle: 1, ellipse: 1, triangle: 1, brush: 1, highlighter: 1 };
    var TIPOS_COLOR = { trend: 1, ray: 1, extended: 1, angle: 1, hline: 1, hray: 1, vline: 1, crossline: 1, channel: 1, arrow: 1,
      rectangle: 1, ellipse: 1, triangle: 1, text: 1, brush: 1, highlighter: 1 };

    var estiloUI2 = document.createElement('style');
    estiloUI2.textContent = [
      '.tvtool.on { background: rgba(139,92,246,0.18); color: #a78bfa; }',
      '#tv-stylebar { position: absolute; top: 10px; left: calc(50% + 22px); transform: translateX(-50%); z-index: 30; display: none; align-items: center; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 5px 8px; box-shadow: 0 6px 20px rgba(0,0,0,0.5); user-select: none; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }',
      '#tv-stylebar.show { display: flex; }',
      '#tv-stylebar .sb-bloque { display: flex; align-items: center; gap: 3px; padding-right: 8px; margin-right: 8px; border-right: 1px solid #30363d; }',
      '#tv-stylebar .sb-bloque.ultimo { border-right: none; margin-right: 0; padding-right: 0; }',
      '.sb-color { width: 18px; height: 18px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; padding: 0; }',
      '.sb-color.on { border-color: #ffffff; }',
      '.sb-ancho, .sb-estilo, .sb-btn { background: transparent; border: 1px solid transparent; color: #8b949e; width: 30px; height: 26px; border-radius: 5px; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; }',
      '.sb-ancho.on, .sb-estilo.on { background: rgba(88,166,255,0.18); color: #58a6ff; border-color: rgba(88,166,255,0.3); }',
      '.sb-btn:hover { background: rgba(255,255,255,0.08); color: #ffffff; }',
      '.sb-btn.peligro:hover { color: #f85149; }',
      '.sb-btn svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }',
      '#tv-stylebar input[type=color] { width: 22px; height: 22px; border: none; padding: 0; background: none; cursor: pointer; }',
      '#tv-actions .tvbtn[disabled] { opacity: 0.35; cursor: default; }'
    ].join(' ');
    document.head.appendChild(estiloUI2);

    function valorEfectivo(el, k){
      if (el[k] !== undefined && el[k] !== null) return el[k];
      if (k === 'color') return COLOR_DEF[el.tipo] || '#2962ff';
      if (k === 'ancho') return ANCHO_DEF[el.tipo] || 2;
      return ESTILO_DEF[el.tipo] || 'solid';
    }

    var areaDibEl = document.getElementById('tv-main-canvas-area');
    var barraEl = document.createElement('div');
    barraEl.id = 'tv-stylebar';

    var bloqueColor = document.createElement('div'); bloqueColor.className = 'sb-bloque';
    PALETA_DIB.forEach(function(col){
      var b = document.createElement('button');
      b.className = 'sb-color'; b.title = 'Color'; b.setAttribute('data-color', col); b.style.background = col;
      bloqueColor.appendChild(b);
    });
    var pickerEl = document.createElement('input');
    pickerEl.type = 'color'; pickerEl.title = 'Color personalizado'; pickerEl.value = '#2962ff';
    bloqueColor.appendChild(pickerEl);

    var bloqueAncho = document.createElement('div'); bloqueAncho.className = 'sb-bloque';
    ANCHOS_DIB.forEach(function(a){
      var b = document.createElement('button');
      b.className = 'sb-ancho'; b.title = 'Grosor ' + a + ' px'; b.setAttribute('data-ancho', String(a));
      b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18"><path d="M3 12h18" stroke="currentColor" stroke-width="' + a + '" fill="none"/></svg>';
      bloqueAncho.appendChild(b);
    });

    var bloqueEstilo = document.createElement('div'); bloqueEstilo.className = 'sb-bloque';
    [['solid', '', 'Línea continua'], ['dash', '6 4', 'Línea discontinua'], ['dot', '1.5 3.5', 'Línea punteada']].forEach(function(par){
      var b = document.createElement('button');
      b.className = 'sb-estilo'; b.title = par[2]; b.setAttribute('data-estilo', par[0]);
      b.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18"><path d="M2 12h20" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="' + par[1] + '"/></svg>';
      bloqueEstilo.appendChild(b);
    });

    var bloqueAcc = document.createElement('div'); bloqueAcc.className = 'sb-bloque ultimo';
    var bDup = document.createElement('button');
    bDup.className = 'sb-btn'; bDup.title = 'Duplicar'; bDup.setAttribute('data-accion', 'duplicar');
    bDup.innerHTML = '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/></svg>';
    var bDel = document.createElement('button');
    bDel.className = 'sb-btn peligro'; bDel.title = 'Eliminar'; bDel.setAttribute('data-accion', 'borrar');
    bDel.innerHTML = '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>';
    bloqueAcc.appendChild(bDup); bloqueAcc.appendChild(bDel);

    barraEl.appendChild(bloqueColor); barraEl.appendChild(bloqueAncho);
    barraEl.appendChild(bloqueEstilo); barraEl.appendChild(bloqueAcc);
    areaDibEl.appendChild(barraEl);

    function elementoSeleccionado(){
      return (seleccionadoId !== null && !bloqueado && dibujosVisibles) ? (elementosDibujados[seleccionadoId] || null) : null;
    }

    function refrescarBarra(el){
      if (!el) { barraEl.classList.remove('show'); return; }
      barraEl.classList.add('show');
      var t = el.tipo;
      bloqueColor.style.display = TIPOS_COLOR[t] ? 'flex' : 'none';
      bloqueAncho.style.display = TIPOS_ANCHO[t] ? 'flex' : 'none';
      bloqueEstilo.style.display = TIPOS_TRAZO[t] ? 'flex' : 'none';
      if (TIPOS_COLOR[t]) {
        var col = valorEfectivo(el, 'color');
        bloqueColor.querySelectorAll('.sb-color').forEach(function(b){
          b.classList.toggle('on', b.getAttribute('data-color') === col);
        });
        if (/^#[0-9a-fA-F]{6}$/.test(col)) pickerEl.value = col;
      }
      if (TIPOS_ANCHO[t]) {
        var a = valorEfectivo(el, 'ancho'), mejor = ANCHOS_DIB[0];
        ANCHOS_DIB.forEach(function(w){ if (Math.abs(w - a) < Math.abs(mejor - a)) mejor = w; });
        bloqueAncho.querySelectorAll('.sb-ancho').forEach(function(b){
          b.classList.toggle('on', parseFloat(b.getAttribute('data-ancho')) === mejor);
        });
      }
      if (TIPOS_TRAZO[t]) {
        var est = valorEfectivo(el, 'estilo');
        bloqueEstilo.querySelectorAll('.sb-estilo').forEach(function(b){
          b.classList.toggle('on', b.getAttribute('data-estilo') === est);
        });
      }
    }

    barraEl.addEventListener('click', function(e){
      var btn = e.target.closest ? e.target.closest('button') : null;
      var el = elementoSeleccionado();
      if (!btn || !el) return;
      if (btn.hasAttribute('data-color')) { el.color = btn.getAttribute('data-color'); }
      else if (btn.hasAttribute('data-ancho')) { el.ancho = parseFloat(btn.getAttribute('data-ancho')); }
      else if (btn.hasAttribute('data-estilo')) { el.estilo = btn.getAttribute('data-estilo'); }
      else if (btn.getAttribute('data-accion') === 'borrar') { borrarSeleccionado(); return; }
      else if (btn.getAttribute('data-accion') === 'duplicar') { copiarSeleccionado(); pegar(); return; }
      else return;
      confirmarCambio();
      refrescarBarra(el);
    });
    pickerEl.addEventListener('input', function(){
      var el = elementoSeleccionado();
      if (!el) return;
      el.color = pickerEl.value;
      redibujarTodo();
    });
    pickerEl.addEventListener('change', function(){
      var el = elementoSeleccionado();
      if (!el) return;
      confirmarCambio();
      refrescarBarra(el);
    });

    function borrarSeleccionado(){
      if (seleccionadoId === null || bloqueado) return;
      elementosDibujados.splice(seleccionadoId, 1);
      seleccionadoId = null; hoverId = null;
      confirmarCambio();
    }

    function copiarSeleccionado(){
      var el = elementoSeleccionado();
      if (el) portapapeles = JSON.stringify(el);
    }

    function pegar(){
      if (!portapapeles || bloqueado || !serie) return;
      var el = JSON.parse(portapapeles);
      var clavesT = [], clavesP = [];
      Object.keys(el).forEach(function(k){
        if (/^time[0-9]?$/.test(k) && typeof el[k] === 'number') clavesT.push(k);
        if (/^price[0-9]?$/.test(k) && typeof el[k] === 'number') clavesP.push(k);
      });
      clavesT.forEach(function(k){
        var l = tiempoALogico(el[k]);
        if (l !== null) el[k] = logicoATiempo(l + 4);
      });
      if (clavesP.length) {
        var yRef = yDePrecio(el[clavesP[0]]);
        var pDesp = ok(yRef) ? serie.coordinateToPrice(yRef + 24) : null;
        if (pDesp !== null) {
          var dp = pDesp - el[clavesP[0]];
          clavesP.forEach(function(k){ el[k] = el[k] + dp; });
        }
      }
      elementosDibujados.push(el);
      seleccionadoId = elementosDibujados.length - 1;
      confirmarCambio();
    }

    function botonIcono(interior, titulo, fn){
      var b = document.createElement('button');
      b.className = 'tvbtn icon'; b.title = titulo;
      b.innerHTML = '<svg viewBox="0 0 20 20">' + interior + '</svg>';
      b.addEventListener('click', fn);
      return b;
    }
    var accionesEl = document.getElementById('tv-actions');
    var btnUndo = botonIcono('<path d="M7 5L3.5 8.5 7 12"/><path d="M3.5 8.5H12a4 4 0 0 1 0 8H9"/>', 'Deshacer', function(){ deshacer(); });
    var btnRedo = botonIcono('<path d="M13 5l3.5 3.5L13 12"/><path d="M16.5 8.5H8a4 4 0 0 0 0 8h3"/>', 'Rehacer', function(){ rehacer(); });
    accionesEl.insertBefore(btnRedo, accionesEl.firstChild);
    accionesEl.insertBefore(btnUndo, btnRedo);

    var dibujosVisibles = true;
    var btnOcultar = document.createElement('button');
    btnOcultar.className = 'tvtool';
    var ICONO_OJO = '<svg viewBox="0 0 20 20"><path d="M2 10s3-5.5 8-5.5S18 10 18 10s-3 5.5-8 5.5S2 10 2 10z"/><circle cx="10" cy="10" r="2.4"/></svg>';
    var ICONO_OJO_OFF = '<svg viewBox="0 0 20 20"><path d="M2 10s3-5.5 8-5.5S18 10 18 10s-3 5.5-8 5.5S2 10 2 10z"/><circle cx="10" cy="10" r="2.4"/><path d="M3 3l14 14"/></svg>';
    function refrescarOcultar(){
      btnOcultar.innerHTML = dibujosVisibles ? ICONO_OJO : ICONO_OJO_OFF;
      btnOcultar.title = dibujosVisibles ? 'Ocultar dibujos' : 'Mostrar dibujos';
      btnOcultar.classList.toggle('on', !dibujosVisibles);
    }
    refrescarOcultar();
    var btnLockRef = document.getElementById('tool-lock');
    btnLockRef.parentNode.insertBefore(btnOcultar, btnLockRef);
    btnOcultar.addEventListener('click', function(e){
      e.stopPropagation();
      dibujosVisibles = !dibujosVisibles;
      if (!dibujosVisibles) { cancelarDibujoEnCurso(); activarHerramienta('cross'); seleccionadoId = null; hoverId = null; }
      refrescarOcultar();
      redibujarTodo();
    });

    var pintarOriginal = pintar;
    pintar = function(){
      if (!dibujosVisibles) { ctx.clearRect(0, 0, cssW, cssH); return; }
      pintarOriginal();
    };
    var elementoBajoOriginal = elementoBajo;
    elementoBajo = function(x, y){ return dibujosVisibles ? elementoBajoOriginal(x, y) : null; };
    var activarHerramientaOriginal = activarHerramienta;
    activarHerramienta = function(t){
      if (t !== 'cross' && !dibujosVisibles) { dibujosVisibles = true; refrescarOcultar(); redibujarTodo(); }
      activarHerramientaOriginal(t);
    };

    var vigSel = -2, vigObj = null, vigHist = '';
    function vigilarUI(){
      var el = elementoSeleccionado();
      if (seleccionadoId !== vigSel || el !== vigObj) { vigSel = seleccionadoId; vigObj = el; refrescarBarra(el); }
      var h = posHist + '/' + historial.length;
      if (h !== vigHist) {
        vigHist = h;
        btnUndo.disabled = posHist <= 0;
        btnRedo.disabled = posHist >= historial.length - 1;
      }
      requestAnimationFrame(vigilarUI);
    }
    requestAnimationFrame(vigilarUI);

    document.addEventListener('keydown', function(e){
      var tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (e.ctrlKey || e.metaKey) {
        var kl = (e.key || '').toLowerCase();
        if (kl === 'c') copiarSeleccionado();
        else if (kl === 'v') pegar();
        return;
      }
      if (e.altKey) {
        var mapa = { KeyT: 'trend', KeyH: 'hline', KeyV: 'vline', KeyF: 'fib', KeyB: 'brush' };
        var t = mapa[e.code];
        if (t) {
          e.preventDefault();
          var item = document.querySelector('.tvtool-flyout-item[data-tool="' + t + '"]');
          if (item) item.click(); else activarHerramienta(t);
        }
      }
    });

    var TAMANOS_TXT = [13, 16, 20, 26, 34];
    var editorTexto = null;

    var estiloTxt = document.createElement('style');
    estiloTxt.textContent = [
      '.tv-texto-input { position: absolute; z-index: 40; box-sizing: content-box; background: rgba(13,17,23,0.96); border: 1px dashed #58a6ff; border-radius: 4px; padding: 2px 4px; margin: 0; outline: none; font-family: sans-serif; }',
      '.sb-txt { background: transparent; border: 1px solid transparent; color: #8b949e; min-width: 28px; height: 26px; border-radius: 5px; cursor: pointer; padding: 0 4px; font-family: inherit; font-size: 12px; }',
      '.sb-txt:hover { background: rgba(255,255,255,0.08); color: #ffffff; }',
      '.sb-txt.on { background: rgba(88,166,255,0.18); color: #58a6ff; border-color: rgba(88,166,255,0.3); }'
    ].join(' ');
    document.head.appendChild(estiloTxt);

    function fuenteTexto(el){ return (el.negrita ? 'bold ' : '') + (el.tamano || 13) + 'px sans-serif'; }

    function cerrarEditorTexto(){
      if (editorTexto && editorTexto.parentNode) editorTexto.parentNode.removeChild(editorTexto);
      editorTexto = null;
    }

    function editarTexto(idx, pos, pt){
      cerrarEditorTexto();
      var el = (idx !== null) ? elementosDibujados[idx] : null;
      var sz = el ? (el.tamano || 13) : 13;
      var inp = document.createElement('input');
      inp.type = 'text';
      inp.className = 'tv-texto-input tv-ui';
      inp.value = el ? (el.texto || '') : '';
      inp.placeholder = 'Escribe y pulsa Enter';
      inp.style.fontSize = sz + 'px';
      if (el && el.negrita) inp.style.fontWeight = 'bold';
      inp.style.color = el ? (el.color || '#ffffff') : '#ffffff';
      inp.style.left = Math.round(pos.x - 5) + 'px';
      inp.style.top = Math.round(pos.y - sz - 6) + 'px';
      function ajustar(){
        ctx.font = (el && el.negrita ? 'bold ' : '') + sz + 'px sans-serif';
        inp.style.width = Math.max(140, Math.ceil(ctx.measureText(inp.value || inp.placeholder).width) + 16) + 'px';
      }
      ajustar();
      inp.addEventListener('input', ajustar);
      wrapEl.appendChild(inp);
      editorTexto = inp;
      var terminado = false;
      function cerrar(guardar){
        if (terminado) return;
        terminado = true;
        var valor = inp.value.trim();
        if (inp.parentNode) inp.parentNode.removeChild(inp);
        if (editorTexto === inp) editorTexto = null;
        if (!guardar || !valor) { redibujarTodo(); return; }
        if (el) {
          if (el.texto !== valor) { el.texto = valor; confirmarCambio(); } else { redibujarTodo(); }
        } else if (pt) {
          elementosDibujados.push({ tipo: 'text', time: pt.time, price: pt.price, texto: valor });
          seleccionadoId = elementosDibujados.length - 1;
          confirmarCambio();
        }
      }
      inp.addEventListener('keydown', function(e){
        e.stopPropagation();
        if (e.key === 'Enter') { e.preventDefault(); cerrar(true); }
        else if (e.key === 'Escape') { cerrar(false); }
      });
      inp.addEventListener('blur', function(){ cerrar(true); });
      setTimeout(function(){ inp.focus(); inp.select(); }, 0);
    }

    wrapEl.addEventListener('dblclick', function(e){
      if (bloqueado || activeTool !== 'cross') return;
      if (e.target && e.target.closest && e.target.closest('.tv-ui')) return;
      var pos = posMouse(e);
      var hit = elementoBajo(pos.x, pos.y);
      if (hit && elementosDibujados[hit.idx].tipo === 'text') {
        e.preventDefault(); e.stopPropagation();
        var g = geom(elementosDibujados[hit.idx]);
        seleccionadoId = hit.idx;
        redibujarTodo();
        editarTexto(hit.idx, { x: g.x, y: g.y });
      }
    }, true);

    var bloqueTexto = document.createElement('div');
    bloqueTexto.className = 'sb-bloque';
    bloqueTexto.style.display = 'none';
    TAMANOS_TXT.forEach(function(t){
      var b = document.createElement('button');
      b.className = 'sb-txt'; b.title = 'Tamaño ' + t + ' px'; b.setAttribute('data-tamano', String(t)); b.textContent = String(t);
      bloqueTexto.appendChild(b);
    });
    var btnNegrita = document.createElement('button');
    btnNegrita.className = 'sb-txt'; btnNegrita.title = 'Negrita'; btnNegrita.setAttribute('data-negrita', '1');
    btnNegrita.innerHTML = '<b>B</b>';
    bloqueTexto.appendChild(btnNegrita);
    barraEl.insertBefore(bloqueTexto, bloqueAcc);

    bloqueTexto.addEventListener('click', function(e){
      var btn = e.target.closest ? e.target.closest('button') : null;
      var el = elementoSeleccionado();
      if (!btn || !el || el.tipo !== 'text') return;
      if (btn.hasAttribute('data-tamano')) { el.tamano = parseInt(btn.getAttribute('data-tamano'), 10); }
      else if (btn.hasAttribute('data-negrita')) { el.negrita = !el.negrita; }
      else return;
      confirmarCambio();
      refrescarBarra(el);
    });

    var refrescarBarraBase = refrescarBarra;
    refrescarBarra = function(el){
      refrescarBarraBase(el);
      var esTxt = !!(el && el.tipo === 'text');
      bloqueTexto.style.display = esTxt ? 'flex' : 'none';
      if (esTxt) {
        var t = el.tamano || 13, mejor = TAMANOS_TXT[0];
        TAMANOS_TXT.forEach(function(w){ if (Math.abs(w - t) < Math.abs(mejor - t)) mejor = w; });
        bloqueTexto.querySelectorAll('.sb-txt[data-tamano]').forEach(function(b){
          b.classList.toggle('on', parseInt(b.getAttribute('data-tamano'), 10) === mejor);
        });
        btnNegrita.classList.toggle('on', !!el.negrita);
      }
    };

    var estiloPincel = { color: COLOR_DEF.brush, ancho: ANCHO_DEF.brush };
    var trazoPincel = null;
    var cachePincel = new WeakMap();

    function firmaPincel(){
      var n = datosActuales.length;
      return n ? (n + ':' + datosActuales[0].time + ':' + datosActuales[n - 1].time + ':' + firmaVista()) : '';
    }

    function puntosPantalla(el){
      var firma = firmaPincel();
      var c = cachePincel.get(el);
      if (c && c.ref === el.puntos && c.firma === firma) return c.pts;
      var out = [];
      (el.puntos || []).forEach(function(q){
        var x = xDeTiempo(q[0]), y = yDePrecio(q[1]);
        if (ok(x, y)) out.push({ x: x, y: y });
      });
      cachePincel.set(el, { ref: el.puntos, firma: firma, pts: out });
      return out;
    }

    function trazarSuave(c, pts, col, ancho){
      var v = pts.filter(function(q){ return ok(q.x, q.y); });
      if (!v.length) return;
      c.save();
      c.strokeStyle = col; c.fillStyle = col; c.lineWidth = ancho;
      c.lineCap = 'round'; c.lineJoin = 'round';
      var punto = v.length === 1 || (v.length === 2 && v[0].x === v[1].x && v[0].y === v[1].y);
      if (punto) {
        c.beginPath(); c.arc(v[0].x, v[0].y, ancho / 2, 0, 2 * Math.PI); c.fill();
      } else {
        c.beginPath(); c.moveTo(v[0].x, v[0].y);
        for (var i = 1; i < v.length - 1; i++) {
          var mx = (v[i].x + v[i + 1].x) / 2, my = (v[i].y + v[i + 1].y) / 2;
          c.quadraticCurveTo(v[i].x, v[i].y, mx, my);
        }
        c.lineTo(v[v.length - 1].x, v[v.length - 1].y);
        c.stroke();
      }
      c.restore();
    }

    function dibujarPincel(c, el, sel, hov){
      var v = puntosPantalla(el);
      if (!v.length) return;
      var col = el.color || COLOR_DEF.brush, w = el.ancho || ANCHO_DEF.brush;
      if (sel) trazarSuave(c, v, 'rgba(88,166,255,0.35)', w + 6);
      trazarSuave(c, v, col, w + ((hov && !sel) ? 1 : 0));
    }

    function hitPincel(el, x, y){
      var v = puntosPantalla(el);
      if (!v.length) return false;
      var tol = Math.max(6, (el.ancho || ANCHO_DEF.brush) / 2 + 4);
      if (v.length === 1) return Math.hypot(x - v[0].x, y - v[0].y) <= tol;
      for (var i = 1; i < v.length; i++) {
        if (distSeg(x, y, v[i - 1].x, v[i - 1].y, v[i].x, v[i].y) <= tol) return true;
      }
      return false;
    }

    var dibujarElementoBase = dibujarElemento;
    dibujarElemento = function(c, el, sel, hov){
      if (el.tipo === 'brush') { dibujarPincel(c, el, sel, hov); return; }
      dibujarElementoBase(c, el, sel, hov);
    };

    var hitTestBase = hitTest;
    hitTest = function(el, x, y, sel){
      if (el.tipo === 'brush') return hitPincel(el, x, y) ? 'body' : null;
      return hitTestBase(el, x, y, sel);
    };

    var anclasOriginalesBase = anclasOriginales;
    anclasOriginales = function(el){
      if (el.tipo === 'brush') {
        return { pts: el.puntos.map(function(q){ return [tiempoALogico(q[0]), q[1]]; }) };
      }
      return anclasOriginalesBase(el);
    };

    var aplicarArrastreBase = aplicarArrastre;
    aplicarArrastre = function(pos, e){
      var el = arrastre ? elementosDibujados[arrastre.idx] : null;
      if (el && el.tipo === 'brush' && arrastre.modo === 'move') {
        var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
        if (l === null || p === null) return;
        var dl = l - arrastre.l0, dp = p - arrastre.p0;
        el.puntos = arrastre.orig.pts.map(function(q){
          return [Math.round(logicoATiempo(q[0] + dl)), q[1] + dp];
        });
        redibujarTodo();
        return;
      }
      aplicarArrastreBase(pos, e);
    };

    var pegarBase = pegar;
    pegar = function(){
      if (portapapeles && !bloqueado && serie) {
        var el0 = JSON.parse(portapapeles);
        if (el0.tipo === 'brush' && el0.puntos && el0.puntos.length) {
          var yRef = yDePrecio(el0.puntos[0][1]);
          var pDesp = ok(yRef) ? serie.coordinateToPrice(yRef + 24) : null;
          var dp0 = (pDesp !== null) ? (pDesp - el0.puntos[0][1]) : 0;
          el0.puntos = el0.puntos.map(function(q){
            var l = tiempoALogico(q[0]);
            return [l === null ? q[0] : Math.round(logicoATiempo(l + 4)), q[1] + dp0];
          });
          elementosDibujados.push(el0);
          seleccionadoId = elementosDibujados.length - 1;
          confirmarCambio();
          return;
        }
      }
      pegarBase();
    };

    var confirmarCambioBase = confirmarCambio;
    confirmarCambio = function(){
      var s = (seleccionadoId !== null) ? elementosDibujados[seleccionadoId] : null;
      if (s && s.tipo === 'brush') {
        if (s.color) estiloPincel.color = s.color;
        if (s.ancho) estiloPincel.ancho = s.ancho;
      }
      confirmarCambioBase();
    };

    var pintarPrevioPincel = pintar;
    pintar = function(){
      pintarPrevioPincel();
      if (!trazoPincel || !dibujosVisibles || !serie) return;
      var ap = areaTrazado(), ts = chart.timeScale();
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 0, ap.w, ap.h); ctx.clip();
      trazarSuave(ctx, trazoPincel.pts.map(function(q){
        return { x: ts.logicalToCoordinate(q.l), y: yDePrecio(q.p) };
      }), trazoPincel.color, trazoPincel.ancho);
      ctx.restore();
    };

    function finalizarTrazo(){
      if (!trazoPincel) return;
      var t = trazoPincel;
      trazoPincel = null;
      bloquearGrafico(false);
      var puntos = [];
      t.pts.forEach(function(q){
        var tm = logicoATiempo(q.l);
        if (tm !== null) puntos.push([Math.round(tm), Math.round(q.p * 1e8) / 1e8]);
      });
      if (!puntos.length) { redibujarTodo(); return; }
      if (puntos.length === 1) puntos.push([puntos[0][0], puntos[0][1]]);
      elementosDibujados.push({ tipo: 'brush', puntos: puntos, color: t.color, ancho: t.ancho });
      seleccionadoId = elementosDibujados.length - 1;
      confirmarCambio();
      activarHerramienta(mantenerHerramienta ? 'brush' : 'cross');
    }

    function sumarPuntoTrazo(pos){
      var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
      if (l === null || p === null) return;
      var u = trazoPincel.ultimoPx;
      if (u && Math.hypot(pos.x - u.x, pos.y - u.y) < 2) return;
      trazoPincel.ultimoPx = { x: pos.x, y: pos.y };
      trazoPincel.pts.push({ l: l, p: p });
      redibujarTodo();
    }

    window.addEventListener('mousedown', function(e){
      if (activeTool !== 'brush' || e.button !== 0 || bloqueado || !serie || !datosActuales.length) return;
      if (!wrapEl.contains(e.target)) return;
      if (e.target.closest && e.target.closest('.tv-ui')) return;
      var pos = posMouse(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      e.preventDefault(); e.stopPropagation();
      bloquearGrafico(true);
      seleccionadoId = null; hoverId = null;
      trazoPincel = { pts: [], color: estiloPincel.color, ancho: estiloPincel.ancho, ultimoPx: null };
      sumarPuntoTrazo(pos);
    }, true);

    window.addEventListener('mousemove', function(e){
      if (!trazoPincel) return;
      if (activeTool !== 'brush') { trazoPincel = null; bloquearGrafico(false); redibujarTodo(); return; }
      if (!(e.buttons & 1)) { finalizarTrazo(); return; }
      var pos = posMouse(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      sumarPuntoTrazo(pos);
    });

    window.addEventListener('mouseup', function(){ finalizarTrazo(); });

    var estiloResaltador = { color: COLOR_DEF.highlighter, ancho: ANCHO_DEF.highlighter };
    var trazoResaltador = null;

    function dibujarResaltador(c, el, sel, hov){
      var v = puntosPantalla(el);
      if (!v.length) return;
      var w = el.ancho || ANCHO_DEF.highlighter;
      c.save();
      c.globalCompositeOperation = 'multiply';
      c.globalAlpha = sel ? 0.55 : 0.35;
      c.strokeStyle = el.color || COLOR_DEF.highlighter;
      c.lineWidth = w + ((hov && !sel) ? 2 : 0);
      c.lineCap = 'round'; c.lineJoin = 'round';
      c.beginPath();
      v.forEach(function(p, i){ i === 0 ? c.moveTo(p.x, p.y) : c.lineTo(p.x, p.y); });
      c.stroke();
      if (sel) {
        c.globalCompositeOperation = 'source-over';
        c.globalAlpha = 1;
        c.strokeStyle = 'rgba(88,166,255,0.5)';
        c.lineWidth = w + 8; c.setLineDash([6, 4]);
        c.beginPath();
        v.forEach(function(p, i){ i === 0 ? c.moveTo(p.x, p.y) : c.lineTo(p.x, p.y); });
        c.stroke();
      }
      c.restore();
    }

    var dibujarElementoBase2 = dibujarElemento;
    dibujarElemento = function(c, el, sel, hov){
      if (el.tipo === 'highlighter') { dibujarResaltador(c, el, sel, hov); return; }
      dibujarElementoBase2(c, el, sel, hov);
    };

    var hitTestBase2 = hitTest;
    hitTest = function(el, x, y, sel){
      if (el.tipo === 'highlighter') return hitPincel(el, x, y) ? 'body' : null;
      return hitTestBase2(el, x, y, sel);
    };

    var anclasOriginalesBase2 = anclasOriginales;
    anclasOriginales = function(el){
      if (el.tipo === 'highlighter') return { pts: el.puntos.map(function(q){ return [tiempoALogico(q[0]), q[1]]; }) };
      return anclasOriginalesBase2(el);
    };

    var aplicarArrastreBase2 = aplicarArrastre;
    aplicarArrastre = function(pos, e){
      var el = arrastre ? elementosDibujados[arrastre.idx] : null;
      if (el && el.tipo === 'highlighter' && arrastre.modo === 'move') {
        var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
        if (l === null || p === null) return;
        var dl = l - arrastre.l0, dp = p - arrastre.p0;
        el.puntos = arrastre.orig.pts.map(function(q){ return [Math.round(logicoATiempo(q[0] + dl)), q[1] + dp]; });
        redibujarTodo(); return;
      }
      aplicarArrastreBase2(pos, e);
    };

    window.addEventListener('mousedown', function(e){
      if (activeTool !== 'highlighter' || e.button !== 0 || bloqueado || !serie || !datosActuales.length) return;
      if (!wrapEl.contains(e.target)) return;
      if (e.target.closest && e.target.closest('.tv-ui')) return;
      var pos = posMouse(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      e.preventDefault(); e.stopPropagation();
      bloquearGrafico(true);
      seleccionadoId = null; hoverId = null;
      trazoResaltador = { pts: [], color: estiloResaltador.color, ancho: estiloResaltador.ancho, ultimoPx: null };
      var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
      if (l !== null && p !== null) trazoResaltador.pts.push({ l: l, p: p });
    }, true);

    window.addEventListener('mousemove', function(e){
      if (!trazoResaltador) return;
      if (activeTool !== 'highlighter') { trazoResaltador = null; bloquearGrafico(false); redibujarTodo(); return; }
      if (!(e.buttons & 1)) { finalizarResaltador(); return; }
      var pos = posMouse(e), ap = areaTrazado();
      if (pos.x < 0 || pos.y < 0 || pos.x > ap.w || pos.y > ap.h) return;
      var u = trazoResaltador.ultimoPx;
      if (u && Math.hypot(pos.x - u.x, pos.y - u.y) < 3) return;
      trazoResaltador.ultimoPx = { x: pos.x, y: pos.y };
      var l = chart.timeScale().coordinateToLogical(pos.x), p = serie.coordinateToPrice(pos.y);
      if (l !== null && p !== null) { trazoResaltador.pts.push({ l: l, p: p }); redibujarTodo(); }
    });

    function finalizarResaltador(){
      if (!trazoResaltador) return;
      var t = trazoResaltador; trazoResaltador = null;
      bloquearGrafico(false);
      var puntos = t.pts.map(function(q){ return [Math.round(logicoATiempo(q.l)), Math.round(q.p * 1e8) / 1e8]; });
      if (!puntos.length) { redibujarTodo(); return; }
      if (puntos.length === 1) puntos.push([puntos[0][0], puntos[0][1]]);
      elementosDibujados.push({ tipo: 'highlighter', puntos: puntos, color: t.color, ancho: t.ancho });
      seleccionadoId = elementosDibujados.length - 1;
      confirmarCambio();
      activarHerramienta(mantenerHerramienta ? 'highlighter' : 'cross');
    }

    window.addEventListener('mouseup', function(){ finalizarResaltador(); });

    var ARROW_CFG = {
      arrow_up:    { color: '#3fb950', label: '▲' },
      arrow_down:  { color: '#f85149', label: '▼' },
      arrow_left:  { color: '#58a6ff', label: '◄' },
      arrow_right: { color: '#ff9800', label: '►' }
    };
    Object.keys(ARROW_CFG).forEach(function(t){
      COLOR_DEF[t] = ARROW_CFG[t].color;
      ANCHO_DEF[t] = 14;
      TIPOS_COLOR[t] = 1;
    });

    var ARROW_DIRS = {
      arrow_up:    function(c, x, y, r){ c.moveTo(x, y - r); c.lineTo(x + r * 0.75, y + r * 0.6); c.lineTo(x - r * 0.75, y + r * 0.6); c.closePath(); },
      arrow_down:  function(c, x, y, r){ c.moveTo(x, y + r); c.lineTo(x + r * 0.75, y - r * 0.6); c.lineTo(x - r * 0.75, y - r * 0.6); c.closePath(); },
      arrow_left:  function(c, x, y, r){ c.moveTo(x - r, y); c.lineTo(x + r * 0.6, y - r * 0.75); c.lineTo(x + r * 0.6, y + r * 0.75); c.closePath(); },
      arrow_right: function(c, x, y, r){ c.moveTo(x + r, y); c.lineTo(x - r * 0.6, y - r * 0.75); c.lineTo(x - r * 0.6, y + r * 0.75); c.closePath(); }
    };

    function coordFlecha(el){
      var x = xDeTiempo(el.time1), y = yDePrecio(el.price1);
      return ok(x, y) ? { x: x, y: y } : null;
    }

    function dibujarFlecha(c, el, sel, hov){
      var g = coordFlecha(el); if (!g) return;
      var cfg = ARROW_CFG[el.tipo], col = el.color || cfg.color;
      var r = (el.ancho || 14) + (hov && !sel ? 2 : 0);
      c.save();
      c.beginPath();
      ARROW_DIRS[el.tipo](c, g.x, g.y, r);
      c.fillStyle = col;
      c.globalAlpha = sel ? 1 : 0.85;
      c.fill();
      if (sel) {
        c.strokeStyle = '#ffffff'; c.lineWidth = 1.5; c.globalAlpha = 0.9; c.stroke();
        dibujarHandle(c, g.x, g.y, col);
      }
      c.restore();
      badgePrecio(c, g.y, el.price1, col, '#fff', areaTrazado());
    }

    function hitFlecha(el, x, y){
      var g = coordFlecha(el); if (!g) return false;
      var r = (el.ancho || 14) + 6;
      return Math.hypot(x - g.x, y - g.y) <= r;
    }

    var dibujarElementoBase3 = dibujarElemento;
    dibujarElemento = function(c, el, sel, hov){
      if (ARROW_CFG[el.tipo]) { dibujarFlecha(c, el, sel, hov); return; }
      dibujarElementoBase3(c, el, sel, hov);
    };

    var hitTestBase3 = hitTest;
    hitTest = function(el, x, y, sel){
      if (ARROW_CFG[el.tipo]) return hitFlecha(el, x, y) ? 'body' : null;
      return hitTestBase3(el, x, y, sel);
    };

    // Funciones matemáticas para indicadores técnicos
    function calcularSMA(datos, periodo){
      var out = [];
      for (var i = periodo - 1; i < datos.length; i++){
        var suma = 0;
        for (var j = i - periodo + 1; j <= i; j++){ suma += datos[j].close; }
        out.push({ time: datos[i].time, value: suma / periodo });
      }
      return out;
    }

    function calcularEMA(datos, periodo){
      var out = [];
      var multiplicador = 2 / (periodo + 1);
      var emaPrevio = 0;
      for (var i = 0; i < datos.length; i++){
        if (i < periodo - 1) continue;
        if (i === periodo - 1) {
          var suma = 0;
          for (var j = 0; j <= i; j++) suma += datos[j].close;
          emaPrevio = suma / periodo;
          out.push({ time: datos[i].time, value: emaPrevio });
        } else {
          emaPrevio = (datos[i].close - emaPrevio) * multiplicador + emaPrevio;
          out.push({ time: datos[i].time, value: emaPrevio });
        }
      }
      return out;
    }

    function calcularBollinger(datos, periodo, desviaciones){
      var sma = calcularSMA(datos, periodo);
      var superiores = [], inferiores = [], medias = [];
      for (var i = 0; i < sma.length; i++){
        var idxDatos = i + periodo - 1;
        var sumaCuadrados = 0;
        var mediaVal = sma[i].value;
        for (var j = idxDatos - periodo + 1; j <= idxDatos; j++){
          var diff = datos[j].close - mediaVal;
          sumaCuadrados += diff * diff;
        }
        var desviacionEst = Math.sqrt(sumaCuadrados / periodo);
        var tiempo = sma[i].time;
        medias.push({ time: tiempo, value: mediaVal });
        superiores.push({ time: tiempo, value: mediaVal + (desviaciones * desviacionEst) });
        inferiores.push({ time: tiempo, value: mediaVal - (desviaciones * desviacionEst) });
      }
      return { medias: medias, superiores: superiores, inferiores: inferiores };
    }

    function rsiDesde(ganancia, perdida){
      if (perdida === 0) return ganancia === 0 ? 50 : 100;
      return 100 - (100 / (1 + ganancia / perdida));
    }

    function calcularRSI(datos, periodo){
      var out = [];
      if (datos.length <= periodo) return out;
      for (var k = 0; k < periodo; k++){ out.push({ time: datos[k].time }); }
      var ganancias = 0, perdidas = 0;
      for (var i = 1; i <= periodo; i++){
        var cambio = datos[i].close - datos[i-1].close;
        if (cambio >= 0) ganancias += cambio;
        else perdidas -= cambio;
      }
      var mediaGanancia = ganancias / periodo;
      var mediaPerdida = perdidas / periodo;
      out.push({ time: datos[periodo].time, value: rsiDesde(mediaGanancia, mediaPerdida) });
      for (var n = periodo + 1; n < datos.length; n++){
        var cam = datos[n].close - datos[n-1].close;
        var g = cam >= 0 ? cam : 0;
        var p = cam < 0 ? -cam : 0;
        mediaGanancia = (mediaGanancia * (periodo - 1) + g) / periodo;
        mediaPerdida = (mediaPerdida * (periodo - 1) + p) / periodo;
        out.push({ time: datos[n].time, value: rsiDesde(mediaGanancia, mediaPerdida) });
      }
      return out;
    }

    function calcularATR(datos, periodo){
      var out = [];
      if (datos.length <= periodo) return out;
      for (var i = 0; i < periodo; i++){ out.push({ time: datos[i].time }); }
      var trs = [];
      for (var i = 0; i < datos.length; i++){
        var d = datos[i];
        var tr = (i === 0) ? (d.high - d.low) : Math.max(d.high - d.low, Math.abs(d.high - datos[i-1].close), Math.abs(d.low - datos[i-1].close));
        trs.push(tr);
      }
      var atrPrev = 0;
      for (var i = 1; i <= periodo; i++){ atrPrev += trs[i]; }
      atrPrev /= periodo;
      out.push({ time: datos[periodo].time, value: atrPrev });
      for (var i = periodo + 1; i < datos.length; i++){
        atrPrev = (atrPrev * (periodo - 1) + trs[i]) / periodo;
        out.push({ time: datos[i].time, value: atrPrev });
      }
      return out;
    }

    function calcularMACD(datos, rapida, lenta, senal){
      var emaR = calcularEMA(datos, rapida);
      var emaL = calcularEMA(datos, lenta);
      var macdLine = [];
      var mapL = {};
      emaL.forEach(function(item){ mapL[item.time] = item.value; });
      emaR.forEach(function(item){
        if (mapL[item.time] !== undefined){
          macdLine.push({ time: item.time, value: item.value - mapL[item.time] });
        }
      });
      var mult = 2 / (senal + 1);
      var signalLine = [];
      var emaVal = 0;
      for (var i = 0; i < macdLine.length; i++){
        if (i < senal - 1) continue;
        if (i === senal - 1) {
          var suma = 0;
          for (var j = 0; j <= i; j++) suma += macdLine[j].value;
          emaVal = suma / senal;
          signalLine.push({ time: macdLine[i].time, value: emaVal });
        } else {
          emaVal = (macdLine[i].value - emaVal) * mult + emaVal;
          signalLine.push({ time: macdLine[i].time, value: emaVal });
        }
      }
      return { macd: macdLine, signal: signalLine };
    }

    function calcularEstocastico(datos, periodo){
      var kLines = [];
      for (var i = periodo - 1; i < datos.length; i++){
        var minL = datos[i].low, maxH = datos[i].high;
        for (var j = i - periodo + 1; j <= i; j++){
          if (datos[j].low < minL) minL = datos[j].low;
          if (datos[j].high > maxH) maxH = datos[j].high;
        }
        var val = (maxH - minL === 0) ? 50 : ((datos[i].close - minL) / (maxH - minL)) * 100;
        kLines.push({ time: datos[i].time, value: val });
      }
      return kLines;
    }

    function calcularParabolicSAR(datos){
      var out = [];
      if (datos.length < 3) return out;
      var af = 0.02, maxAf = 0.2;
      var longPos = datos[1].close > datos[0].close;
      var sar = longPos ? datos[0].low : datos[0].high;
      var ep = longPos ? datos[0].high : datos[0].low;
      for (var i = 2; i < datos.length; i++){
        sar = sar + af * (ep - sar);
        if (longPos) {
          if (datos[i].low < sar) { longPos = false; sar = ep; ep = datos[i].low; af = 0.02; }
          else {
            if (datos[i].high > ep) { ep = datos[i].high; af = Math.min(af + 0.02, maxAf); }
            if (datos[i-1].low < sar) sar = datos[i-1].low;
            if (datos[i-2].low < sar) sar = datos[i-2].low;
          }
        } else {
          if (datos[i].high > sar) { longPos = true; sar = ep; ep = datos[i].high; af = 0.02; }
          else {
            if (datos[i].low < ep) { ep = datos[i].low; af = Math.min(af + 0.02, maxAf); }
            if (datos[i-1].high > sar) sar = datos[i-1].high;
            if (datos[i-2].high > sar) sar = datos[i-2].high;
          }
        }
        out.push({ time: datos[i].time, value: sar });
      }
      return out;
    }

    function inicializarRSIChart(){
      if (chartRsi) return;
      var rsiEl = document.getElementById('rsi-container');
      rsiEl.style.display = 'block';
      chartRsi = LightweightCharts.createChart(rsiEl, {
        autoSize: true,
        layout: { background: { color: '#0d1117' }, textColor: '#d1d4dc', fontSize: 11 },
        grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
        timeScale: { visible: false },
        rightPriceScale: { borderColor: '#30363d', minimumWidth: 72, scaleMargins: { top: 0.1, bottom: 0.1 } },
        handleScroll: false,
        handleScale: false
      });
      serieRsi = chartRsi.addLineSeries({
        color: '#a78bfa', lineWidth: 2,
        priceFormat: { type: 'price', precision: 2, minMove: 0.01 }
      });
      serieRsi.createPriceLine({ price: 70, color: '#8b949e', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '' });
      serieRsi.createPriceLine({ price: 30, color: '#8b949e', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '' });
    }

    function actualizarIndicadoresActivos(){
      if (indicadores.sma20) {
        if (!seriesInd.sma20) seriesInd.sma20 = chart.addLineSeries({ color: '#f5c518', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.sma20.setData(calcularSMA(datosActuales, 20));
      } else if (seriesInd.sma20) {
        chart.removeSeries(seriesInd.sma20); seriesInd.sma20 = null;
      }

      if (indicadores.sma50) {
        if (!seriesInd.sma50) seriesInd.sma50 = chart.addLineSeries({ color: '#3399ff', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.sma50.setData(calcularSMA(datosActuales, 50));
      } else if (seriesInd.sma50) {
        chart.removeSeries(seriesInd.sma50); seriesInd.sma50 = null;
      }

      if (indicadores.sma200) {
        if (!seriesInd.sma200) seriesInd.sma200 = chart.addLineSeries({ color: '#a78bfa', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.sma200.setData(calcularSMA(datosActuales, 200));
      } else if (seriesInd.sma200) {
        chart.removeSeries(seriesInd.sma200); seriesInd.sma200 = null;
      }

      if (indicadores.ema20) {
        if (!seriesInd.ema20) seriesInd.ema20 = chart.addLineSeries({ color: '#ff6600', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.ema20.setData(calcularEMA(datosActuales, 20));
      } else if (seriesInd.ema20) {
        chart.removeSeries(seriesInd.ema20); seriesInd.ema20 = null;
      }

      if (indicadores.ema50) {
        if (!seriesInd.ema50) seriesInd.ema50 = chart.addLineSeries({ color: '#e056fd', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.ema50.setData(calcularEMA(datosActuales, 50));
      } else if (seriesInd.ema50) {
        chart.removeSeries(seriesInd.ema50); seriesInd.ema50 = null;
      }

      if (indicadores.bollinger) {
        var bb = calcularBollinger(datosActuales, 20, 2);
        if (!seriesInd.bolsuper) {
          seriesInd.bolsuper = chart.addLineSeries({ color: 'rgba(41, 98, 255, 0.7)', lineWidth: 1, priceLineVisible: false, priceFormat: PF });
          seriesInd.bolmedia = chart.addLineSeries({ color: 'rgba(255, 152, 0, 0.7)', lineWidth: 1, priceLineVisible: false, priceFormat: PF });
          seriesInd.bolinf = chart.addLineSeries({ color: 'rgba(41, 98, 255, 0.7)', lineWidth: 1, priceLineVisible: false, priceFormat: PF });
        }
        seriesInd.bolsuper.setData(bb.superiores);
        seriesInd.bolmedia.setData(bb.medias);
        seriesInd.bolinf.setData(bb.inferiores);
      } else if (seriesInd.bolsuper) {
        chart.removeSeries(seriesInd.bolsuper); seriesInd.bolsuper = null;
        chart.removeSeries(seriesInd.bolmedia); seriesInd.bolmedia = null;
        chart.removeSeries(seriesInd.bolinf); seriesInd.bolinf = null;
      }

      if (indicadores.rsi) {
        inicializarRSIChart();
        if (serieRsi) {
          serieRsi.setData(calcularRSI(datosActuales, 14));
          var rango = chart.timeScale().getVisibleLogicalRange();
          if (rango && chartRsi) chartRsi.timeScale().setVisibleLogicalRange(rango);
        }
      } else {
        var rsiEl = document.getElementById('rsi-container');
        rsiEl.style.display = 'none';
        if (chartRsi) { chartRsi.remove(); chartRsi = null; serieRsi = null; }
      }

      if (indicadores.atr) {
        if (!seriesInd.atr) seriesInd.atr = chart.addLineSeries({ color: '#ff9800', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.atr.setData(calcularATR(datosActuales, 14));
      } else if (seriesInd.atr) {
        chart.removeSeries(seriesInd.atr); seriesInd.atr = null;
      }

      if (indicadores.macd) {
        var mc = calcularMACD(datosActuales, 12, 26, 9);
        if (!seriesInd.macdLine) {
          seriesInd.macdLine = chart.addLineSeries({ color: '#2962ff', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
          seriesInd.macdSignal = chart.addLineSeries({ color: '#ff9800', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        }
        seriesInd.macdLine.setData(mc.macd);
        seriesInd.macdSignal.setData(mc.signal);
      } else if (seriesInd.macdLine) {
        chart.removeSeries(seriesInd.macdLine); seriesInd.macdLine = null;
        chart.removeSeries(seriesInd.macdSignal); seriesInd.macdSignal = null;
      }

      if (indicadores.stochastic) {
        if (!seriesInd.stoch) seriesInd.stoch = chart.addLineSeries({ color: '#3fb950', lineWidth: 2, priceLineVisible: false, priceFormat: PF });
        seriesInd.stoch.setData(calcularEstocastico(datosActuales, 14));
      } else if (seriesInd.stoch) {
        chart.removeSeries(seriesInd.stoch); seriesInd.stoch = null;
      }

      if (indicadores.parabolic) {
        if (!seriesInd.sar) seriesInd.sar = chart.addLineSeries({ color: '#f85149', lineWidth: 2, priceLineVisible: false, lineStyle: 2, priceFormat: PF });
        seriesInd.sar.setData(calcularParabolicSAR(datosActuales));
      } else if (seriesInd.sar) {
        chart.removeSeries(seriesInd.sar); seriesInd.sar = null;
      }
    }

    // Renderizar lista en el modal de indicadores
    function renderizarListaIndicadores(filtro){
      var container = document.getElementById('ind-list-container');
      container.innerHTML = '';
      var textoFiltro = (filtro || '').toLowerCase();

      CATALOGO_INDICADORES.forEach(function(ind){
        if (textoFiltro && ind.nombre.toLowerCase().indexOf(textoFiltro) === -1 && ind.tipo.toLowerCase().indexOf(textoFiltro) === -1) return;
        
        var activo = indicadores[ind.id];
        var div = document.createElement('div');
        div.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:10px 20px; cursor:pointer; transition:background 0.1s;';
        div.onmouseover = function(){ div.style.background = 'rgba(139,92,246,0.15)'; };
        div.onmouseout = function(){ div.style.background = 'transparent'; };

        div.innerHTML = '<div style="display:flex; flex-direction:column; gap:2px;">' +
                        '<span style="font-size:13px; color:#d1d4dc; font-weight:500;">' + ind.nombre + '</span>' +
                        '<span style="font-size:11px; color:#8b949e;">' + ind.tipo + '</span>' +
                        '</div>' +
                        '<span style="font-size:12px; font-weight:bold; padding:3px 8px; border-radius:4px; ' + 
                        (activo ? 'background:rgba(63,185,80,0.2); color:#3fb950;' : 'background:rgba(255,255,255,0.06); color:#8b949e;') + '">' + 
                        (activo ? 'Activo' : 'Añadir') + '</span>';

        div.addEventListener('click', function(){
          indicadores[ind.id] = !indicadores[ind.id];
          actualizarIndicadoresActivos();
          renderizarListaIndicadores(document.getElementById('ind-search-input').value);
        });

        container.appendChild(div);
      });
    }

    var modalOverlay = document.getElementById('ind-modal-overlay');
    var btnIndSelect = document.getElementById('btn-ind-select');
    var modalClose = document.getElementById('ind-modal-close');
    var searchInput = document.getElementById('ind-search-input');

    btnIndSelect.addEventListener('click', function(e){
      e.stopPropagation();
      modalOverlay.style.display = 'flex';
      renderizarListaIndicadores('');
      setTimeout(function(){ searchInput.focus(); }, 50);
    });

    modalClose.addEventListener('click', function(){
      modalOverlay.style.display = 'none';
    });

    modalOverlay.addEventListener('click', function(e){
      if (e.target === modalOverlay) modalOverlay.style.display = 'none';
    });

    searchInput.addEventListener('input', function(e){
      renderizarListaIndicadores(e.target.value);
    });

    function calcularHeikinAshi(datos){
      var ha = [];
      for (var i = 0; i < datos.length; i++){
        var d = datos[i];
        var haClose = (d.open + d.high + d.low + d.close) / 4;
        var haOpen = (i === 0) ? (d.open + d.close) / 2 : (ha[i-1].open + ha[i-1].close) / 2;
        var haHigh = Math.max(d.high, haOpen, haClose);
        var haLow = Math.min(d.low, haOpen, haClose);
        ha.push({ time: d.time, open: haOpen, high: haHigh, low: haLow, close: haClose, volume: d.volume });
      }
      return ha;
    }

    function formatearDatos(datos, tipo){
      if (tipo === "line" || tipo === "area") {
        return datos.map(function(v){ return { time: v.time, value: v.close }; });
      }
      if (tipo === "heikin") {
        var ha = calcularHeikinAshi(datos);
        return ha.map(function(v){ return { time: v.time, open: v.open, high: v.high, low: v.low, close: v.close }; });
      }
      return datos.map(function(v){ return { time: v.time, open: v.open, high: v.high, low: v.low, close: v.close }; });
    }

    function aPuntoVolumen(v){
      return { time: v.time, value: v.volume || 0, color: (v.close >= v.open ? 'rgba(63,185,80,0.5)' : 'rgba(248,81,73,0.5)') };
    }

    function fmtVol(v){
      v = v || 0;
      if (v >= 1e9) return (v/1e9).toFixed(2) + 'B';
      if (v >= 1e6) return (v/1e6).toFixed(2) + 'M';
      if (v >= 1e3) return (v/1e3).toFixed(2) + 'K';
      return String(v);
    }

    function actualizarLeyenda(v){
      if (!v) return;
      var elOhlc = document.getElementById('tv-ohlc-vals');
      var elVol = document.getElementById('tv-vol-val');
      if (!elOhlc) return;
      
      var cierreAnt = v.open;
      if (datosActuales.length > 1) {
        var idxActual = datosActuales.findIndex(function(d){ return d.time === v.time; });
        if (idxActual > 0) {
          cierreAnt = datosActuales[idxActual - 1].close;
        } else if (idxActual === -1 && datosActuales.length > 0) {
          cierreAnt = datosActuales[datosActuales.length - 2].close;
        }
      }

      var delta = v.close - cierreAnt;
      var pct = cierreAnt ? (delta / cierreAnt) * 100 : 0;
      var col = (v.close >= v.open) ? '#3fb950' : '#f85149';
      var colD = (delta >= 0) ? '#3fb950' : '#f85149';
      function c(l, n){ return l + '<b style="color:' + col + '">' + n.toFixed(DIGITS) + '</b>'; }
      elOhlc.innerHTML =
        c('O', v.open) + c('H', v.high) + c('L', v.low) + c('C', v.close) +
        '<b style="color:' + colD + '">' + (delta >= 0 ? '+' : '') + delta.toFixed(DIGITS) +
        ' (' + (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%)</b>';
      if (elVol) elVol.innerText = 'Vol ' + fmtVol(v.volume);
    }

    function cargar(tf, n, ajustarFit){
      tfActual = tf;
      var elTf = document.getElementById('lg-tf');
      if (elTf) elTf.innerText = (tf === 'MN1' ? 'MN' : tf);
      nBarrasActual = n;
      var miId = ++cargaId;
      cargando = true;
      fetch(API + "/velas/" + encodeURIComponent(SIMBOLO) + "?tf=" + tf + "&n=" + n)
        .then(function(r){
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function(velas){
          if (miId !== cargaId) return;
          cargando = false;
          if (velas && velas.length){
            datosActuales = velas;
            serie.setData(formatearDatos(velas, tipoActual));
            serieVolumen.setData(velas.map(aPuntoVolumen));
            if (ajustarFit === 'ultimas') {
              var nv = datosActuales.length;
              chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, nv - 150), to: nv + 8 });
            } else if (ajustarFit) {
              chart.timeScale().fitContent();
            }
            actualizarLeyenda(velas[velas.length - 1]);
            actualizarIndicadoresActivos();
            redibujarTodo();
          }
        })
        .catch(function(){
          if (miId !== cargaId) return;
          cargando = false;
          if (!datosActuales.length) {
            var elOhlc = document.getElementById('tv-ohlc-vals');
            if (elOhlc) elOhlc.innerText = 'Sin conexión con la API (' + API + ')';
          }
        });
    }

    cargar(tfActual, nBarrasActual, 'ultimas');

    var btnTypeSelect = document.getElementById('btn-type-select');
    var typeMenu = document.getElementById('type-menu');

    btnTypeSelect.addEventListener('click', function(e){ e.stopPropagation(); typeMenu.classList.toggle('show'); });

    window.addEventListener('click', function(){
      typeMenu.classList.remove('show');
    });

    document.querySelectorAll('#type-menu .tv-drop-item').forEach(function(item){
      item.addEventListener('click', function(){
        tipoActual = item.getAttribute('data-type');
        btnTypeSelect.innerHTML = item.querySelector('svg').outerHTML + '<span>' + item.getAttribute('data-label') + '</span><svg class="caret" viewBox="0 0 10 10"><path d="M2 3.5L5 6.5L8 3.5"/></svg>';
        crearSerie(tipoActual);
        if (datosActuales.length){
          serie.setData(formatearDatos(datosActuales, tipoActual));
          serieVolumen.setData(datosActuales.map(aPuntoVolumen));
          actualizarIndicadoresActivos();
        }
        redibujarTodo();
      });
    });

    setInterval(function(){
      if (cargando || pollEnCurso || !datosActuales.length) return;
      var tfLlamada = tfActual;
      var idLlamada = cargaId;
      pollEnCurso = true;
      fetch(API + "/ultima/" + encodeURIComponent(SIMBOLO) + "?tf=" + tfLlamada)
        .then(function(r){ return r.json(); })
        .then(function(v){
          if (tfLlamada !== tfActual || idLlamada !== cargaId) return;
          if (v && v.time){
            var ultima = datosActuales[datosActuales.length - 1];
            if (v.time < ultima.time) return;
            if (ultima.time === v.time){
              datosActuales[datosActuales.length - 1] = v;
            } else {
              datosActuales.push(v);
            }
            var datosFormateados = formatearDatos(datosActuales, tipoActual);
            serie.update(datosFormateados[datosFormateados.length - 1]);
            serieVolumen.update(aPuntoVolumen(v));
            actualizarLeyenda(v);
            actualizarIndicadoresActivos();
            redibujarTodo();
          }
        })
        .catch(function(){})
        .then(function(){ pollEnCurso = false; });
    }, 1500);

    chart.subscribeCrosshairMove(function(param){
      if (!param || !param.time){
        if (datosActuales.length) actualizarLeyenda(datosActuales[datosActuales.length - 1]);
        return;
      }
      var idx = datosActuales.findIndex(function(d){ return d.time === param.time; });
      if (idx >= 0) actualizarLeyenda(datosActuales[idx]);
    });

    function marcarTF(tf){
      document.querySelectorAll('.tvtf').forEach(function(b){
        b.classList.toggle('active', b.getAttribute('data-tf') === tf);
      });
    }

    document.querySelectorAll('.tvtf').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tf = btn.getAttribute('data-tf');
        marcarTF(tf);
        document.querySelectorAll('.tvrange').forEach(function(b){ b.classList.remove('active'); });
        cargar(tf, parseInt(btn.getAttribute('data-n'), 10), 'ultimas');
      });
    });

    document.querySelectorAll('.tvrange').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tf = btn.getAttribute('data-tf');
        document.querySelectorAll('.tvrange').forEach(function(b){ b.classList.remove('active'); });
        btn.classList.add('active');
        marcarTF(tf);
        cargar(tf, parseInt(btn.getAttribute('data-n'), 10), true);
      });
    });

    var btnShot = document.getElementById('btn-shot');
    if (btnShot){
      btnShot.addEventListener('click', function(){
        try {
          var shot = chart.takeScreenshot();
          var selPrev = seleccionadoId, hovPrev = hoverId;
          seleccionadoId = null; hoverId = null;
          pintar();
          var out = document.createElement('canvas');
          out.width = shot.width; out.height = shot.height;
          var oc = out.getContext('2d');
          oc.drawImage(shot, 0, 0);
          oc.drawImage(canvas, 0, 0, shot.width, shot.height);
          seleccionadoId = selPrev; hoverId = hovPrev;
          redibujarTodo();

          var esc = shot.width / Math.max(1, cssW);
          var ahora = new Date();
          function dos(n){ return (n < 10 ? '0' : '') + n; }
          var fecha = ahora.getFullYear() + '-' + dos(ahora.getMonth() + 1) + '-' + dos(ahora.getDate()) + ' ' + dos(ahora.getHours()) + ':' + dos(ahora.getMinutes());
          oc.save();
          oc.textBaseline = 'top';
          oc.font = 'bold ' + Math.round(15 * esc) + 'px sans-serif';
          oc.fillStyle = '#ffffff';
          oc.fillText(SIMBOLO + '  ·  ' + tfActual, 14 * esc, 10 * esc);
          oc.font = Math.round(11 * esc) + 'px sans-serif';
          oc.fillStyle = '#8b949e';
          oc.textAlign = 'right';
          oc.fillText('P&J  ·  ' + fecha, shot.width - 74 * esc, 12 * esc);
          oc.restore();

          out.toBlob(function(blob){
            if (!blob) return;
            var url = URL.createObjectURL(blob);
            var enlace = document.createElement('a');
            enlace.download = SIMBOLO + '_' + tfActual + '_' + fecha.replace(/[- :]/g, '') + '.png';
            enlace.href = url;
            document.body.appendChild(enlace);
            enlace.click();
            document.body.removeChild(enlace);
            setTimeout(function(){ URL.revokeObjectURL(url); }, 2000);
          }, 'image/png');
        } catch (e) {}
      });
    }

    var btnFull = document.getElementById('btn-full');
    var wrap = document.getElementById('tv-wrap');
    if (btnFull && wrap){
      btnFull.addEventListener('click', function(){
        if (!document.fullscreenElement){
          if (wrap.requestFullscreen) wrap.requestFullscreen();
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
        }
      });
    }
  }
  iniciar();
})();
</script>
"""


def _limpiar_simbolo(valor: str) -> str:
    """Quita los puntos suspensivos con que la lista de activos abrevia el símbolo."""
    return valor.replace("...", "").replace("…", "").strip()


def _info_simbolo(simbolo: str) -> Tuple[int, float]:
    """
    Devuelve (decimales, tamaño_del_pip) del símbolo según MT5.
    El pip es 0.0 si el activo no es forex.
    """
    digits = 5
    pip = 0.0
    try:
        mt5.symbol_select(simbolo, True)
        info = mt5.symbol_info(simbolo)
        if info is not None:
            digits = int(info.digits)
            es_forex = info.trade_calc_mode == getattr(mt5, "SYMBOL_CALC_MODE_FOREX", 0)
            if es_forex:
                pip = float(info.point) * (10 if digits in (3, 5) else 1)
    except Exception:
        pass
    return digits, pip


def renderizar_panel_central(main: Optional[ModuleType]):
    inicializar_mt5()

    activo_actual = st.session_state.get("activo_seleccionado", "EURUSD...")
    activo_visible = _limpiar_simbolo(activo_actual)
    digits, pip = _info_simbolo(activo_visible)

    @st.fragment(run_every="2s")
    def _cabecera_precio():
        info_tick = obtener_precio_actual(activo_visible)
        conectado = "error" not in info_tick
        if conectado:
            precio_actual = info_tick.get("last", 0) if info_tick.get("last", 0) > 0 else info_tick.get("bid", 0)
        else:
            precio_actual = 0.0
        bid = float(info_tick.get("bid", 0) or 0)
        ask = float(info_tick.get("ask", 0) or 0)
        conectado = conectado and precio_actual > 0

        clave = f"_prev_precio_{activo_visible}"
        clave_color = f"_color_precio_{activo_visible}"
        if conectado:
            anterior = st.session_state.get(clave, precio_actual)
            if precio_actual > anterior:
                color_var_activo = "#3fb950"
            elif precio_actual < anterior:
                color_var_activo = "#f85149"
            else:
                color_var_activo = st.session_state.get(clave_color, "#3fb950")
            st.session_state[clave] = precio_actual
            st.session_state[clave_color] = color_var_activo
        else:
            color_var_activo = "#8b949e"

        color_estado = "#3fb950" if conectado else "#f85149"
        texto_estado = "Conectado" if conectado else "Sin conexión"
        
        st.markdown(f"""
            <div style='background-color: #161b22; padding: 10px 16px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;'>
                <div style='display: flex; align-items: center; gap: 14px;'>
                    <span style='font-size: 20px; font-weight: bold; color: #ffffff;'>{escape(activo_visible)}</span>
                    <span style='background: #30363d; color: #8b949e; padding: 2px 8px; border-radius: 4px; font-size: 11px;'>XM / MT5</span>
                    <span style='font-size: 22px; font-weight: bold; font-family: monospace; color: {color_var_activo};'>{precio_actual:,.{digits}f}</span>
                    <span style='font-size: 14px; font-weight: 600; color: {color_var_activo};'>Bid: {bid:,.{digits}f} | Ask: {ask:,.{digits}f}</span>
                </div>
                <div style='font-size: 13px; color: #8b949e; font-weight: 600; display: flex; align-items: center; gap: 6px;'>
                    {texto_estado} <span style='color: {color_estado}; font-size: 16px;'>●</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    _cabecera_precio()

    html_chart = (
        _CHART_TEMPLATE
        .replace("__SIMBOLO_HTML__", escape(activo_visible))
        .replace("__SIMBOLO_JS__", json.dumps(activo_visible))
        .replace("__API_URL_JS__", json.dumps(API_URL))
        .replace("__DIGITS__", str(digits))
        .replace("__PIP__", json.dumps(pip))
    )
    components.html(html_chart, height=750)

    # --- ZONA DE CHAT INFERIOR CONECTADA A main.py ---
    st.markdown("---")
    st.markdown("### 🤖 Asistente IA Analítico (Consola, Gráficos e Imágenes)")
    st.caption("Interactúa libremente con el agente bursátil. Mantiene contexto, herramientas, gráficos e imágenes renderizadas.")

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
                        activo_encontrado = activo_visible

                        df_chat = obtener_datos_historicos(activo_encontrado, timeframe=mt5.TIMEFRAME_H1, n_velas=30)
                        if not df_chat.empty:
                            valores = df_chat['close'].values
                            chart_data_resultado = pd.DataFrame(valores, columns=[f'Rendimiento - {activo_encontrado}'])

                            fig = Figure(figsize=(8, 4), facecolor='#0d1117')
                            ax = fig.subplots()
                            ax.set_facecolor('#0d1117')
                            ax.tick_params(colors='#8b949e')
                            for borde in ax.spines.values():
                                borde.set_color('#30363d')
                            ax.plot(valores, color='#3fb950', linewidth=2, label=f'Tendencia {activo_encontrado}')
                            ax.fill_between(range(len(valores)), valores, float(np.min(valores) * 0.99), color='#238636', alpha=0.2)
                            ax.set_title(f"Análisis Técnico y Gráfico Renderizado (MT5) - {activo_encontrado}", color='white', fontsize=12, fontweight='bold')
                            ax.set_xlabel("Barras", color='#8b949e')
                            ax.set_ylabel("Precio", color='#8b949e')
                            ax.grid(True, color='#30363d', linestyle='--', alpha=0.5)
                            ax.legend(loc='upper left', facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

                            os.makedirs("downloads", exist_ok=True)
                            imagen_filename = f"downloads/grafico_{activo_encontrado.lower()}_{int(time.time())}.png"
                            fig.savefig(imagen_filename, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())

                            imagen_resultado_path = imagen_filename
                            respuesta_final += f"\n\n*Gráfico interactivo e imagen renderizada con datos de MetaTrader 5 para **{activo_encontrado}**.*"

                    st.markdown(respuesta_final)
                    if chart_data_resultado is not None:
                        st.line_chart(chart_data_resultado)
                    if imagen_resultado_path is not None:
                        st.image(imagen_resultado_path, caption=f"Imagen renderizada del análisis", use_container_width=True)

                    st.session_state.mensajes_ui.append({
                        "role": "assistant",
                        "content": respuesta_final,
                        "chart_data": chart_data_resultado,
                        "imagen_path": imagen_resultado_path
                    })