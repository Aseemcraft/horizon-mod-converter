import os
import re
import shutil
import zipfile
import subprocess
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def extract_jar(jar_path, extract_dir):
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(jar_path, 'r') as jar:
        jar.extractall(extract_dir)

def build_hmod_android(extract_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for folder in ["assets", "data"]:
        src_folder = os.path.join(extract_dir, folder)
        if os.path.exists(src_folder):
            shutil.copytree(src_folder, os.path.join(output_dir, folder), dirs_exist_ok=True)

    mod_info = ""
    for info_file in ["fabric.mod.json", "META-INF/mods.toml"]:
        info_path = os.path.join(extract_dir, info_file)
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8", errors="ignore") as f:
                mod_info += f.read()

    # استخراج كود الجافا لترجمته إلى WebAssembly (WASM)
    all_java_code = ""
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".class"):
                class_path = os.path.join(root, file)
                res = subprocess.run(["javap", "-c", "-p", class_path], capture_output=True, text=True)
                all_java_code += f"\n// Class: {file}\n" + res.stdout

    # 1. توليد ملف horizon-mod.toml الرسمي بدون أي أقواس [mod]
    toml_prompt = f"""
    أنت خبير في محرك Horizon-Rust للعبة ماين كرافت.
    بناءً على معلومات المود التالية، اكتب ملف `horizon-mod.toml` الرسمي بالصيغة التالية حصراً وبدون أي أقواس [mod] أو علامات Markdown:
    id = "معرف_المود_بحروف_صغيرة_فقط"
    name = "اسم المود"
    version = "0.1.0"
    description = "وصف مختصر"
    authors = ["AI Converter"]
    api = "0.2"
    side = "both"
    capabilities = ["registries"]

    معلومات المود:
    {mod_info[:3000]}
    """
    toml_res = client.models.generate_content(model='gemini-2.5-flash', contents=toml_prompt)
    toml_content = toml_res.text.replace("```toml", "").replace("```", "").replace("[mod]", "").strip()
    
    with open(os.path.join(output_dir, "horizon-mod.toml"), "w", encoding="utf-8") as f:
        f.write(toml_content)

    # 2. توليد كود Rust متوافق مع WASM لتجميعه إلى mod.wasm
    wasm_prompt = f"""
    حول منطق مود ماين كرافت التالي إلى كود Rust مستقل (بدون مكتبات خارجية غير قياسية) ليتم تجميعه إلى هدف wasm32-unknown-unknown.
    يجب أن يحتوي الكود على دالة تصدير أساسية `#[no_mangle] pub extern "C" fn init() {{}}`.
    أعطني كود Rust الصافي فقط بدون أي شرح أو Markdown.

    الكود:
    {all_java_code[:20000]}
    """
    rust_res = client.models.generate_content(model='gemini-2.5-flash', contents=wasm_prompt)
    rust_code = rust_res.text.replace("```rust", "").replace("```", "").strip()

    os.makedirs("wasm_project/src", exist_ok=True)
    with open("wasm_project/src/lib.rs", "w", encoding="utf-8") as f:
        f.write(rust_code)

if __name__ == "__main__":
    jar_file = "input_mod.jar"
    if os.path.exists(jar_file):
        extract_jar(jar_file, "extracted_jar")
        build_hmod_android("extracted_jar", "final_package")
