# -*- coding: utf-8 -*-
"""
main.py — Tampilan Android (Kivy) untuk Unlock Arsip.

PENTING, JUJUR DI AWAL:
File ini TIDAK bisa saya jalankan/uji di lingkungan chat saya (sandbox ini
tidak punya akses ke PyPI untuk install Kivy, dan juga tidak punya akses
ke Android SDK/NDK untuk build). Jadi berbeda dengan core.py (logika
ekstrak/ganti password) yang SUDAH saya uji nyata dan terbukti jalan,
bagian antarmuka Android di file ini ditulis berdasarkan pola baku yang
umum dipakai komunitas Kivy/python-for-android untuk minta izin
penyimpanan & menjalankan proses di background thread, TAPI belum
pernah benar-benar saya jalankan. Kalau pas dicoba di HP ada error,
kirim pesan errornya (bisa dilihat lewat `adb logcat` atau lewat
tombol "Lihat Log" di GitHub Actions) ke saya, nanti saya perbaiki.
"""

import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.properties import StringProperty

import core

DEFAULT_FOLDER = "/storage/emulated/0/Download"


def minta_izin_penyimpanan():
    """
    Minta izin akses penyimpanan di Android. Dibungkus try/except penuh
    supaya kalau dijalankan di luar Android (atau ada API yang berubah
    di versi Android tertentu) tidak membuat app crash saat start.
    """
    try:
        from jnius import autoclass  # noqa: F401
    except Exception:
        return  # bukan di Android (atau pyjnius belum siap) -> lewati saja

    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
        ])
    except Exception:
        pass

    # Android 11+ (API 30+) butuh izin "All files access" terpisah,
    # tidak cukup lewat request_permissions biasa.
    try:
        from jnius import autoclass, cast
        Build_VERSION = autoclass('android.os.Build$VERSION')
        if Build_VERSION.SDK_INT >= 30:
            Environment = autoclass('android.os.Environment')
            if not Environment.isExternalStorageManager():
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                uri = Uri.fromParts("package", activity.getPackageName(), None)
                intent.setData(uri)
                activity.startActivity(intent)
    except Exception:
        pass


class LogLabel(Label):
    """Label yang melebar ke bawah mengikuti isi teks, dipakai di dalam ScrollView."""
    pass


class RootWidget(BoxLayout):
    status_text = StringProperty("Siap.")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=8, **kwargs)

        self.folder_input = TextInput(
            text=DEFAULT_FOLDER, size_hint_y=None, height=48, multiline=False
        )
        self.add_widget(Label(text="Folder berisi arsip .zip/.rar:",
                               size_hint_y=None, height=24, halign="left"))
        self.add_widget(self.folder_input)

        shortcut_row = BoxLayout(size_hint_y=None, height=44, spacing=6)
        for label, path in [
            ("Download", "/storage/emulated/0/Download"),
            ("Documents", "/storage/emulated/0/Documents"),
            ("DCIM", "/storage/emulated/0/DCIM"),
        ]:
            btn = Button(text=label)
            btn.bind(on_release=lambda _b, p=path: self.set_folder(p))
            shortcut_row.add_widget(btn)
        self.add_widget(shortcut_row)

        opt_row = BoxLayout(size_hint_y=None, height=40, spacing=6)
        self.chk_recursive = CheckBox(size_hint_x=None, width=40)
        opt_row.add_widget(self.chk_recursive)
        opt_row.add_widget(Label(text="Telusuri sub-folder juga"))
        self.add_widget(opt_row)

        self.btn_proses = Button(text="Proses", size_hint_y=None, height=52)
        self.btn_proses.bind(on_release=self.mulai_proses)
        self.add_widget(self.btn_proses)

        self.status_label = Label(text=self.status_text, size_hint_y=None, height=28)
        self.bind(status_text=lambda _i, v: setattr(self.status_label, "text", v))
        self.add_widget(self.status_label)

        self.log_label = LogLabel(
            text="", size_hint_y=None, halign="left", valign="top",
            text_size=(None, None),
        )
        self.log_label.bind(texture_size=lambda _i, size: setattr(self.log_label, "height", size[1]))
        scroll = ScrollView()
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)

        self.bind(size=self._update_text_width, pos=self._update_text_width)

    def _update_text_width(self, *_args):
        self.log_label.text_size = (self.width - 24, None)

    def set_folder(self, path):
        self.folder_input.text = path

    def append_log(self, msg):
        def _do(_dt):
            self.log_label.text += (str(msg) + "\n")
        Clock.schedule_once(_do, 0)

    def set_status(self, text):
        def _do(_dt):
            self.status_text = text
        Clock.schedule_once(_do, 0)

    def set_processing(self, is_processing):
        def _do(_dt):
            self.btn_proses.disabled = is_processing
        Clock.schedule_once(_do, 0)

    def mulai_proses(self, *_args):
        folder = self.folder_input.text.strip()
        if not folder or not os.path.isdir(folder):
            self.append_log(f"Folder tidak ditemukan: {folder}")
            return

        self.log_label.text = ""
        self.set_processing(True)
        self.set_status("Memproses...")
        recursive = self.chk_recursive.active

        def worker():
            try:
                core.process_folder(folder, self.append_log, recursive=recursive)
            except Exception as e:
                self.append_log(f"Terjadi error tak terduga: {e}")
            finally:
                self.set_processing(False)
                self.set_status("Selesai.")

        threading.Thread(target=worker, daemon=True).start()


class UnlockArsipApp(App):
    def build(self):
        self.title = "Unlock Arsip"
        minta_izin_penyimpanan()
        return RootWidget()


if __name__ == "__main__":
    UnlockArsipApp().run()
