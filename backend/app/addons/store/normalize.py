from .models import CatalogAddon


def normalize_catalog_entry(addon: CatalogAddon) -> CatalogAddon:
    """
    Normalize a catalog addon entry so the rest of the system
    never has to care about missing defaults.
    """

    # Defaults
    if addon.ref is None:
        addon.ref = "main"

    if addon.path is None:
        addon.path = "."

    # Basic security guard
    if ".." in addon.path.replace("\\", "/"):
        raise ValueError(f"Invalid addon path: {addon.path}")

    return addon
