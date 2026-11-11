import os
import zipfile
import subprocess
from google import genai

# التأكد من وجود مفتاح API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("مفتاح GEMINI_API_KEY غير موجود في Secrets!")

client = genai.Client(api_key=api_key)

def extract_and_decompile(jar_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(jar_path, 'r') as jar:
        jar.extractall(output_dir)
    
    all_java_code = ""
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".class"):
                class_path = os.path.join(root, file)
                try:
                    result = subprocess.run(["javap", "-c", "-p", class_path], capture_output=True, text=True)
                    all_java_code += f"\n// Class: {file}\n" + result.stdout
                except Exception as e:
                    print(f"تخطي ملف {file}: {e}")
    return all_java_code

def translate_to_rust(java_code):
    if not java_code.strip():
        return "// لم يتم العثور على أكواد جافا داخل الملف المرفوع."
        
    prompt = f"""
    أنت خبير في لغة Rust وتطوير مودات محرك Horizon-Rust للعبة ماين كرافت.
    قم بتحويل كود البايت كود (Bytecode) والكلاسات المستخرجة من مود الجافا التالي إلى كود Rust كامل وصحيح، مع الالتزام الصارم بقواعد الذاكرة (Ownership) في Rust.
    أعطني كود ملف lib.rs فقط بدون أي شرح إضافي أو علامات تنسيق Markdown.

    كود المود المستخرج:
    {java_code}
    """
    # استخدام gemini-2.5-flash لضمان العمل في الباقة المجانية بأقصى سرعة
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text.replace("```rust", "").replace("```", "").strip()

if __name__ == "__main__":
    jar_file = "input_mod.jar"
    if os.path.exists(jar_file):
        print("جاري فك ضغط المود...")
        extracted_code = extract_and_decompile(jar_file, "decompiled_java")
        print(f"تم استخراج {len(extracted_code)} حرف. جاري الترجمة بالذكاء الاصطناعي...")
        
        rust_code = translate_to_rust(extracted_code[:25000])
        
        os.makedirs("rust_mod/src", exist_ok=True)
        with open("rust_mod/src/lib.rs", "w", encoding="utf-8") as f:
            f.write(rust_code)
        print("تمت الترجمة وحفظ ملف lib.rs بنجاح!")
    else:
        print("ملف input_mod.jar غير موجود!")

