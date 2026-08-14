import re

from app.models import ModelFamily, ModelVersion, ProductType


DRUM_TYPE_ALIAS_MAP = {
    "原生滚筒": "原生滚筒",
    "干燥滚筒": "原生滚筒",
    "再生滚筒": "再生滚筒",
    "全再生滚筒": "再生滚筒",
    "干混滚筒": "干混滚筒",
    "双回程干燥滚筒": "干混滚筒",
}

DRUM_TYPE_SORT_ORDER = {
    "原生滚筒": 10,
    "再生滚筒": 20,
    "干混滚筒": 30,
}

DRUM_FAMILY_CATEGORY_MAP = {
    "AT": "原生滚筒",
    "GT": "原生滚筒",
    "RT": "再生滚筒",
    "GTR": "再生滚筒",
    "GTRS": "再生滚筒",
    "GTRQ": "再生滚筒",
    "HT": "再生滚筒",
    "HTS": "再生滚筒",
    "CT": "干混滚筒",
    "CTD": "干混滚筒",
    "GFT": "干混滚筒",
}

DRUM_FAMILY_CAPACITY_MAP = {
    "AT": [120, 160, 240, 320, 400],
    "GT": [120, 160, 240, 320, 400],
    "RT": [80, 130, 200, 300],
    "GTR": [80, 130, 200, 300],
    "HTS": [80, 130, 200, 300],
    "GFT": [30, 50, 70, 100],
    "CT": [30, 50, 70, 100],
}


class DrumCatalogError(ValueError):
    pass


def normalize_drum_type_name(raw_name):
    name = str(raw_name or "").strip()
    if not name:
        raise DrumCatalogError("分类名称不能为空")
    if "干混" in name or "双回程" in name:
        return "干混滚筒"
    if "再生" in name:
        return "再生滚筒"
    if "原生" in name or "干燥" in name:
        return "原生滚筒"
    return DRUM_TYPE_ALIAS_MAP.get(name, name)


def _normalize_drum_category(raw_name):
    name = str(raw_name or "").strip()
    if not name:
        return None
    normalized = normalize_drum_type_name(name)
    if normalized in DRUM_TYPE_SORT_ORDER:
        return normalized
    return None


