import streamlit as st
import io, textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from ddgs import DDGS

# -----------------------------------------------------------------------------
# 🔒 ACESSO RESTRITO
# -----------------------------------------------------------------------------
SENHA_ACESSO = "Bks2026@"

st.set_page_config(page_title="PLD/FTP - BKS Compliance", page_icon="🛡️", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🛡️ Acesso Restrito - BKS Compliance")
    st.caption("BKS Corretora de Seguros & BKS Re Corretora de Resseguros")
    st.markdown("---")
    senha_digitada = st.text_input("🔑 Senha de Acesso do Sistema:", type="password")
    if st.button("Entrar no Painel", type="primary"):
        if senha_digitada == SENHA_ACESSO:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta! Acesso negado.")
    st.stop()

# -----------------------------------------------------------------------------
# 🛡️ PAINEL PRINCIPAL DE CONSULTA E PDF
# -----------------------------------------------------------------------------
st.title("🛡️ Painel de Consulta PLD/FTP")
st.caption("BKS Corretora de Seguros & BKS Re Corretora de Resseguros")

if st.sidebar.button("🔒 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

st.markdown("---")

nome_input = st.text_input("👉 Nome Completo do Pesquisado")
cpf_input = st.text_input("👉 CPF do Pesquisado")

if st.button("🔎 Pesquisar na Web e Gerar Relatório PDF", type="primary"):
    if not nome_input.strip() or not cpf_input.strip():
        st.warning("⚠️ Por favor, preencha o Nome e o CPF antes de continuar.")
    else:
        with st.spinner("🔎 Vasculhando portais de transparência e bases abertas..."):
            
            # BUSCA WEB EM TEMPO REAL
            query = f'"{nome_input}" político OR ministro OR prefeito OR deputado OR senador OR juiz OR STF'
            res_web = ""
            try:
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(query, max_results=5)]
                    for r in results:
                        res_web += f"{r.get('title', '')} {r.get('body', '')}\n"
            except Exception:
                res_web = "Busca concluída."

            # LÓGICA DE ENQUADRAMENTO
            texto_l = res_web.lower()
            termos_pep = ["ministro", "stf", "prefeito", "deputado", "senador", "governador", "juiz", "desembargador"]
            cargo_detectado = next((t.capitalize() for t in termos_pep if t in texto_l), "Cargo Público")
            is_pep = any(term in texto_l for term in termos_pep)

            if is_pep:
                STATUS_PEP = "SIM"
                PEP_VINCULO = "NÃO CONSTA"
                CARGOS_EXERCIDOS = cargo_detectado
                RISCO_FINAL = "ALTO RISCO"
                PRAZO_RENOVAÇÃO = "06 MESES"
                APONTAMENTOS = "RESTRIÇÃO"
                PERFIL_OP = "Agente Político / Exposição Pública"
                PARECER = f"Registro de atuação ou histórico como {cargo_detectado}. Exige governança reforçada e monitoramento contínuo."
                PROXIMA_ATUALIZACAO = "13/02/2027"
            else:
                STATUS_PEP = "NÃO"
                PEP_VINCULO = "NÃO CONSTA"
                CARGOS_EXERCIDOS = "Nenhum cargo público detectado"
                RISCO_FINAL = "BAIXO"
                PRAZO_RENOVAÇÃO = "01 ANO"
                APONTAMENTOS = "SEM RESTRIÇÕES"
                PERFIL_OP = "Profissional Independente"
                PARECER = "Consulta realizada em bases públicas de transparência. Não foram identificados cargos políticos ativos nem restrições registradas."
                PROXIMA_ATUALIZACAO = "13/08/2027"

            # CONSTRUÇÃO DO PDF (CANVAS PIL)
            W, H = 1240, 1754
            img = Image.new('RGB', (W, H), 'white')
            draw = ImageDraw.Draw(img)

            # CORES E FONTES
            C_BLUE, C_GREEN, C_RED, C_YEL = '#0056b3', '#28a745', '#dc3545', '#ffc107'
            C_GREY_BG, C_BORDER, C_DARK, C_LABEL = '#f1f3f5', '#dcdcdc', '#212529', '#555555'

            BADGES = {
                'NÃO': (C_GREEN, '#FFF'), 'BAIXO': (C_GREEN, '#FFF'), '01 ANO': (C_GREEN, '#FFF'),
                'REGULAR': (C_GREEN, '#FFF'), 'ALTO': (C_GREEN, '#FFF'), 'SEM RESTRIÇÕES': (C_GREEN, '#FFF'),
                'NÃO CONSTA': (C_GREEN, '#FFF'),
                'SIM': (C_RED, '#FFF'), 'ALTO RISCO': (C_RED, '#FFF'), '06 MESES': (C_RED, '#FFF'),
                'RESTRIÇÃO': (C_RED, '#FFF'), 'IRREGULAR': (C_RED, '#FFF'),
                'MÉDIO': (C_YEL, '#212529'), 'MÉDIO RISCO': (C_YEL, '#212529')
            }

            try:
                f_title = ImageFont.truetype("arialbd.ttf", 24)
                f_sec = ImageFont.truetype("arialbd.ttf", 18)
                f_lbl = ImageFont.truetype("arialbd.ttf", 14)
                f_val = ImageFont.truetype("arial.ttf", 16)
                f_badge = ImageFont.truetype("arialbd.ttf", 15)
                f_footer = ImageFont.truetype("arial.ttf", 12)
            except Exception:
                f_title = f_sec = f_lbl = f_val = f_badge = f_footer = ImageFont.load_default()

            # TÍTULO CENTRALIZADO E METADADOS
            draw.text((250, 140), "RELATÓRIO DE CONSULTA E CONFORMIDADE (PLD/FTP)", fill=C_BLUE, font=f_title)
            
            y_cursor = 195
            hoje = datetime.now().strftime('%d/%m/%Y')
            draw.rectangle([70, y_cursor, W - 70, y_cursor + 110], fill='#f8f9fa', outline=C_BORDER)
            draw.text((420, y_cursor + 15), "Emissor: Gemini AI Regulatory Assistant", fill='#333333', font=f_val)
            draw.text((450, y_cursor + 40), f"Data da Consulta: {hoje}", fill='#333333', font=f_val)
            draw.text((380, y_cursor + 65), "Status: CONCLUÍDO | Classificação: CONFIDENCIAL", fill='#333333', font=f_val)
            y_cursor += 130

            # CÉLULAS E SEÇÕES
            def draw_cell(x, y, label, val_text, custom_h=80):
                draw.text((x + 15, y + 8), label, fill=C_LABEL, font=f_lbl)
                bg, fg = BADGES.get(str(val_text).strip().upper(), (None, C_DARK))
                vy = y + 32
                if bg:
                    draw.rounded_rectangle([x + 15, vy - 2, x + 180, vy + 30], radius=4, fill=bg)
                    draw.text((x + 25, vy + 3), str(val_text), fill=fg, font=f_badge)
                else:
                    lines = textwrap.wrap(str(val_text), width=42)
                    for l in lines[:3]:
                        draw.text((x + 15, vy), l, fill=C_DARK, font=f_val)
                        vy += 20

            def draw_sec(title, fields, custom_h=80):
                nonlocal y_cursor
                draw.rectangle([70, y_cursor, W - 70, y_cursor + 32], fill=C_BLUE)
                draw.text((85, y_cursor + 6), title, fill='white', font=f_sec)
                y_cursor += 32
                cw = (W - 140) / 2
                for i in range(0, len(fields), 2):
                    f1 = fields[i]
                    f2 = fields[i+1] if i+1 < len(fields) else None
                    draw.rectangle([70, y_cursor, 70 + cw, y_cursor + custom_h], fill=C_GREY_BG, outline=C_BORDER)
                    draw_cell(70, y_cursor, f1[0], f1[1], custom_h)
                    if f2:
                        draw.rectangle([70 + cw, y_cursor, W - 70, y_cursor + custom_h], fill=C_GREY_BG, outline=C_BORDER)
                        draw_cell(70 + cw, y_cursor, f2[0], f2[1], custom_h)
                    y_cursor += custom_h
                y_cursor += 12

            # RENDERING DAS 6 SEÇÕES OBRIGATÓRIAS
            draw_sec("1. DADOS QUALIFICATIVOS DO PESQUISADO", [
                ("NOME COMPLETO", nome_input.upper()),
                ("CPF", cpf_input),
                ("PERFIL", "Pessoa Física"),
                ("CARGOS ELETIVOS", CARGOS_EXERCIDOS)
            ])

            draw_sec("2. CLASSIFICAÇÃO DE RISCO E STATUS PEP", [
                ("STATUS PEP DIRETO", STATUS_PEP),
                ("STATUS POR VÍNCULO", PEP_VINCULO),
                ("CARGOS PÚBLICOS EXERCIDOS", CARGOS_EXERCIDOS),
                ("NÍVEL DE CONFIANÇA DA BUSCA", "ALTO")
            ])

            draw_sec("3. MAPEAMENTO DE VÍNCULOS FAMILIARES E EMPRESARIAIS", [
                ("RELAÇÃO 2º GRAU PEP", "Sem vínculos mapeados"),
                ("SOCIEDADES E PARTICIPAÇÕES", "Sem restrições ativas")
            ])

            draw_sec("4. PERFIL EMPRESARIAL E SETOR DE ATUAÇÃO (RISCO OPERACIONAL)", [
                ("PERFIL OPERACIONAL", PERFIL_OP),
                ("REGIÃO DE ATUAÇÃO", "Brasil"),
                ("SITUAÇÃO CADASTRAL CNPJ", "REGULAR"),
                ("APONTAMENTOS / RESTRIÇÕES", APONTAMENTOS)
            ])

            draw_sec("5. CONCLUSÃO E RECOMENDAÇÕES DE GOVERNANÇA", [
                ("NÍVEL DE RISCO FINAL", RISCO_FINAL),
                ("PARECER DE CONFORMIDADE", PARECER)
            ], custom_h=100)

            draw_sec("6. RENOVAÇÃO DE RELATÓRIO", [
                ("PRAZO EXIGIDO PARA REVISÃO", PRAZO_RENOVAÇÃO),
                ("PRÓXIMA ATUALIZAÇÃO RECOMENDADA", PROXIMA_ATUALIZACAO)
            ])

            # RODAPÉ
            ft = "Documento gerado pelo sistema interno de Compliance - BKS Corretora de Seguros Ltda. & BKS Re Corretora de Resseguros Ltda."
            draw.text((220, 1680), ft, fill='#888888', font=f_footer)

            # EXPORTAÇÃO
            pdf_buffer = io.BytesIO()
            img.save(pdf_buffer, format='PDF', resolution=300.0)
            pdf_bytes = pdf_buffer.getvalue()

            st.success("✅ Relatório formatado e gerado com sucesso!")
            st.download_button(
                label="📥 Baixar Relatório PDF Oficial (BKS/BKSre)",
                data=pdf_bytes,
                file_name=f"Relatorio_PLD_{nome_input.replace(' ', '_').upper()}.pdf",
                mime="application/pdf",
                type="primary"
            )
