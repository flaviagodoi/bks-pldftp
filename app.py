import streamlit as st
import io, os, re, unicodedata, requests, csv
from datetime import datetime, timezone, timedelta
from PIL import Image as PILImage

# ReportLab - Gerador Vetorial Profissional de PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# -----------------------------------------------------------------------------
# 📅 GESTÃO DE EXPIRAÇÃO DA BASE DE DADOS INTERNA (30 DIAS)
# -----------------------------------------------------------------------------
# Data fixa da inclusão da base (Sexta-feira, 14/08/2026)
DATA_INCLUSAO_BASE = datetime(2026, 8, 14)
VALIDADE_DIAS = 30

def verificar_validade_base():
    hoje = datetime.now()
    dias_decorridos = (hoje - DATA_INCLUSAO_BASE).days
    dias_restantes = VALIDADE_DIAS - dias_decorridos
    
    if dias_decorridos >= VALIDADE_DIAS:
        st.error(f"⚠️ **ATENÇÃO:** A base de dados interna expirou! (Incluída em {DATA_INCLUSAO_BASE.strftime('%d/%m/%Y')} - Há {dias_decorridos} dias). É necessário atualizá-la.")
    elif dias_restantes <= 5:
        st.warning(f"⏰ **LEMBRETE DE ATUALIZAÇÃO:** A base de dados vence em {dias_restantes} dia(s) ({DATA_INCLUSAO_BASE.strftime('%d/%m/%Y')}).")
    else:
        st.info(f"ℹ️ **Base Interna:** Incluída em {DATA_INCLUSAO_BASE.strftime('%d/%m/%Y')} (Válida por mais {dias_restantes} dias).")

# -----------------------------------------------------------------------------
# 🛠️ FUNÇÕES AUXILIARES, VALIDAÇÃO DE CPF E BUSCA LOCAL
# -----------------------------------------------------------------------------
def normalizar_texto(txt):
    """Remove acentos, caracteres especiais e converte para caixa baixa e espaços simples."""
    if not txt:
        return ""
    nfkd = unicodedata.normalize('NFD', str(txt))
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    limpo = re.sub(r'[^a-zA-Z0-9\s]', ' ', sem_acento).lower()
    return " ".join(limpo.split())

def validar_cpf(cpf: str) -> bool:
    """Valida o cálculo dos dígitos verificadores do CPF (Módulo 11)."""
    cpf = ''.join(filter(str.isdigit, str(cpf)))
    
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito_1 = 0 if resto == 10 else resto
    if digito_1 != int(cpf[9]):
        return False
        
    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito_2 = 0 if resto == 10 else resto
    if digito_2 != int(cpf[10]):
        return False
        
    return True

def identificar_arquivo_pep():
    """Localiza o arquivo da planilha de PEPs no diretório."""
    for arq in ["pep_oficial.csv", "pep_oficial.txt", "pep_oficial.csv.csv", "PEP_OFICIAL.csv", "PEP_OFICIAL.txt"]:
        if os.path.exists(arq):
            return arq
    try:
        for arq in os.listdir("."):
            nome_baixo = arq.lower()
            if "pep" in nome_baixo and (nome_baixo.endswith(".csv") or nome_baixo.endswith(".txt")):
                return arq
    except Exception:
        pass
    return None

