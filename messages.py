"""
messages.py — загрузчик пакета копирайта по активному бренду
=============================================================

Тексты (голос персонажа) — это контент, а не конфиг, поэтому каждый бренд
держит свой пакет: copy_metaplay.py, copy_goalcast.py, …

Этот модуль выбирает нужный пакет по полю BRAND.copy_pack и реэкспортит из
него все имена. Поэтому существующий код продолжает писать просто
    from messages import HOOK_CAPTION, BRIDGE, CTA_REGISTER, ...
и ничего не меняется при добавлении нового бренда.

Добавить голос нового бренда:
    1) создать copy_<brand>.py с теми же именами (см. copy_metaplay.py как образец)
    2) указать copy_pack="copy_<brand>" в brand.py
"""
import importlib

from brand import BRAND

# Дефолт на случай пустого/неверного значения.
_pack_name = BRAND.copy_pack or "copy_metaplay"

try:
    _pack = importlib.import_module(_pack_name)
except ModuleNotFoundError as e:
    raise RuntimeError(
        f"Copy pack '{_pack_name}' not found for brand '{BRAND.id}'. "
        f"Create {_pack_name}.py (use copy_metaplay.py as a template)."
    ) from e

# Реэкспорт всех публичных имён пакета в пространство messages.*
globals().update({k: v for k, v in vars(_pack).items() if not k.startswith("_")})
