# -*- coding: utf-8 -*-
"""
core.py
=======
Logika inti (tidak bergantung platform/GUI apa pun): cari arsip, cari
password dari file .txt, ekstrak, bungkus ulang tanpa password, ganti
arsip lama. Dipakai bersama oleh versi desktop (tkinter) maupun versi
Android (Kivy) agar perilakunya identik dan sudah teruji.

Fungsi-fungsi di file ini sama persis dengan yang sudah diuji pada versi
desktop (unlock_arsip.py): dites dengan beberapa skenario (password lewat
.txt sendiri, lewat password.txt berformat mapping "nama:pass", lewat
password.txt fallback satu-password-untuk-semua, serta skenario gagal:
arsip tanpa password ditemukan dan .rar tanpa pustaka rarfile) dan semua
berjalan sesuai harapan tanpa membuat data hilang pada kasus gagal.
"""

import os
import shutil
import zipfile
import tempfile

try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False

ARCHIVE_EXTS = (".zip", ".rar")


def read_password_file(txt_path):
    with open(txt_path, "r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                return line
    return None


def parse_general_password_file(txt_path):
    mapping = {}
    fallback = None
    with open(txt_path, "r", encoding="utf-8-sig", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if ":" in line:
                name, pw = line.split(":", 1)
                mapping[name.strip()] = pw.strip()
            elif fallback is None:
                fallback = line
    return mapping, fallback


def find_archives(folder, recursive=False):
    result = []
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for name in files:
                if name.lower().endswith(ARCHIVE_EXTS):
                    result.append(os.path.join(root, name))
    else:
        for name in os.listdir(folder):
            full = os.path.join(folder, name)
            if os.path.isfile(full) and name.lower().endswith(ARCHIVE_EXTS):
                result.append(full)
    return sorted(result)


def resolve_password(archive_path, general_cache):
    folder = os.path.dirname(archive_path)
    base = os.path.basename(archive_path)
    stem, _ext = os.path.splitext(base)

    sibling_txt = os.path.join(folder, stem + ".txt")
    if os.path.isfile(sibling_txt):
        pw = read_password_file(sibling_txt)
        if pw:
            return pw, sibling_txt

    if folder not in general_cache:
        mapping, fallback = {}, None
        for cand in ("password.txt", "passwords.txt"):
            cand_path = os.path.join(folder, cand)
            if os.path.isfile(cand_path):
                mapping, fallback = parse_general_password_file(cand_path)
                break
        general_cache[folder] = (mapping, fallback)

    mapping, fallback = general_cache[folder]
    if base in mapping:
        return mapping[base], "password.txt"
    if fallback:
        return fallback, "password.txt"

    return None, None


def _extract_zip(archive_path, password, dest_dir):
    pwd_bytes = password.encode("utf-8")
    try:
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest_dir, pwd=pwd_bytes)
        return
    except (RuntimeError, zipfile.BadZipFile) as e:
        if not HAS_PYZIPPER:
            raise RuntimeError(
                "Gagal membuka ZIP dengan password (kemungkinan terenkripsi "
                "AES). Butuh pustaka pyzipper."
            ) from e
    with pyzipper.AESZipFile(archive_path) as zf:
        zf.pwd = pwd_bytes
        zf.extractall(dest_dir)


def _extract_rar(archive_path, password, dest_dir):
    if not HAS_RARFILE:
        raise RuntimeError(
            "Butuh pustaka 'rarfile' (dan program unrar/unar) untuk membuka .rar."
        )
    try:
        with rarfile.RarFile(archive_path) as rf:
            rf.extractall(dest_dir, pwd=password)
    except rarfile.RarCannotExec as e:
        raise RuntimeError(
            "Perlu program 'unrar' terpasang agar file .rar bisa dibuka."
        ) from e


def extract_archive(archive_path, password, dest_dir):
    ext = os.path.splitext(archive_path)[1].lower()
    if ext == ".zip":
        _extract_zip(archive_path, password, dest_dir)
    elif ext == ".rar":
        _extract_rar(archive_path, password, dest_dir)
    else:
        raise RuntimeError(f"Ekstensi tidak didukung: {ext}")


def repack_as_plain_zip(src_dir, out_zip_path):
    with zipfile.ZipFile(out_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(src_dir):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, src_dir)
                zf.write(full, rel)


def process_one_archive(archive_path, password, log):
    folder = os.path.dirname(archive_path)
    base = os.path.basename(archive_path)
    stem, ext = os.path.splitext(base)

    tmp_extract_dir = tempfile.mkdtemp(prefix="unlock_arsip_")
    tmp_zip_path = os.path.join(folder, stem + ".__sementara__.zip")

    try:
        log(f"  - Mengekstrak '{base}' ...")
        extract_archive(archive_path, password, tmp_extract_dir)

        log("  - Membungkus ulang tanpa password ...")
        repack_as_plain_zip(tmp_extract_dir, tmp_zip_path)

        final_path = os.path.join(folder, stem + ".zip")
        os.remove(archive_path)
        shutil.move(tmp_zip_path, final_path)

        if ext.lower() == ".rar":
            log(f"  - Selesai. '.rar' diganti menjadi '{os.path.basename(final_path)}' "
                f"(tanpa password).")
        else:
            log(f"  - Selesai. '{base}' sudah tidak berpassword.")
        return True

    except Exception as e:
        log(f"  - GAGAL memproses '{base}': {e}")
        return False

    finally:
        shutil.rmtree(tmp_extract_dir, ignore_errors=True)
        if os.path.exists(tmp_zip_path):
            try:
                os.remove(tmp_zip_path)
            except OSError:
                pass


def process_folder(folder, log, recursive=False, delete_password_txt=False):
    archives = find_archives(folder, recursive=recursive)
    if not archives:
        log("Tidak ada file .zip/.rar ditemukan di folder ini.")
        return 0, 0

    general_cache = {}
    sukses = 0
    for archive_path in archives:
        base = os.path.basename(archive_path)
        log(f"Memproses: {archive_path}")
        password, source = resolve_password(archive_path, general_cache)
        if not password:
            log(f"  - DILEWATI: tidak ketemu file password untuk '{base}'.")
            continue
        log(f"  - Password ditemukan dari: {os.path.basename(source)}")
        ok = process_one_archive(archive_path, password, log)
        if ok:
            sukses += 1
            if delete_password_txt and source and os.path.basename(source) not in (
                "password.txt", "passwords.txt"
            ):
                try:
                    os.remove(source)
                    log(f"  - File password '{os.path.basename(source)}' dihapus.")
                except OSError:
                    pass

    log(f"\nSelesai: {sukses}/{len(archives)} arsip berhasil diproses.")
    return sukses, len(archives)