# -----------------------------------------------------------------------------
# 📄 GERAÇÃO DE RELATÓRIO PDF (REPORTLAB)
# -----------------------------------------------------------------------------
def gerar_relatorio_pdf(nome_pesquisado, cpf_pesquisado, cpf_valido, pep_encontrado, detalhes_pep=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    # Estilos customizados
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        alignment=TA_LEFT,
        fontName="Helvetica-Bold"
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        fontName="Helvetica"
    )

    status_cpf_str = "Válido" if cpf_valido else "Inválido"

    # Cabeçalho do Relatório
    story.append(Paragraph("<b>PORTAL BKS - CONSULTA DE CONFORMIDADE PLDFTP</b>", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Data da Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", body_style))
    story.append(Paragraph(f"<b>Base de Dados Atualizada em:</b> {DATA_INCLUSAO_BASE.strftime('%d/%m/%Y')}", body_style))
    story.append(Spacer(1, 15))

    # Tabela de Dados Analisados
    dados_tabela = [
        [Paragraph("<b>Parâmetro</b>", body_style), Paragraph("<b>Resultado</b>", body_style)],
        [Paragraph("Nome Pesquisado", body_style), Paragraph(nome_pesquisado.upper(), body_style)],
        [Paragraph("CPF Informado", body_style), Paragraph(cpf_pesquisado, body_style)],
        [Paragraph("Status Estrutural do CPF", body_style), Paragraph(f"<b>{status_cpf_str}</b>", body_style)],
        [Paragraph("Consta na Base PEP/SULIFT", body_style), Paragraph("<b>SIM</b>" if pep_encontrado else "<b>NÃO</b>", body_style)]
    ]

    t = Table(dados_tabela, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#E2E8F0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    if detalhes_pep:
        story.append(Paragraph("<b>Detalhes do Registro Localizado:</b>", title_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(str(detalhes_pep), body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------------------------
# 💻 INTERFACE STREAMLIT
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="PLDFTP - BKS Corretora", page_icon="🛡️", layout="wide")
    
    # -------------------------------------------------------------------------
    # 🔗 BARRA LATERAL (SIDEBAR) - LINKS DA RECEITA FEDERAL E UTILITÁRIOS
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.header("🔗 Links Úteis da Receita Federal")
        st.markdown("""
        Caso necessite realizar uma validação cadastral formal em tempo real junto aos órgãos governamentais:
        """)
        
        st.markdown("""
        * 🏛️ [Comprovante de Situação Cadastral CPF](https://servicos.receita.fazenda.gov.br/servicos/cpf/consultasituacao/consultapublica.asp)
        * 📄 [Consulta CNPJ (Receita Federal)](https://solucoes.receita.fazenda.gov.br/servicos/cnpjreva/cnpjreva_solicitacao.asp)
        * 🔍 [Consulta Consolidada PEP (Portal da Transparência)](https://portaldatransparencia.gov.br/busca)
        * ⚖️ [Certidão Negativa de Debitos (CND)](https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/PB/Consultar/)
        """)
        
        st.markdown("---")
        st.caption("BKS Corretora de Seguros — Sistema PLDFTP")

    # -------------------------------------------------------------------------
    # CORPO PRINCIPAL
    # -------------------------------------------------------------------------
    st.title("🛡️ Portal Interno PLDFTP - BKS")
    st.caption("Verificação de Pessoas Expostas Politicamente (PEP) e Validação de Cadastro")

    # Exibe o status e aviso de expiração de 30 dias da base de dados
    verificar_validade_base()

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        nome_input = st.text_input("Nome Completo:", placeholder="Ex: João da Silva")
    with col2:
        cpf_input = st.text_input("CPF (Apenas números ou formatado):", placeholder="000.000.000-00")

    if st.button("🔍 Realizar Consulta", type="primary"):
        if not nome_input or not cpf_input:
            st.warning("Por favor, preencha o Nome e o CPF para realizar a busca.")
            return

        # 1. Validação Algorítmica do CPF
        eh_valido = validar_cpf(cpf_input)
        
        st.subheader("Resultado da Análise")
        
        if eh_valido:
            st.success("✅ **Status do CPF:** Válido")
        else:
            st.error("❌ **Status do CPF:** Inválido (Dígitos verificadores incorretos)")

        # 2. Busca na Base PEP Local
        arquivo_pep = identificar_arquivo_pep()
        encontrado = False
        detalhes = ""

        if arquivo_pep:
            nome_busca = normalizar_texto(nome_input)
            try:
                with open(arquivo_pep, mode='r', encoding='utf-8', errors='ignore') as f:
                    leitor = csv.reader(f)
                    for linha in leitor:
                        linha_str = " ".join(linha)
                        if nome_busca in normalizar_texto(linha_str):
                            encontrado = True
                            detalhes = linha_str
                            break
            except Exception as e:
                st.error(f"Erro ao ler a base de dados interna: {e}")

        if encontrado:
            st.warning("⚠️ **Alerta:** Registro localizado na base de PEP/SULIFT interna!")
        else:
            st.info("ℹ️ Nenhum apontamento de PEP localizado na base interna.")

        # 3. Gerador de Relatório PDF
        pdf_buffer = gerar_relatorio_pdf(
            nome_pesquisado=nome_input,
            cpf_pesquisado=cpf_input,
            cpf_valido=eh_valido,
            pep_encontrado=encontrado,
            detalhes_pep=detalhes if encontrado else None
        )

        st.markdown("---")
        st.download_button(
            label="📄 Baixar Relatório em PDF",
            data=pdf_buffer,
            file_name=f"Relatorio_PLDFTP_{re.sub(r'\D', '', cpf_input)}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
