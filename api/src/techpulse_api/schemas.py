"""Schemas Marshmallow — sérialisation + validation des entrées/sorties."""

from __future__ import annotations

from marshmallow import Schema, fields


# ─── Technology ────────────────────────────────────
class TechnologySchema(Schema):
    canonical_name = fields.Str(metadata={"description": "Clé canonique (python, react…)."})
    display_name = fields.Str(metadata={"description": "Libellé d'affichage (Python, React…)."})
    category = fields.Str(
        metadata={
            "description": "language / framework / database / cloud / tool / library / methodology"
        }
    )


# ─── Offer ─────────────────────────────────────────
class OfferSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str(allow_none=True)
    company_name = fields.Str()
    company_sector = fields.Str(allow_none=True)
    source = fields.Str()
    source_url = fields.Str()
    city = fields.Str(allow_none=True)
    department_code = fields.Str(allow_none=True)
    contract_type = fields.Str(allow_none=True)
    experience_level = fields.Str(allow_none=True)
    salary_min = fields.Int(allow_none=True)
    salary_max = fields.Int(allow_none=True)
    salary_currency = fields.Str()
    posted_at = fields.DateTime(allow_none=True)
    scraped_at = fields.DateTime()
    technologies = fields.List(fields.Nested(TechnologySchema))


class PaginatedOffersSchema(Schema):
    items = fields.List(fields.Nested(OfferSchema))
    total = fields.Int(metadata={"description": "Nombre total d'offres (tous filtres appliqués)."})
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int(metadata={"description": "Nombre total de pages."})


# ─── Query params ──────────────────────────────────
class OffersQueryArgs(Schema):
    page = fields.Int(load_default=1, metadata={"description": "Page (1-indexed)."})
    per_page = fields.Int(load_default=20, metadata={"description": "Offres par page (max 100)."})
    keyword = fields.Str(
        required=False, metadata={"description": "Mot-clé dans titre ou description."}
    )
    city = fields.Str(required=False, metadata={"description": "Ville exacte."})
    tech = fields.Str(
        required=False, metadata={"description": "Canonical name d'une techno (ex: python)."}
    )
    contract = fields.Str(
        required=False, metadata={"description": "Type de contrat (CDI, CDD, Stage…)."}
    )


# ─── Stats ─────────────────────────────────────────
class TopTechItemSchema(Schema):
    name = fields.Str()
    display_name = fields.Str()
    category = fields.Str()
    count = fields.Int()


class SalaryDistributionSchema(Schema):
    count = fields.Int()
    mean = fields.Float(allow_none=True)
    median = fields.Int(allow_none=True)
    p25 = fields.Int(allow_none=True)
    p75 = fields.Int(allow_none=True)
    min = fields.Int(allow_none=True)
    max = fields.Int(allow_none=True)


class CityCountSchema(Schema):
    city = fields.Str()
    department_code = fields.Str(allow_none=True)
    count = fields.Int()


class TimelinePointSchema(Schema):
    date = fields.Date()
    count = fields.Int()


class SourceStatSchema(Schema):
    source = fields.Str()
    count = fields.Int()


# ─── Meta ──────────────────────────────────────────
class HealthSchema(Schema):
    status = fields.Str()
    database = fields.Str()
    offers_count = fields.Int()


class VersionSchema(Schema):
    version = fields.Str()
    scraper_version = fields.Str()