def _category_from_code(raw_code):
    code = str(raw_code or "").strip().upper()
    if not code:
        return None
    match = re.match(r"^([A-Z]+)", code)
    prefix = match.group(1) if match else code
    for family_code, category in sorted(DRUM_FAMILY_CATEGORY_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if prefix.startswith(family_code):
            return category
    return None


def _resolve_product_type_category(product_type, families):
    category = _normalize_drum_category(product_type.get("category"))
    if category:
        return category

    alias_keywords = str(product_type.get("alias_keywords") or "").strip()
    if alias_keywords:
        for keyword in re.split(r"[\s,，/、]+", alias_keywords):
            category = _normalize_drum_category(keyword)
            if category:
                return category

    for field in ("type_name", "model_code", "type_code"):
        category = _normalize_drum_category(product_type.get(field))
        if category:
            return category
        category = _category_from_code(product_type.get(field))
        if category:
            return category

    for family in families:
        category = _category_from_code(family.get("family_code"))
        if category:
            return category

    # 兜底折叠到原生，避免历史脏数据在工作台顶层散落成多个分类。
    return "原生滚筒"


def _resolve_drum_seed_category(product_type):
    category = _normalize_drum_category(product_type.get("category"))
    if category:
        return category

    alias_keywords = str(product_type.get("alias_keywords") or "").strip()
    if alias_keywords:
        for keyword in re.split(r"[\s,，/、]+", alias_keywords):
            category = _normalize_drum_category(keyword)
            if category:
                return category

    for field in ("type_name", "model_code", "type_code"):
        category = _normalize_drum_category(product_type.get(field))
        if category:
            return category
        category = _category_from_code(product_type.get(field))
        if category:
            return category
    return None


def _normalize_catalog_code(raw_code):
    code = str(raw_code or "").strip().upper()
    return code or None


def _derive_family_code(raw_code):
    code = _normalize_catalog_code(raw_code)
    if not code:
        return None
    match = re.match(r"^([A-Z]+)", code)
    return match.group(1) if match else None


def _extract_capacity_value(raw_code):
    code = _normalize_catalog_code(raw_code)
    if not code:
        return None
    match = re.search(r"(\d+)", code)
    return int(match.group(1)) if match else None


def _build_capacity_options(family_code):
    capacities = DRUM_FAMILY_CAPACITY_MAP.get(str(family_code or "").strip().upper())
    if not capacities:
        return None
    return ",".join(str(item) for item in capacities)


def plan_drum_catalog_sync(product_types=None, families=None, versions=None):
    family_rows = list(families or [])
    version_rows = list(versions or [])
    families_by_code = {}
    family_id_to_code = {}
    versions_by_family_code = {}

    for family in family_rows:
        family_code = _normalize_catalog_code(family.get("family_code"))
        if not family_code or family_code in families_by_code:
            continue
        families_by_code[family_code] = family
        family_id_to_code[family.get("id")] = family_code

    for version in version_rows:
        family_code = family_id_to_code.get(version.get("family_id"))
        version_code = _normalize_catalog_code(version.get("version_code"))
        if not family_code or not version_code:
            continue
        versions_by_family_code.setdefault(family_code, set()).add(version_code)

    create_families = []
    update_families = []
    create_versions = []
    planned_family_codes = set()
    planned_version_codes = {}
    planned_update_ids = set()

    for product_type in sorted(list(product_types or []), key=lambda item: item.get("id", 0)):
        category = _resolve_drum_seed_category(product_type)
        model_code = _normalize_catalog_code(product_type.get("model_code") or product_type.get("type_code"))
        family_code = _derive_family_code(model_code)
        if not category or not model_code or not family_code:
            continue

        capacity_options = _build_capacity_options(family_code)
        family = families_by_code.get(family_code)
        if not family and family_code not in planned_family_codes:
            create_families.append(
                {
                    "family_code": family_code,
                    "family_name": category,
                    "category": category,
                    "capacity_options": capacity_options,
                    "product_type_id": product_type["id"],
                }
            )
            planned_family_codes.add(family_code)
        elif family and not family.get("product_type_id") and family.get("id") not in planned_update_ids:
            update_families.append(
                {
                    "id": family["id"],
                    "product_type_id": product_type["id"],
                    "family_name": category,
                    "category": category,
                    "capacity_options": capacity_options,
                }
            )
            planned_update_ids.add(family["id"])

        existing_codes = set(versions_by_family_code.get(family_code, set()))
        existing_codes.update(planned_version_codes.get(family_code, set()))
        if model_code not in existing_codes:
            create_versions.append(
                {
                    "family_code": family_code,
                    "version_code": model_code,
                    "capacity_value": _extract_capacity_value(model_code),
                    "display_name": model_code,
                }
            )
            planned_version_codes.setdefault(family_code, set()).add(model_code)

    return {
        "create_families": create_families,
        "update_families": update_families,
        "create_versions": create_versions,
    }


def _sync_drum_catalog_from_product_types(db):
    product_types = (
        db.query(ProductType)
        .order_by(ProductType.sort_order.asc(), ProductType.id.asc())
        .all()
    )
    families = db.query(ModelFamily).order_by(ModelFamily.id.asc()).all()
    versions = db.query(ModelVersion).order_by(ModelVersion.id.asc()).all()
    plan = plan_drum_catalog_sync(
        product_types=[
            {
                "id": item.id,
                "type_name": item.type_name,
                "category": item.category,
                "alias_keywords": item.alias_keywords,
                "model_code": item.model_code,
                "type_code": item.type_code,
            }
            for item in product_types
        ],
        families=[
            {
                "id": item.id,
                "family_code": item.family_code,
                "family_name": item.family_name,
                "category": item.category,
                "capacity_options": item.capacity_options,
                "product_type_id": item.product_type_id,
            }
            for item in families
        ],
        versions=[
            {
                "id": item.id,
                "family_id": item.family_id,
                "version_code": item.version_code,
            }
            for item in versions
        ],
    )
    if not plan["create_families"] and not plan["update_families"] and not plan["create_versions"]:
        return

    families_by_id = {item.id: item for item in families}
    families_by_code = {_normalize_catalog_code(item.family_code): item for item in families}
    version_keys = {
        (item.family_id, _normalize_catalog_code(item.version_code))
        for item in versions
    }
    changed = False

    for row in plan["update_families"]:
        family = families_by_id.get(row["id"])
        if not family:
            continue
        if family.product_type_id is None:
            family.product_type_id = row["product_type_id"]
            changed = True
        if not family.family_name and row.get("family_name"):
            family.family_name = row["family_name"]
            changed = True
        if not family.category and row.get("category"):
            family.category = row["category"]
            changed = True
        if family.capacity_options is None and row.get("capacity_options"):
            family.capacity_options = row["capacity_options"]
            changed = True

    for row in plan["create_families"]:
        family = ModelFamily(
            family_code=row["family_code"],
            family_name=row["family_name"],
            category=row["category"],
            capacity_options=row["capacity_options"],
            product_type_id=row["product_type_id"],
            sort_order=DRUM_TYPE_SORT_ORDER.get(row["category"], 999),
        )
        db.add(family)
        db.flush()
        families_by_id[family.id] = family
        families_by_code[_normalize_catalog_code(family.family_code)] = family
        changed = True

    for row in plan["create_versions"]:
        family = families_by_code.get(row["family_code"])
        if not family:
            continue
        version_key = (family.id, _normalize_catalog_code(row["version_code"]))
        if version_key in version_keys:
            continue
        db.add(
            ModelVersion(
                family_id=family.id,
                version_code=row["version_code"],
                capacity_value=row["capacity_value"],
                display_name=row["display_name"],
                status="active",
                created_by="system-sync",
            )
        )
        version_keys.add(version_key)
        changed = True

    if changed:
        db.commit()


def build_version_codes(family_code):
    code = str(family_code or "").strip().upper()
    capacities = DRUM_FAMILY_CAPACITY_MAP.get(code)
    if not capacities:
        raise DrumCatalogError(f"未知系列: {code}")
    return [f"{code}{capacity}" for capacity in capacities]


def build_family_version_rows(family_id, family_code, existing_codes=None):
    existing = {str(code).strip().upper() for code in (existing_codes or set())}
    rows = []
    for capacity in DRUM_FAMILY_CAPACITY_MAP.get(str(family_code or "").strip().upper(), []):
        version_code = f"{str(family_code).strip().upper()}{capacity}"
        if version_code in existing:
            continue
        rows.append({
            "family_id": int(family_id),
            "version_code": version_code,
            "capacity_value": capacity,
        })
    return rows


def build_drum_tree_payload(product_types=None, families=None, versions=None):
    type_rows = sorted(
        list(product_types or []),
        key=lambda item: (DRUM_TYPE_SORT_ORDER.get(item.get("type_name"), 999), item.get("id", 0)),
    )
    family_rows = list(families or [])
    version_rows = list(versions or [])
    versions_by_family = {}
    for version in version_rows:
        versions_by_family.setdefault(version["family_id"], []).append({
            "id": version["id"],
            "version_code": version["version_code"],
            "capacity_value": version.get("capacity_value"),
            "display_name": version.get("display_name"),
        })
    families_by_type = {}
    for family in family_rows:
        families_by_type.setdefault(family["product_type_id"], []).append({
            "id": family["id"],
            "family_code": family["family_code"],
            "family_name": family.get("family_name"),
            "capacity_options": family.get("capacity_options"),
            "versions": sorted(
                versions_by_family.get(family["id"], []),
                key=lambda item: (item.get("capacity_value") or 0, item["version_code"]),
            ),
        })
    grouped_types = {}
    for product_type in type_rows:
        family_items = sorted(
            families_by_type.get(product_type["id"], []),
            key=lambda item: item["family_code"],
        )
        category_name = _resolve_product_type_category(product_type, family_items)
        bucket = grouped_types.setdefault(
            category_name,
            {
                "id": product_type["id"],
                "type_name": category_name,
                "alias_keywords": product_type.get("alias_keywords"),
                "families": [],
            },
        )
        bucket["id"] = min(bucket["id"], product_type["id"])
        if not bucket.get("alias_keywords") and product_type.get("alias_keywords"):
            bucket["alias_keywords"] = product_type.get("alias_keywords")
        for family in family_items:
            existing_family = next(
                (item for item in bucket["families"] if item["family_code"] == family["family_code"]),
                None,
            )
            if not existing_family:
                bucket["families"].append(family)
                continue

            existing_versions = {item["version_code"]: item for item in existing_family["versions"]}
            for version in family["versions"]:
                existing_versions.setdefault(version["version_code"], version)
            existing_family["versions"] = sorted(
                existing_versions.values(),
                key=lambda item: (item.get("capacity_value") or 0, item["version_code"]),
            )

    return [
        {
            **item,
            "families": sorted(item["families"], key=lambda family: family["family_code"]),
        }
        for item in sorted(
            grouped_types.values(),
            key=lambda item: (DRUM_TYPE_SORT_ORDER.get(item["type_name"], 999), item["id"]),
        )
    ]


def build_drum_tree(db):
    _sync_drum_catalog_from_product_types(db)

    product_types = (
        db.query(ProductType)
        .order_by(ProductType.sort_order.asc(), ProductType.id.asc())
        .all()
    )
    drum_product_types = [
        item
        for item in product_types
        if _resolve_drum_seed_category(
            {
                "id": item.id,
                "type_name": item.type_name,
                "category": item.category,
                "alias_keywords": item.alias_keywords,
                "model_code": item.model_code,
                "type_code": item.type_code,
            }
        )
    ]
    drum_product_type_ids = [item.id for item in drum_product_types]
    families = (
        db.query(ModelFamily)
        .filter(ModelFamily.product_type_id.in_(drum_product_type_ids))
        .order_by(ModelFamily.sort_order.asc(), ModelFamily.family_code.asc())
        .all()
        if drum_product_type_ids
        else []
    )
    family_ids = [item.id for item in families]
    versions = (
        db.query(ModelVersion)
        .filter(ModelVersion.family_id.in_(family_ids))
        .order_by(ModelVersion.capacity_value.asc(), ModelVersion.version_code.asc(), ModelVersion.id.asc())
        .all()
        if family_ids
        else []
    )
    return build_drum_tree_payload(
        product_types=[
            {
                "id": item.id,
                "type_name": item.type_name,
                "category": item.category,
                "alias_keywords": item.alias_keywords,
                "model_code": item.model_code,
                "type_code": item.type_code,
            }
            for item in drum_product_types
        ],
        families=[
            {
                "id": item.id,
                "product_type_id": item.product_type_id,
                "family_code": item.family_code,
                "family_name": item.family_name,
                "capacity_options": item.capacity_options,
            }
            for item in families
        ],
        versions=[
            {
                "id": item.id,
                "family_id": item.family_id,
                "version_code": item.version_code,
                "capacity_value": item.capacity_value,
                "display_name": item.display_name,
            }
            for item in versions
        ],
    )


def create_family_versions(db, family_id):
    family = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not family:
        raise DrumCatalogError("系列不存在")
    family_code = str(family.family_code or "").strip().upper()
    if family_code not in DRUM_FAMILY_CAPACITY_MAP:
        raise DrumCatalogError(f"系列 {family_code} 未配置产量档位")
    existing_codes = {
        row.version_code.strip().upper()
        for row in db.query(ModelVersion).filter(ModelVersion.family_id == family_id).all()
    }
    rows = build_family_version_rows(family_id, family_code, existing_codes)
    created_versions = []
    for row in rows:
        version = ModelVersion(
            family_id=row["family_id"],
            version_code=row["version_code"],
            capacity_value=row["capacity_value"],
            display_name=row["version_code"],
            status="active",
            created_by="system",
        )
        db.add(version)
        created_versions.append(version)
    if family.capacity_options is None:
        family.capacity_options = ",".join(str(item) for item in DRUM_FAMILY_CAPACITY_MAP[family_code])
    db.commit()
    for version in created_versions:
        db.refresh(version)
    return {
        "family_id": family_id,
        "created_count": len(created_versions),
        "versions": [
            {
                "id": version.id,
                "version_code": version.version_code,
                "capacity_value": version.capacity_value,
                "display_name": version.display_name,
            }
            for version in created_versions
        ],
    }
