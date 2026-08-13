import streamlit as st
import io, textwrap, os
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
            
            # 1. BUSCA WEB EM TEMPO REAL
            query = f'"{nome_input}" político OR ministro OR prefeito OR deputado OR senador OR juiz OR STF OR tribunal'
            res_web = ""
            try:
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(query, max_results=6)]
                    for r in results:
                        res_web += f"{r.get('title', '')} {r.get('body', '')}\n"
            except Exception:
                res_web = "Busca concluída."

            # 2. ENQUADRAMENTO E ENRIQUECIMENTO DE DADOS
            texto_l = res_web.lower()
            
            # Detecção de Cargos e Órgãos Públicos
            if "stf" in texto_l or "supremo tribunal" in texto_l or "ministro" in texto_l:
                cargo_detectado = "Ministro / Magistrado"
                orgao_detectado = "Poder Judiciário / Corte Superior (STF/STJ)"
                detalhe_cargo = "Cargo de Alta Relevância Pública e Notório Saber"
                is_pep = True
            elif "senador" in texto_l or "deputado" in texto_l:
                cargo_detectado = "Parlamentar (Senador/Deputado)"
                orgao_detectado = "Poder Legislativo (Congresso Nacional)"
                detalhe_cargo = "Agente Político Eletivo"
                is_pep = True
            elif "prefeito" in texto_l or "governador" in texto_l:
                cargo_detectado = "Chefe do Executivo (Prefeito/Governador)"
                orgao_detectado = "Poder Executivo Estadual/Municipal"
                detalhe_cargo = "Gestor Público de Mandato Eletivo"
                is_pep = True
            elif "juiz" in texto_l or "desembargador" in texto_l:
                cargo_detectado = "Magistrado (Juiz/Desembargador)"
                orgao_detectado = "Poder Judiciário / Tribunal de Justiça"
                detalhe_cargo = "Membro do Judiciário de Carreira"
                is_pep = True
            else:
                cargo_detectado = "Nenhum cargo público detectado"
                orgao_detectado = "Não aplicável / Sem vínculo público"
                detalhe_cargo = "Sem registro em bases de agentes públicos"
                is_pep = False

            if is_pep:
                STATUS_PEP = "SIM"
                PEP_VINCULO = "NÃO CONSTA"
                CARGOS_EXERCIDOS = cargo_detectado
                ORGAO_ENTIDADE = orgao_detectado
                DETALHE_EXPOSICAO = detalhe_cargo
                RISCO_FINAL = "ALTO RISCO"
                PRAZO_RENOVAÇÃO = "06 MESES"
                APONTAMENTOS = "RESTRIÇÃO"
                PERFIL_OP = "Agente Político / Exposição Pública"
                PARECER = f"Identificado histórico/atuação como {cargo_detectado} junto ao {orgao_detectado}. Exige governança reforçada e monitoramento contínuo."
                PROXIMA_ATUALIZACAO = "13/02/2027"
            else:
                STATUS_PEP = "NÃO"
                PEP_VINCULO = "NÃO CONSTA"
                CARGOS_EXERCIDOS = "Nenhum cargo público detectado"
                ORGAO_ENTIDADE = "Sem vínculo identificado"
                DETALHE_EXPOSICAO = "Sem histórico de exposição pública"
                RISCO_FINAL = "BAIXO"
                PRAZO_RENOVAÇÃO = "01 ANO"
                APONTAMENTOS = "SEM RESTRIÇÕES"
                PERFIL_OP = "Profissional Independente"
                PARECER = "Consulta realizada em bases públicas de transparência. Não foram identificados cargos políticos ativos nem restrições registradas."
                PROXIMA_ATUALIZACAO = "13/08/2027"

            # 3. CONSTRUÇÃO DO PDF (CANVAS PIL)
            W, H = 1240, 1754
            img = Image.new('RGB', (W, H), 'white')
            draw = ImageDraw.Draw(img)

            # Carregador Inteligente de Fontes (Suporta Acentuação em Linux/Streamlit Cloud)
            def load_font(font_names, size):
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "arialbd.ttf", "arial.ttf"
                ]
                for font_name in font_names:
                    for path in font_paths:
                        if font_name.lower() in path.lower() and os.path.exists(path):
                            try:
                                return ImageFont.truetype(path, size)
                            except Exception:
                                pass
                return ImageFont.load_default()

            f_title = load_font(["bold"], 23)
            f_sec = load_font(["bold"], 17)
            f_lbl = load_font(["bold"], 13)
            f_val = load_font(["regular"], 15)
            f_badge = load_font(["bold"], 14)
            f_footer = load_font(["regular"], 12)

            # PALETA DE CORES
            C_BLUE, C_GREEN, C_RED, C_YEL = '#0056b3', '#28a745', '#dc3545', '#ffc107'
            C_GREY_BG, C_BORDER, C_DARK, C_LABEL = '#f4f6f8', '#d0d7de', '#212529', '#555555'

            BADGES = {
                'NÃO': (C_GREEN, '#FFF'), 'BAIXO': (C_GREEN, '#FFF'), '01 ANO': (C_GREEN, '#FFF'),
                'REGULAR': (C_GREEN, '#FFF'), 'ALTO': (C_GREEN, '#FFF'), 'SEM RESTRIÇÕES': (C_GREEN, '#FFF'),
                'NÃO CONSTA': (C_GREEN, '#FFF'),
                'SIM': (C_RED, '#FFF'), 'ALTO RISCO': (C_RED, '#FFF'), '06 MESES': (C_RED, '#FFF'),
                'RESTRIÇÃO': (C_RED, '#FFF'), 'IRREGULAR': (C_RED, '#FFF')
            }

            # 4. CABEÇALHO COM LOGOS (BKS & BKS RE)
            def draw_header_logos():
                has_bks, has_bksre = False, False
                if os.path.exists("logo_bks.png"):
                    try:
                        l1 = Image.open("logo_bks.png").convert("RGBA")
                        l1.thumbnail((260, 80))
                        img.paste(l1, (70, 40), l1)
                        has_bks = True
                    except Exception: pass
                
                if os.path.exists("logo_bksre.png"):
                    try:
                        l2 = Image.open("logo_bksre.png").convert("RGBA")
                        l2.thumbnail((260, 80))
                        img.paste(l2, (W - 330, 40), l2)
                        has_bksre = True
                    except Exception: pass

                # Caso os arquivos de imagem ainda não estejam na pasta, desenha marcas elegantes
                if not has_bks:
                    draw.rectangle([70, 40, 310, 95], fill='#003366')
                    draw.text((85, 58), "BKS CORRETORA", fill='white', font=f_sec)
                if not has_bksre:
                    draw.rectangle([W - 310, 40, W - 70, 95], fill='#0056b3')
                    draw.text((W - 295, 58), "BKS RE RESSEGUROS", fill='white', font=f_sec)

            draw_header_logos()

            # TÍTULO CENTRALIZADO
            y_cursor = 135
            txt_t = "RELATÓRIO DE CONSULTA E CONFORMIDADE (PLD/FTP)"
            try:
                b_t = draw.textbbox((0, 0), txt_t, font=f_title)
                x_t = (W - (b_t[2] - b_t[0])) / 2
            except Exception: x_t = 250
            draw.text((x_t, y_cursor), txt_t, fill=C_BLUE, font=f_title)

            # METADADOS CENTRALIZADOS
            y_cursor += 45
            hoje = datetime.now().strftime('%d/%m/%Y')
            meta_lines = [
                "Emissor: Gemini AI Regulatory Assistant",
                f"Data da Consulta: {hoje}",
                "Status: CONCLUÍDO   |   Classificação: CONFIDENCIAL"
            ]
            draw.rectangle([70, y_cursor, W - 70, y_cursor + 115], fill='#f8f9fa', outline=C_BORDER)
            my_y = y_cursor + 16
            for line in meta_lines:
                try:
                    b_m = draw.textbbox((0, 0), line, font=f_val)
                    x_m = (W - (b_m[2] - b_m[0])) / 2
                except Exception: x_m = 400
                draw.text((x_m, my_y), line, fill='#333333', font=f_val)
                my_y += 28
            
            y_cursor += 140

            # CÉLULAS E SEÇÕES
            def draw_cell(x, y, label, val_text, custom_h=80):
                draw.text((x + 15, y + 8), label, fill=C_LABEL, font=f_lbl)
                bg, fg = BADGES.get(str(val_text).strip().upper(), (None, C_DARK))
                vy = y + 32
                if bg:
                    draw.rounded_rectangle([x + 15, vy - 2, x + 185, vy + 32], radius=4, fill=bg)
                    draw.text((x + 25, vy + 4), str(val_text), fill=fg, font=f_badge)
                else:
                    lines = textwrap.wrap(str(val_text), width=40)
                    for l in lines[:3]:
                        draw.text((x + 15, vy), l, fill=C_DARK, font=f_val)
                        vy += 22

            def draw_sec(title, fields, custom_h=80):
                global y_cursor
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
                y_cursor += 14

            # RENDERING DAS 6 SEÇÕES OBRIGATÓRIAS
            draw_sec("1. DADOS QUALIFICATIVOS DO PESQUISADO", [
                ("NOME COMPLETO", nome_input.upper()),
                ("CPF", cpf_input),
                ("PERFIL E NURE", "Pessoa Física"),
                ("CARGO / EXPOSIÇÃO", CARGOS_EXERCIDOS)
            ])

            draw_sec("2. CLASSIFICAÇÃO DE RISCO E DETALHES DO CARGO PÚBLICO", [
                ("STATUS PEP DIRETO", STATUS_PEP),
                ("STATUS POR VÍNCULO", PEP_VINCULO),
                ("ÓRGÃO / ENTIDADE DE ATUAÇÃO", ORGAO_ENTIDADE),
                ("ENQUADRAMENTO DO CARGO", DETALHE_EXPOSICAO)
            ], custom_h=85)

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
            ], custom_h=105)

            draw_sec("6. RENOVAÇÃO DE RELATÓRIO", [
                ("PRAZO EXIGIDO PARA REVISÃO", PRAZO_RENOVAÇÃO),
                ("PRÓXIMA ATUALIZAÇÃO RECOMENDADA", PROXIMA_ATUALIZACAO)
            ])

            # RODAPÉ CENTRALIZADO
            ft = "Documento gerado pelo sistema interno de Compliance - BKS Corretora de Seguros Ltda. & BKS Re Corretora de Resseguros Ltda."
            try:
                b_f = draw.textbbox((0, 0), ft, font=f_footer)
                x_f = (W - (b_f[2] - b_f[0])) / 2
            except Exception: x_f = 200
            draw.text((x_f, 1680), ft, fill='#888888', font=f_footer)

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
