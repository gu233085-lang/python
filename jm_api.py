from flask import Flask, request, send_file, jsonify
from PyPDF2 import PdfReader, PdfWriter
import os
import sys
import traceback
import subprocess

app = Flask(__name__)

# 固定下载路径
FIXED_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "炫压抑", "jm")
os.makedirs(FIXED_DOWNLOAD_PATH, exist_ok=True)
print(f"✅ 下载路径：{FIXED_DOWNLOAD_PATH}，是否存在：{os.path.exists(FIXED_DOWNLOAD_PATH)}")


# ==================== 工具函数 ====================
def encrypt_pdf(input_pdf_path, output_pdf_path, password):
    """PDF加密函数"""
    if not os.path.exists(input_pdf_path):
        return {"success": False, "msg": f"源文件不存在：{input_pdf_path}"}
    try:
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(user_password=password, owner_password=None, use_128bit=True)
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            writer.write(f)
        return {"success": True, "msg": "加密成功", "output_path": output_pdf_path}
    except Exception as e:
        return {"success": False, "msg": f"加密失败：{str(e)}"}


def run_jmcomic_cli(album_id):
    """调用jmcomic命令行下载漫画"""
    try:
        # jmcomic CLI命令（所有版本都支持的核心命令）
        cmd = [
            sys.executable,  # 使用当前Python解释器，确保环境一致
            "-m", "jmcomic",
            "download", album_id,
            "--save-path", FIXED_DOWNLOAD_PATH,
            "--ext", "pdf",
            "--thread", "1"
        ]
        # 执行命令并捕获输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 超时5分钟
        )
        if result.returncode == 0:
            print(f"✅ CLI下载成功：{result.stdout}")
            return {"success": True, "msg": "下载成功"}
        else:
            print(f"❌ CLI下载失败：{result.stderr}")
            return {"success": False, "msg": f"下载失败：{result.stderr[:200]}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "msg": "下载超时（5分钟）"}
    except Exception as e:
        return {"success": False, "msg": f"命令执行失败：{str(e)}"}


# ==================== 接口定义 ====================
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Python API运行正常（CLI模式）"})


@app.route("/api/get-pdf-list", methods=["GET"])
def get_pdf_list():
    """获取PDF列表（修复前端空值问题：返回空数组而非undefined）"""
    try:
        pdf_files = []
        for root, dirs, files in os.walk(FIXED_DOWNLOAD_PATH):
            for file in files:
                if file.lower().endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    pdf_files.append({
                        "filename": file,
                        "path": file_path,
                        "size_mb": round(os.path.getsize(file_path) / 1024 / 1024, 2)
                    })
        # 关键：即使为空，也返回空数组，避免前端读length报错
        return jsonify({"success": True, "data": pdf_files})
    except Exception as e:
        print(f"获取PDF列表失败：{e}")
        # 异常时也返回空数组
        return jsonify({"success": False, "msg": str(e), "data": []})


@app.route("/api/download", methods=["POST"])
def download_comic():
    """下载漫画接口（CLI模式）"""
    data = request.json
    if not data or "album_id" not in data:
        return jsonify({"success": False, "msg": "缺少album_id参数", "data": []}), 400

    album_id = str(data["album_id"]).strip()
    if not album_id:
        return jsonify({"success": False, "msg": "album_id不能为空", "data": []}), 400

    print(f"\n=== 开始处理漫画下载：album_id={album_id} ===")

    # 1. 调用CLI下载
    download_result = run_jmcomic_cli(album_id)
    if not download_result["success"]:
        return jsonify({"success": False, "msg": download_result["msg"], "data": []}), 500

    # 2. 查找PDF
    pdf_files = []
    for root, dirs, files in os.walk(FIXED_DOWNLOAD_PATH):
        for file in files:
            if album_id in file and file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))

    if not pdf_files:
        return jsonify({"success": False, "msg": "下载成功但未找到PDF", "data": []}), 200

    # 3. 加密PDF
    input_pdf = pdf_files[0]
    output_pdf = os.path.join(FIXED_DOWNLOAD_PATH, f"{album_id}_encrypted.pdf")
    encrypt_result = encrypt_pdf(input_pdf, output_pdf, album_id)

    if not encrypt_result["success"]:
        return jsonify({"success": False, "msg": encrypt_result["msg"], "data": []}), 200

    # 4. 返回结果
    return jsonify({
        "success": True,
        "msg": f"专辑 {album_id} 下载并加密成功",
        "data": [{
            "album_id": album_id,
            "filename": os.path.basename(output_pdf),
            "size_mb": round(os.path.getsize(output_pdf) / 1024 / 1024, 2)
        }]
    }), 200


@app.route("/api/view-pdf", methods=["GET"])
def view_pdf():
    album_id = request.args.get("album_id")
    filename = request.args.get("filename")
    if not album_id and not filename:
        return jsonify({"success": False, "msg": "缺少参数", "data": []}), 400

    pdf_path = ""
    if filename:
        pdf_path = os.path.join(FIXED_DOWNLOAD_PATH, filename)
    else:
        for root, dirs, files in os.walk(FIXED_DOWNLOAD_PATH):
            for file in files:
                if f"{album_id}_encrypted.pdf" == file:
                    pdf_path = os.path.join(root, file)
                    break

    if not os.path.exists(pdf_path):
        return jsonify({"success": False, "msg": "PDF不存在", "data": []}), 404

    try:
        return send_file(pdf_path, mimetype="application/pdf")
    except Exception as e:
        return jsonify({"success": False, "msg": str(e), "data": []}), 500


@app.route("/api/download-pdf", methods=["GET"])
def download_pdf():
    album_id = request.args.get("album_id")
    filename = request.args.get("filename")
    if not album_id and not filename:
        return jsonify({"success": False, "msg": "缺少参数", "data": []}), 400

    pdf_path = ""
    if filename:
        pdf_path = os.path.join(FIXED_DOWNLOAD_PATH, filename)
    else:
        for root, dirs, files in os.walk(FIXED_DOWNLOAD_PATH):
            for file in files:
                if f"{album_id}_encrypted.pdf" == file:
                    pdf_path = os.path.join(root, file)
                    break

    if not os.path.exists(pdf_path):
        return jsonify({"success": False, "msg": "PDF不存在", "data": []}), 404

    try:
        return send_file(pdf_path, mimetype="application/pdf", as_attachment=True)
    except Exception as e:
        return jsonify({"success": False, "msg": str(e), "data": []}), 500


# ==================== 启动服务 ====================
if __name__ == "__main__":
    print("✅ Python Flask API 启动中（CLI模式）...")
    print(f"✅ Python解释器路径：{sys.executable}")
    # 验证jmcomic CLI是否可用
    try:
        subprocess.run([sys.executable, "-m", "jmcomic", "--version"], capture_output=True, text=True)
        print("✅ jmcomic CLI 可用")
    except Exception as e:
        print(f"❌ jmcomic CLI 不可用：{e}")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)