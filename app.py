import os
import json
import shutil
import zipfile
import subprocess
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def read_platform():
    if os.path.exists("target_platform.txt"):
        with open("target_platform.txt", "r") as f:
            return f.read().strip()
    return "android"

def extract_jar(jar_path, extract_dir):
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(jar_path, 'r') as jar:
        jar.extractall(extract_dir)

def build_hmod_android(extract_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # نسخ مجلدات الأصول والبيانات (assets & data) من مود الجافا الأصلي
    for folder in ["assets", "data"]:
        src_folder = os.path.join(extract_dir, folder)
        if os.path.exists(src_folder):
            shutil.copytree(src_folder, os.path.join(output_dir, folder), dirs_exist_ok=True)

    # قراءة معلومات المود الأصلية (fabric.mod.json أو mods.toml)
    mod_info = ""
    for info_file in ["fabric.mod.json", "META-INF/mods.toml"]:
        info_path = os.path.join(extract_dir, info_file)
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8", errors="ignore") as f:
                mod_info += f.read()

    # استخراج أسماء الكلاسات لفهم محتوى المود
    classes_summary = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".class"):
                classes_summary.append(file)

    prompt = f"""
    أنت خبير في تطوير مودات المحتوى (.hmod) لمحرك Horizon-Rust للعبة ماين كرافت.
    بناءً على معلومات مود الجافا التالي، قم بإنشاء محتوى ملف `horizon-mod.toml` الرسمي.
    يجب أن يحتوي الملف على قسم `[mod]` بالحقول التالية:
    id = "معرف_المود_بحروف_صغيرة"
    name = "اسم المود"
    version = "1.0.0"
    description = "وصف مختصر للمود"
    authors = ["Converted by AI"]

    أعطني محتوى ملف horizon-mod.toml فقط بدون أي شرح أو علامات Markdown.

    معلومات المود:
    {mod_info[:4000]}
    الكلاسات الموجودة:
    {', '.join(classes_summary[:50])}
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    toml_content = response.text.replace("```toml", "").replace("```", "").strip()
    
    with open(os.path.join(output_dir, "horizon-mod.toml"), "w", encoding="utf-8") as f:
        f.write(toml_content)

    # ضغط المجلد بصيغة .hmod
    shutil.make_archive("converted_mod", 'zip', output_dir)
    os.rename("converted_mod.zip", "converted_mod.hmod")
    print("تم إنشاء حزمة الأندرويد converted_mod.hmod بنجاح!")

def build_hnmod_pc(extract_dir, output_dir):
    os.makedirs(os.path.join(output_dir, "src"), exist_ok=True)
    
    all_java_code = ""
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".class"):
                class_path = os.path.join(root, file)
                res = subprocess.run(["javap", "-c", "-p", class_path], capture_output=True, text=True)
                all_java_code += f"\n// Class: {file}\n" + res.stdout

    prompt = f"""
    أنت خبير في لغة Rust وتطوير مودات Native (.hnmod) لمحرك Horizon-Rust على الكمبيوتر.
    حول كود الجافا التالي إلى كود Rust نظيف لملف `src/lib.rs`.
    أعطني كود Rust فقط بدون أي شرح أو علامات Markdown.

    الكود:
    {all_java_code[:25000]}
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    rust_code = response.text.replace("```rust", "").replace("```", "").strip()

    with open(os.path.join(output_dir, "src/lib.rs"), "w", encoding="utf-8") as f:
        f.write(rust_code)

    native_json = {
        "id": "converted_native_mod",
        "name": "Converted Native Mod",
        "version": "1.0.0",
        "description": "Converted from Java mod via AI"
    }
    with open(os.path.join(output_dir, "horizon-native.json"), "w", encoding="utf-8") as f:
        json.dump(native_json, f, indent=2)

    cargo_toml = """[package]
name = "converted_native_mod"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["rlib"]
"""
    with open(os.path.join(output_dir, "Cargo.toml"), "w", encoding="utf-8") as f:
        f.write(cargo_toml)

    shutil.make_archive("converted_mod", 'zip', output_dir)
    os.rename("converted_mod.zip", "converted_mod.hnmod")
    print("تم إنشاء حزمة الكمبيوتر converted_mod.hnmod بنجاح!")

if __name__ == "__main__":
    jar_file = "input_mod.jar"
    if os.path.exists(jar_file):
        platform = read_platform()
        extract_jar(jar_file, "extracted_jar")
        os.makedirs("final_output", exist_ok=True)
        
        if platform == "pc":
            build_hnmod_pc("extracted_jar", "final_output/package")
            shutil.move("converted_mod.hnmod", "final_output/converted_mod.hnmod")
        else:
            build_hmod_android("extracted_jar", "final_output/package")
            shutil.move("converted_mod.hmod", "final_output/converted_mod.hmod")

