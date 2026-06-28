
from jmcomic import create_option_by_file, download_album
from PyPDF2 import PdfReader, PdfWriter
import os  # 导入os模块，用于检查文件是否存在
import sys
def encrypt_pdf(input_pdf, output_pdf, password):
    """给PDF文件加密的函数，增加异常处理"""
    # 先检查输入PDF是否存在
    if not os.path.exists(input_pdf):
        print(f"错误：未找到文件 {input_pdf}，加密失败！")
        return False

    try:
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        # 遍历所有页面并添加到writer
        for page in reader.pages:
            writer.add_page(page)

        # 设置加密密码（用户密码，仅能查看；权限密码留空）
        writer.encrypt(user_password=password, owner_password='', use_128bit=True)

        # 保存加密后的PDF
        with open(output_pdf, "wb") as f:
            writer.write(f)
        print(f"✅ PDF加密成功！输出文件：{output_pdf}")
        return True
    except Exception as e:
        print(f"❌ PDF加密失败：{str(e)}")
        return False


if __name__ == "__main__":
    # 获取用户输入的ID
    try:
        album_id = int(input("释放你的想象力吧:\n"))
    except ValueError:
        print("❌ 输入错误！请输入数字ID")
        sys.exit(1)

    # 1. 初始化jmcomic配置
    try:
        # 读取配置文件（确保option.yml在同目录）
        option = create_option_by_file("option.yml")
        print("✅ 配置文件加载成功")
    except FileNotFoundError:
        print("❌ 未找到option.yml配置文件！请确保该文件与test.py在同一目录")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 配置文件加载失败：{str(e)}")
        sys.exit(1)

    # 2. 下载漫画专辑（生成PDF）
    try:
        print(f"📥 开始下载ID为 {album_id} 的漫画...")
        download_album(album_id, option)
        print(f"✅ 漫画下载完成！")
    except Exception as e:
        print(f"❌ 漫画下载失败：{str(e)}")
        print("提示：请检查ID是否正确，或jmcomic模块是否支持该ID的资源")
        sys.exit(1)

    # 3. 给PDF加密
    input_pdf = f"{album_id}.pdf"
    output_pdf = f"{album_id}_locked.pdf"
    password = f"{album_id}"
    encrypt_pdf(input_pdf, output_pdf, password)