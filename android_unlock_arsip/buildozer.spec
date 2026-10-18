[app]
title = Unlock Arsip
package.name = unlockarsip
package.domain = org.sayasukashirakami

source.dir = .
source.include_exts = py

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
