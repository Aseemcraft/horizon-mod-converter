name: Run Rust Mod Converter

on:
  push:
    paths:
      - 'input_mod.jar'
  workflow_dispatch:

jobs:
  build-and-convert:
    runs-on: ubuntu-latest
    steps:
      - name: سحب ملفات المستودع
        uses: actions/checkout@v4

      - name: تثبيت بيئة راست ومعماريات الأندرويد والكمبيوتر
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: aarch64-linux-android, x86_64-unknown-linux-gnu, x86_64-pc-windows-gnu

      - name: تثبيت أدوات التجميع للكمبيوتر
        run: sudo apt-get update && sudo apt-get install -y gcc-mingw-w64-x86-64

      - name: تثبيت مكتبة Gemini
        run: pip install google-genai

      - name: تشغيل الذكاء الاصطناعي لترجمة المود
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python app.py

      - name: تجهيز ملف إعدادات مشروع راست بالمكتبات الأساسية
        run: |
          cat << 'EOF' > rust_mod/Cargo.toml
          [package]
          name = "horizon_converted_mod"
          version = "0.1.0"
          edition = "2021"

          [lib]
          crate-type = ["cdylib"]

          [dependencies]
          log = "0.4"
          lazy_static = "1.4"
          parking_lot = "0.12"
          serde = { version = "1.0", features = ["derive"] }
          serde_json = "1.0"
          EOF

      - name: تجميع المود حسب اختيار المستخدم
        working-directory: ./rust_mod
        env:
          CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER: /usr/local/lib/android/sdk/ndk/27.2.12479018/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android24-clang
        run: |
          PLATFORM=$(cat ../target_platform.txt 2>/dev/null || echo "android")
          echo "المعمارية المختارة: $PLATFORM"
          if [ "$PLATFORM" = "pc" ]; then
            cargo build --release --target x86_64-unknown-linux-gnu || true
            cargo build --release --target x86_64-pc-windows-gnu || true
          else
            cargo build --release --target aarch64-linux-android || true
          fi

      - name: رفع المود الجاهز للتحميل
        uses: actions/upload-artifact@v4
        with:
          name: Converted-Horizon-Mod
          path: |
            rust_mod/src/lib.rs
            rust_mod/target/*/release/*.so
            rust_mod/target/*/release/*.dll
