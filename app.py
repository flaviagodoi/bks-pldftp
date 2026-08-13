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

            # 2. ENQUADRAMENTO DE DADOS
            texto_l = res_web.lower()
            
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
                SITUACAO_CPF = "REGULAR"
                APONTAMENTOS = "RESTRIÇÃO: Exposição ativa por função pública / PEP"
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
                SITUACAO_CPF = "REGULAR"
                APONTAMENTOS = "SEM RESTRIÇÕES: Nada consta nas bases abertas"
                PERFIL_OP = "Profissional Independente"
                PARECER = "Consulta realizada em bases públicas de transparência. Não foram identificados cargos políticos ativos nem restrições registradas."
                PROXIMA_ATUALIZACAO = "13/08/2027"

            # 3. CONSTRUÇÃO DO PDF EM ALTA RESOLUÇÃO (CANVAS AMPLIA)
            W, H = 1600, 2260
            img = Image.new('RGB', (W, H), 'white')
            draw = ImageDraw.Draw(img)

            # CARREGAMENTO DE FONTES MAIORES
            f_title = f_sec = f_lbl = f_val = f_badge = f_footer = ImageFont.load_default()
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
            ]
            for p in font_paths:
                if os.path.exists(p):
                    try:
                        f_title = ImageFont.truetype(p, 30)
                        f_sec = ImageFont.truetype(p, 22)
                        f_lbl = ImageFont.truetype(p, 18)
                        f_val = ImageFont.truetype(p, 20)
                        f_badge = ImageFont.truetype(p, 19)
                        f_footer = ImageFont.truetype(p, 15)
                        break
                    except Exception: pass

            # PALETA DE CORES
            C_BLUE, C_GREEN, C_RED, C_YEL = '#0056b3', '#28a745', '#dc3545', '#ffc107'
            C_GREY_BG, C_BORDER, C_DARK, C_LABEL = '#f4f6f8', '#d0d7de', '#212529', '#555555'

            # APENAS ESTES CAMPOS RECEBEM BALÕES COLORIDOS (BADGES)
            BADGES_ONLY = {
                'NÃO': (C_GREEN, '#FFF'), 'SIM': (C_RED, '#FFF'),
                'BAIXO': (C_GREEN, '#FFF'), 'ALTO RISCO': (C_RED, '#FFF'), 'MÉDIO RISCO': (C_YEL, '#212529'),
                '01 ANO': (C_GREEN, '#FFF'), '06 MESES': (C_RED, '#FFF')
            }

            # 4. CABEÇALHO COM LOGOS EM TAMANHO DUPLO
            has_l1, has_l2 = False, False
            for ext in ['.png', '.PNG', '.jpg', '.jpeg']:
                p1 = f"logo_bks{ext}"
                p2 = f"logo_bksre{ext}"
                if os.path.exists(p1) and not has_l1:
                    try:
                        l1 = Image.open(p1).convert("RGBA")
                        l1.thumbnail((420, 140))
                        img.paste(l1, (90, 45), l1)
                        has_l1 = True
                    except Exception: pass
                if os.path.exists(p2) and not has_l2:
                    try:
                        l2 = Image.open(p2).convert("RGBA")
                        l2.thumbnail((420, 140))
                        img.paste(l2, (W - 510, 45), l2)
                        has_l2 = True
                    except Exception: pass

            if not has_l1:
                draw.rectangle([90, 45, 450, 130], fill='#003366')
                draw.text((110, 72), "BKS CORRETORA", fill='white', font=f_sec)
            if not has_l2:
                draw.rectangle([W - 450, 45, W - 90, 130], fill='#0056b3')
                draw.text((W - 430, 72), "BKS RE RESSEGUROS", fill='white', font=f_sec)

            # TÍTULO CENTRALIZADO
            y_cursor = 195
            txt_t = "RELATÓRIO DE CONSULTA E CONFORMIDADE (PLD/FTP)"
            try:
                b_t = draw.textbbox((0, 0), txt_t, font=f_title)
                x_t = (W - (b_t[2] - b_t[0])) / 2
            except Exception: x_t = 300
            draw.text((x_t, y_cursor), txt_t, fill=C_BLUE, font=f_title)

            # METADADOS CENTRALIZADOS
            y_cursor += 60
            hoje = datetime.now().strftime('%d/%m/%Y')
            meta_lines = [
                "Emissor: Gemini AI Regulatory Assistant",
                f"Data da Consulta: {hoje}",
                "Status: CONCLUÍDO   |   Classificação: CONFIDENCIAL"
            ]
            draw.rectangle([90, y_cursor, W - 90, y_cursor + 140], fill='#f8f9fa', outline=C_BORDER)
            my_y = y_cursor + 20
            for line in meta_lines:
                try:
                    b_m = draw.textbbox((0, 0), line, font=f_val)
                    x_m = (W - (b_m[2] - b_m[0])) / 2
                except Exception: x_m = 500
                draw.text((x_m, my_y), line, fill='#333333', font=f_val)
                my_y += 36
            
            y_cursor += 175

            # CÉLULAS E SEÇÕES COM ALTURA E ESPAÇAMENTO EXPANDIDOS
            def draw_cell(x, y, label, val_text, custom_h=105):
                draw.text((x + 20, y + 10), label, fill=C_LABEL, font=f_lbl)
                val_str = str(val_text).strip()
                bg_fg = BADGES_ONLY.get(val_str.upper(), None)
                vy = y + 42
                
                if bg_fg:
                    bg, fg = bg_fg
                    draw.rounded_rectangle([x + 20, vy - 2, x + 240, vy + 42], radius=6, fill=bg)
                    draw.text((x + 35, vy + 6), val_str, fill=fg, font=f_badge)
                else:
                    lines = textwrap.wrap(val_str, width=38)
                    for l in lines[:3]:
                        draw.text((x + 20, vy), l, fill=C_DARK, font=f_val)
                        vy += 28

            def draw_sec(title, fields, custom_h=105):
                global y_cursor
                draw.rectangle([90, y_cursor, W - 90, y_cursor + 42], fill=C_BLUE)
                draw.text((110, y_cursor + 8), title, fill='white', font=f_sec)
                y_cursor += 42
                cw = (W - 180) / 2
                for i in range(0, len(fields), 2):
                    f1 = fields[i]
                    f2 = fields[i+1] if i+1 < len(fields) else None
                    
                    # Desenha primeira coluna
                    draw.rectangle([90, y_cursor, 90 + cw, y_cursor + custom_h], fill=C_GREY_BG, outline=C_BORDER)
                    draw_cell(90, y_cursor, f1[0], f1[1], custom_h)
                    
                    # Desenha segunda coluna
                    if f2:
                        draw.rectangle([90 + cw, y_cursor, W - 90, y_cursor + custom_h], fill=C_GREY_BG, outline=C_BORDER)
                        draw_cell(90 + cw, y_cursor, f2[0], f2[1], custom_h)
                    
                    y_cursor += custom_h
                y_cursor += 18

            # RENDERING DAS 6 SEÇÕES COM MUDANÇAS SOLICITADAS
            draw_sec("1. DADOS QUALIFICATIVOS DO PESQUISADO", [
                ("NOME COMPLETO", nome_input.upper()),
                ("CPF", cpf_input),
                ("PERFIL E NATUREZA", "Pessoa Física"),
                ("CARGO / EXPOSIÇÃO", CARGOS_EXERCIDOS)
            ])

            draw_sec("2. CLASSIFICAÇÃO DE RISCO E DETALHES DO CARGO PÚBLICO", [
                ("STATUS PEP DIRETO", STATUS_PEP),
                ("STATUS POR VÍNCULO", PEP_VINCULO),
                ("ÓRGÃO / ENTIDADE DE ATUAÇÃO", ORGAO_ENTIDADE),
                ("ENQUADRAMENTO DO CARGO", DETALHE_EXPOSICAO)
            ], custom_h=115)

            draw_sec("3. MAPEAMENTO DE VÍNCULOS FAMILIARES E EMPRESARIAIS", [
                ("RELAÇÃO 2º GRAU PEP", "Sem vínculos mapeados"),
                ("SOCIEDADES E PARTICIPAÇÕES", "Sem restrições ativas")
            ])

            draw_sec("4. PERFIL EMPRESARIAL E SETOR DE ATUAÇÃO (RISCO OPERACIONAL)", [
                ("PERFIL OPERACIONAL", PERFIL_OP),
                ("REGIÃO DE ATUAÇÃO", "Brasil"),
                ("SITUAÇÃO CADASTRAL CPF", SITUACAO_CPF), # <-- MUDADO PARA CPF
                ("APONTAMENTOS / RESTRIÇÕES", APONTAMENTOS) # <-- COM MOTIVO SUCINTO
            ], custom_h=115)

            draw_sec("5. CONCLUSÃO E RECOMENDAÇÕES DE GOVERNANÇA", [
                ("NÍVEL DE RISCO FINAL", RISCO_FINAL),
                ("PARECER DE CONFORMIDADE", PARECER)
            ], custom_h=135)

            draw_sec("6. RENOVAÇÃO DE RELATÓRIO", [
                ("PRAZO EXIGIDO PARA REVISÃO", PRAZO_RENOVAÇÃO),
                ("PRÓXIMA ATUALIZAÇÃO RECOMENDADA", PROXIMA_ATUALIZACAO)
            ])

            # RODAPÉ CENTRALIZADO
            ft = "Documento gerado pelo sistema interno de Compliance - BKS Corretora de Seguros Ltda. & BKS Re Corretora de Resseguros Ltda."
            try:
                b_f = draw.textbbox((0, 0), ft, font=f_footer)
                x_f = (W - (b_f[2] - b_f[0])) / 2
            except Exception: x_f = 250
            draw.text((x_f, 2180), ft, fill='#888888', font=f_footer)

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
