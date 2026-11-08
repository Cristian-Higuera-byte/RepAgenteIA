#!/usr/bin/env bash
# Ejecutar desde la raíz del repositorio RepAgenteIA (donde están las carpetas FASE 1 y FASE 2).
# Renombra las evidencias individuales al formato Apellido_Nombre_N.N_APT122_NombreDelDocumento.docx
# (git mv conserva el historial).
set -e
cd "FASE 1/EVIDENCIAS INDIVIDUALES"
git mv CRISTIAN_HIGUERA_1.1_APT122_AutoevaluacionCompetenciasFase1.docx HIGUERA_CRISTIAN_1.1_APT122_AutoevaluacionCompetenciasFase1.docx
git mv CRISTIAN_HIGUERA_1.2_APT122_DiarioReflexionFase1.docx            HIGUERA_CRISTIAN_1.2_APT122_DiarioReflexionFase1.docx
git mv CRISTIAN_HIGUERA_1.3_APT122_AutoevaluacionFase1.docx             HIGUERA_CRISTIAN_1.3_APT122_AutoevaluacionFase1.docx
cd ../../"FASE 2/Individuales"
git mv CRISTIAN_HIGUERA_2.1_APT122_DiarioReflexionFase2.docx            HIGUERA_CRISTIAN_2.1_APT122_DiarioReflexionFase2.docx
git mv "CRISTIAN_HIGUERA_2.2_APT122_AutoevaluacionAvance Fase2.docx"    HIGUERA_CRISTIAN_2.2_APT122_AutoevaluacionAvanceFase2.docx
git mv JOAQUIN_ALLENDES_2.1_APT122_DiarioReflexionFase2.docx            ALLENDES_JOAQUIN_2.1_APT122_DiarioReflexionFase2.docx
git mv "JOAQUIN_ALLENDES_2.2_APT122_AutoevaluacionAvance Fase2.docx"    ALLENDES_JOAQUIN_2.2_APT122_AutoevaluacionAvanceFase2.docx
cd ../..
echo "Renombres listos. Configura tu identidad de Git (cada integrante con SUS datos reales):"
echo '  git config --global user.name  "Nombre Apellido"'
echo '  git config --global user.email "correo.institucional@duocuc.cl"'
echo 'Luego: git add -A && git commit -m "Renombra evidencias individuales al formato APT122" && git push'
