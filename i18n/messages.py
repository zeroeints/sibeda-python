from __future__ import annotations
from typing import Dict

# Katalog pesan multibahasa.
# Key konvensi snake_case.
# Tambah bahasa baru dengan menambahkan kunci top-level (misal 'jp').
# ...existing code...
_MESSAGES: Dict[str, Dict[str, str]] = {
    "id": {
        "login_success": "Login berhasil",
        "invalid_credentials": "NIP atau password salah",
        "not_authenticated": "Tidak terautentikasi",
        "permission_denied": "Tidak punya akses",
        "validation_error": "Data tidak valid",
        "internal_error": "Terjadi kesalahan pada server",
        "user_create_success": "User berhasil dibuat",
        "vehicle_create_success": "Kendaraan berhasil dibuat",
        "vehicle_delete_success": "Kendaraan berhasil dihapus",
        "wallet_delete_success": "Wallet berhasil dihapus",
        "report_create_success": "Laporan berhasil dibuat",
        "report_update_success": "Laporan berhasil diperbarui",
        "report_delete_success": "Laporan berhasil dihapus",
        "create_success": "Data berhasil dibuat",
        "update_success": "Data berhasil diperbarui",
        "delete_success": "Data berhasil dihapus",
        "not_found": "Data tidak ditemukan",
        "duplicate_entry": "Data sudah terdaftar",
    },
    "en": {
        "login_success": "Login successful",
        "invalid_credentials": "Invalid NIP or password",
        "not_authenticated": "Not authenticated",
        "permission_denied": "Permission denied",
        "validation_error": "Validation error",
        "internal_error": "Internal server error",
        "user_create_success": "User created successfully",
        "vehicle_create_success": "Vehicle created successfully",
        "vehicle_delete_success": "Vehicle deleted successfully",
        "wallet_delete_success": "Wallet deleted successfully",
        "report_create_success": "Report created successfully",
        "report_update_success": "Report updated successfully",
        "report_delete_success": "Report deleted successfully",
        "create_success": "Created successfully",
        "update_success": "Updated successfully",
        "delete_success": "Deleted successfully",
        "not_found": "Data not found",
        "duplicate_entry": "Duplicate entry",
    },
    "ja": {
        "login_success": "ログイン成功",
        "invalid_credentials": "NIP またはパスワードが正しくありません",
        "not_authenticated": "認証されていません",
        "permission_denied": "アクセス権がありません",
        "validation_error": "検証エラー",
        "internal_error": "サーバー内部エラー",
        "user_create_success": "ユーザーを作成しました",
        "vehicle_create_success": "車両を作成しました",
        "vehicle_delete_success": "車両を削除しました",
        "wallet_delete_success": "ウォレットを削除しました",
        "report_create_success": "レポートを作成しました",
        "report_update_success": "レポートを更新しました",
        "report_delete_success": "レポートを削除しました",
        "create_success": "作成に成功しました",
        "update_success": "更新に成功しました",
        "delete_success": "削除に成功しました",
        "not_found": "データが見つかりません",
        "duplicate_entry": "重複したデータです",
    },
    "zh": {
        "login_success": "登录成功",
        "invalid_credentials": "NIP或密码错误",
        "not_authenticated": "未认证",
        "permission_denied": "没有访问权限",
        "validation_error": "验证错误",
        "internal_error": "服务器内部错误",
        "user_create_success": "用户创建成功",
        "vehicle_create_success": "车辆创建成功",
        "vehicle_delete_success": "车辆删除成功",
        "wallet_delete_success": "钱包删除成功",
    "report_create_success": "报告创建成功",
    "report_update_success": "报告更新成功",
    "report_delete_success": "报告删除成功",
        "create_success": "创建成功",
        "update_success": "更新成功",
        "delete_success": "删除成功",
        "not_found": "数据未找到",
        "duplicate_entry": "数据已存在",
    },
}
# ...existing code...

DEFAULT_LANG = "id"


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return DEFAULT_LANG
    lang = lang.lower()
    if lang not in _MESSAGES:
        return DEFAULT_LANG
    return lang


def get_message(key: str, lang: str | None = None) -> str:
    lang_code = normalize_lang(lang)
    # fallback ke default bila key tidak ditemukan di bahasa yg dipilih
    return _MESSAGES.get(lang_code, {}).get(key, _MESSAGES[DEFAULT_LANG].get(key, key))


def available_languages() -> list[str]:
    return list(_MESSAGES.keys())
