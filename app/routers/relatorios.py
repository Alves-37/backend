from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db_session
from app.db.models import Produto

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


def _build_produtos_pdf(produtos: List[Produto], titulo: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Spacer(1, 12))

    data = [["Código", "Nome", "Preço venda", "Estoque", "Estoque mín."]]
    for p in produtos:
        data.append([
            p.codigo or "",
            p.nome or "",
            f"MT {p.preco_venda:,.2f}",
            f"{p.estoque}",
            f"{p.estoque_minimo}",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
    ]))

    story.append(table)
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


@router.get("/produtos", response_class=StreamingResponse)
async def relatorio_produtos(baixo_estoque: bool = False, db: AsyncSession = Depends(get_db_session)):
    stmt = select(Produto).where(Produto.ativo == True)
    result = await db.execute(stmt)
    produtos = result.scalars().all()

    if baixo_estoque:
        def is_baixo(p: Produto) -> bool:
            estoque = float(p.estoque or 0)
            minimo = float(p.estoque_minimo or 0)
            return (minimo > 0 and estoque <= minimo) or (minimo <= 0 and estoque <= 5)

        produtos = [p for p in produtos if is_baixo(p)]

    titulo = "Produtos" if not baixo_estoque else "Produtos com baixo estoque"
    pdf_bytes = _build_produtos_pdf(produtos, titulo)

    filename = "produtos.pdf" if not baixo_estoque else "produtos_baixo_estoque.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
