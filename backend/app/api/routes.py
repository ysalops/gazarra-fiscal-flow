from datetime import datetime

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Query,
    Depends,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, require_admin, ensure_company_access

from app.models.entities import (
    Company,
    Product,
    ProductMapping,
    User,
)

from app.schemas.product import (
    MatchRequest,
    BatchMatchRequest,
    MappingReview,
    CandidateProduct,
)

from app.services.xml_parser import parse_nfe_xml
from app.services.product_matcher import suggest_match
from app.services.iss_repository import search_iss
from app.services.llm.router import get_llm_provider


router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "GAZARRA POC",
    }


# ---------------------------------------------------------
# XML
# ---------------------------------------------------------

@router.post("/xml/preview")
async def xml_preview(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".xml"):
        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo XML.",
        )

    content = await file.read()

    try:
        return parse_nfe_xml(content)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"XML inválido ou não suportado: {exc}",
        )


# ---------------------------------------------------------
# AMBIENTE DEMONSTRATIVO
# ---------------------------------------------------------

@router.post("/demo/setup")
def demo_setup(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    company = db.scalar(
        select(Company).where(
            Company.name == "Cliente Piloto GAZARRA"
        )
    )

    if company is None:
        company = Company(
            name="Cliente Piloto GAZARRA",
            cnpj="00000000000000",
        )

        db.add(company)
        db.commit()
        db.refresh(company)

    products = db.scalars(
        select(Product).where(
            Product.company_id == company.id
        )
    ).all()

    if not products:

        demo_products = [
            Product(
                company_id=company.id,
                internal_code="PRD-001",
                description="Açúcar Cristal 5 KG",
                gtin="7890000000011",
                ncm="17019900",
                unit="UN",
            ),
            Product(
                company_id=company.id,
                internal_code="PRD-002",
                description="Açúcar Refinado 1 KG",
                gtin="7899999999999",
                ncm="17019900",
                unit="UN",
            ),
            Product(
                company_id=company.id,
                internal_code="PRD-003",
                description="Café Torrado e Moído 500 G",
                gtin="7890000000028",
                ncm="09012100",
                unit="UN",
            ),
        ]

        db.add_all(demo_products)
        db.commit()

    return {
        "status": "ok",
        "company_id": company.id,
        "company": company.name,
        "message": "Ambiente demonstrativo criado.",
    }


# ---------------------------------------------------------
# PRODUTOS INTERNOS
# ---------------------------------------------------------

@router.get("/products/{company_id}")
def list_products(
    company_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_company_access(db, user, company_id)

    products = db.scalars(
        select(Product).where(
            Product.company_id == company_id
        )
    ).all()

    return [
        {
            "id": product.id,
            "internal_code": product.internal_code,
            "description": product.description,
            "gtin": product.gtin,
            "ncm": product.ncm,
            "unit": product.unit,
        }
        for product in products
    ]


# ---------------------------------------------------------
# MATCHER INDIVIDUAL
# ---------------------------------------------------------

@router.post("/matcher/suggest")
def matcher_suggest(
    payload: MatchRequest,
    user: User = Depends(get_current_user),
):
    return suggest_match(
        payload.supplier_product,
        payload.candidates,
    )


# ---------------------------------------------------------
# PRODUCT MAPPER EM LOTE
# ---------------------------------------------------------

@router.post("/matcher/batch")
def matcher_batch(
    payload: BatchMatchRequest,
    company_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    ensure_company_access(db, user, company_id)

    products = db.scalars(
        select(Product).where(
            Product.company_id == company_id
        )
    ).all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="Empresa sem produtos internos cadastrados.",
        )

    candidates = [
        CandidateProduct(
            internal_code=p.internal_code,
            description=p.description,
            gtin=p.gtin,
            ncm=p.ncm,
            unit=p.unit,
        )
        for p in products
    ]

    results = []

    for item in payload.items:

        # Primeiro verifica se já existe De/Para homologado.
        existing_mapping = db.scalar(
            select(ProductMapping).where(
                ProductMapping.company_id == company_id,
                ProductMapping.supplier_cnpj
                == payload.supplier_cnpj,
                ProductMapping.supplier_code
                == item.supplier_code,
                ProductMapping.approved.is_(True),
            )
        )

        if existing_mapping:

            target = db.get(
                Product,
                existing_mapping.target_product_id,
            )

            results.append(
                {
                    "mapping_id": existing_mapping.id,
                    "supplier_code": item.supplier_code,
                    "supplier_description": item.description,
                    "internal_product_id": (
                        target.id if target else None
                    ),
                    "internal_code": (
                        target.internal_code if target else None
                    ),
                    "internal_description": (
                        target.description if target else None
                    ),
                    "confidence": 1.0,
                    "status": "homologated",
                    "reasons": [
                        "De/Para previamente homologado"
                    ],
                }
            )

            continue

        suggestion = suggest_match(
            item,
            candidates,
        )

        target = None

        if suggestion.internal_code:

            target = db.scalar(
                select(Product).where(
                    Product.company_id == company_id,
                    Product.internal_code
                    == suggestion.internal_code,
                )
            )

        mapping = ProductMapping(
            company_id=company_id,
            supplier_cnpj=payload.supplier_cnpj,
            supplier_code=item.supplier_code,
            supplier_description=item.description,
            target_product_id=(
                target.id if target else None
            ),
            confidence=suggestion.confidence,
            status=suggestion.status,
            rationale="; ".join(
                suggestion.reasons
            ),
            approved=False,
        )

        db.add(mapping)
        db.commit()
        db.refresh(mapping)

        results.append(
            {
                "mapping_id": mapping.id,
                "supplier_code": item.supplier_code,
                "supplier_description": item.description,
                "internal_product_id": (
                    target.id if target else None
                ),
                "internal_code": (
                    target.internal_code if target else None
                ),
                "internal_description": (
                    target.description if target else None
                ),
                "confidence": suggestion.confidence,
                "status": suggestion.status,
                "reasons": suggestion.reasons,
            }
        )

    return {
        "company_id": company_id,
        "supplier_cnpj": payload.supplier_cnpj,
        "total_items": len(results),
        "items": results,
    }


# ---------------------------------------------------------
# HOMOLOGAÇÃO
# ---------------------------------------------------------

@router.get("/mappings")
def list_mappings(
    company_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_company_access(db, user, company_id)

    mappings = db.scalars(
        select(ProductMapping)
        .where(
            ProductMapping.company_id == company_id
        )
        .order_by(
            ProductMapping.created_at.desc()
        )
    ).all()

    result = []

    for mapping in mappings:

        product = None

        if mapping.target_product_id:
            product = db.get(
                Product,
                mapping.target_product_id,
            )

        result.append(
            {
                "id": mapping.id,
                "supplier_cnpj": mapping.supplier_cnpj,
                "supplier_code": mapping.supplier_code,
                "supplier_description": (
                    mapping.supplier_description
                ),
                "target_product_id": (
                    mapping.target_product_id
                ),
                "internal_code": (
                    product.internal_code
                    if product
                    else None
                ),
                "internal_description": (
                    product.description
                    if product
                    else None
                ),
                "confidence": mapping.confidence,
                "status": mapping.status,
                "approved": mapping.approved,
                "rationale": mapping.rationale,
                "reviewed_by": mapping.reviewed_by,
                "created_at": mapping.created_at,
                "approved_at": mapping.approved_at,
            }
        )

    return result


@router.post("/mappings/{mapping_id}/review")
def review_mapping(
    mapping_id: int,
    payload: MappingReview,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    mapping = db.get(
        ProductMapping,
        mapping_id,
    )

    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail="Mapeamento não encontrado.",
        )

    ensure_company_access(db, user, mapping.company_id)

    if payload.action == "block":

        mapping.approved = False
        mapping.status = "blocked"
        mapping.reviewed_by = payload.reviewed_by

        if payload.rationale:
            mapping.rationale = payload.rationale

        db.commit()

        return {
            "status": "blocked",
            "mapping_id": mapping.id,
        }

    target_product_id = (
        payload.target_product_id
        or mapping.target_product_id
    )

    if target_product_id is None:
        raise HTTPException(
            status_code=400,
            detail="Informe o produto interno.",
        )

    product = db.get(
        Product,
        target_product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Produto interno não encontrado.",
        )

    mapping.target_product_id = product.id
    mapping.approved = True
    mapping.status = "homologated"
    mapping.reviewed_by = payload.reviewed_by
    mapping.approved_at = datetime.utcnow()

    if payload.rationale:
        mapping.rationale = payload.rationale

    db.commit()
    db.refresh(mapping)

    return {
        "status": "homologated",
        "mapping_id": mapping.id,
        "internal_product_id": product.id,
        "internal_code": product.internal_code,
        "internal_description": product.description,
    }


# ---------------------------------------------------------
# ISS
# ---------------------------------------------------------

@router.get("/iss/search")
def iss_search(
    municipio: str | None = Query(default=None),
    uf: str | None = Query(default=None),
    codigo: str | None = Query(default=None),
    user: User = Depends(get_current_user),
):

    return {
        "source": (
            "Base local de demonstração — "
            "substituir pela fonte oficial no piloto"
        ),
        "items": search_iss(
            municipio=municipio,
            uf=uf,
            codigo=codigo,
        ),
    }


# ---------------------------------------------------------
# IA - ainda opcional
# ---------------------------------------------------------

@router.post("/ai/explain-match")
def explain_match(
    payload: MatchRequest,
    user: User = Depends(get_current_user),
):

    suggestion = suggest_match(
        payload.supplier_product,
        payload.candidates,
    )

    provider = get_llm_provider()

    if provider is None:

        return {
            "mode": "rules_only",
            "suggestion": suggestion,
            "explanation": (
                "LLM desabilitada. "
                "A sugestão foi produzida "
                "apenas pelas regras da POC."
            ),
        }

    system_prompt = (
        "Você é um assistente interno de "
        "homologação de produtos. "
        "Não invente dados. "
        "Explique somente os critérios fornecidos "
        "e destaque incertezas."
    )

    user_prompt = (
        f"Produto fornecedor: "
        f"{payload.supplier_product.model_dump()}\n"
        f"Sugestão calculada: "
        f"{suggestion.model_dump()}\n"
        "Explique brevemente se a sugestão "
        "deve ser aprovada, revisada ou bloqueada."
    )

    explanation = provider.analyze(
        system_prompt,
        user_prompt,
    )

    return {
        "mode": "llm_assisted",
        "suggestion": suggestion,
        "explanation": explanation,
    }