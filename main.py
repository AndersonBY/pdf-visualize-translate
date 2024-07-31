# @Author: Bi Ying
# @Date:   2024-07-21 22:54:26
import re
import os
import io
import json
import mimetypes
import webbrowser
from pathlib import Path
from copy import deepcopy

import pymupdf
from PIL import Image
from flask import (
    Flask,
    abort,
    request,
    jsonify,
    send_file,
    render_template,
    send_from_directory,
)

from vectorvein.settings import settings
from vectorvein.chat_clients import create_chat_client


mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")

app = Flask(__name__)

llm_credentials_file = Path("llm_credentials.json")
if not llm_credentials_file.exists():
    llm_credentials_file.write_text("{}")
settings.load(json.loads(llm_credentials_file.read_text()))

translation_extract_re = re.compile(r"<.*?>(.*?)</.*?>", re.DOTALL)

config_file = Path("config.json")
if not config_file.exists():
    raise FileNotFoundError("Config file not found")
config = json.loads(config_file.read_text())
port = config.get("port", 5000)


class PDFTranslator:
    def __init__(
        self,
        pdf_path: str,
        output_json_path: str,
        translated_pdf_path: str,
        font_name: str,
        font_file: str,
        target_language: str,
        model_selection: list,
    ):
        self.pdf_path = pdf_path
        self.output_json_path = output_json_path
        self.translated_pdf_path = translated_pdf_path
        self.font_name = font_name
        self.font_file = font_file
        self.target_language = target_language
        self.model_selection = model_selection
        self.doc = pymupdf.open(pdf_path)
        self.current_page = 0
        self.translations = {"pages": [{"page_number": i, "translations": []} for i in range(len(self.doc))]}
        self.clients = {}
        provider = model_selection[0].lower() if model_selection else "openai"
        self.clients[provider] = create_chat_client(provider, stream=False)
        self.load_progress()

    def load_progress(self):
        if Path(self.output_json_path).exists():
            with open(self.output_json_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

    def save_progress(self):
        with open(self.output_json_path, "w", encoding="utf-8") as f:
            json.dump(self.translations, f, ensure_ascii=False, indent=4)

    def get_page_info(self, page_num):
        page = self.doc[page_num]
        blocks = page.get_text("blocks")
        valid_blocks = []
        extra_blocks = deepcopy(self.translations["pages"][page_num]["translations"])
        for block in blocks:
            if self.is_valid_text(block[4]):
                block_info = {
                    "originalRect": block[:4],
                    "rect": block[:4],
                    "text": block[4].strip(),
                    "font_size": self.get_font_size(page, block),
                    "color": self.get_text_color(page, block),
                }
                # Check if this block has been translated
                if self.translations["pages"][page_num]["translations"]:
                    translated_block = next(
                        (
                            item
                            for item in self.translations["pages"][page_num]["translations"]
                            if item["original"] == block_info["text"]
                            and tuple(item["rect"]) == tuple(block_info["rect"])
                        ),
                        None,
                    )
                    if translated_block:
                        block_info["translation"] = translated_block["translation"]
                        block_info["translated"] = translated_block["translation"] is not None
                        block_info["rect"] = translated_block.get("new_rect") or block_info["rect"]
                        block_info["align"] = translated_block.get("align", pymupdf.TEXT_ALIGN_LEFT)
                        if block_info.get("font_size") != translated_block.get("font_size"):
                            block_info["font_size"] = translated_block.get("font_size")
                        if block_info.get("color") != translated_block.get("color"):
                            block_info["color"] = translated_block.get("color")
                        # 从 extra_blocks 中删除这个translated_block
                        extra_blocks.remove(translated_block)
                    else:
                        block_info["translated"] = False
                else:
                    block_info["translated"] = False
                valid_blocks.append(block_info)

        for extra_block in extra_blocks:
            extra_block["text"] = extra_block["original"]
            extra_block["translated"] = extra_block["translation"] is not None
            extra_block["originalRect"] = extra_block["rect"]
            extra_block["rect"] = extra_block.get("new_rect") or extra_block["rect"]
            extra_block["align"] = extra_block.get("align", pymupdf.TEXT_ALIGN_LEFT)
            extra_block["is_extra"] = True
            valid_blocks.append(extra_block)

        return {"blocks": valid_blocks, "width": page.rect.width, "height": page.rect.height}

    def is_valid_text(self, text):
        return bool(re.search(r"[a-zA-Z0-9\u4e00-\u9fff]", text))

    def get_font_size(self, page, block):
        text_instances = page.search_for(block[4].strip())
        if text_instances:
            rect = text_instances[0]
            font_size = rect.y1 - rect.y0
            return font_size
        return 12  # Default font size if not found

    def get_text_color(self, page, block):
        text_instances = page.search_for(block[4].strip())
        if not text_instances:
            return (0, 0, 0)
        rect = text_instances[0]
        for span in page.get_text("dict")["blocks"]:
            for line in span.get("lines", []):
                for span in line["spans"]:
                    if pymupdf.Rect(span["bbox"]) == rect:
                        color_int = span["color"]
                        r = (color_int >> 16) & 0xFF
                        g = (color_int >> 8) & 0xFF
                        b = color_int & 0xFF
                        return (r / 255.0, g / 255.0, b / 255.0)
        return (0, 0, 0)  # Default color (black)

    def translate_block(self, text: str, model_selection: list | None = None, extra_requirements: str = ""):
        if model_selection is None:
            provider = self.model_selection[0].lower()
            model = self.model_selection[1].lower()
        else:
            provider = model_selection[0].lower()
            model = model_selection[1].lower()

        if provider not in self.clients:
            self.clients[provider] = create_chat_client(provider, stream=False)
        client = self.clients[provider]

        book_name = Path(self.pdf_path).stem
        system_prompt = f"你是专业的书籍翻译员，你需要对这本《{book_name}》进行翻译。翻译时务必根据这本书的内容进行翻译，保持信达雅。请根据用户的输入片段直接输出翻译结果，不要解释。"
        if extra_requirements:
            system_prompt += f"\n\n额外要求: {extra_requirements}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"<原文片段>{text}</原文片段>\n\n<要求>目标语言：{self.target_language}\n直接输出翻译结果，不需要用XML标签包裹。</要求>",
            },
        ]

        response = client.create_completion(messages=messages, model=model, temperature=0.2)
        result = response["content"]
        if translation_extract_re.match(result):
            return translation_extract_re.match(result).group(1)
        else:
            return result

    def delete_block(self, page_num, rect, original):
        # Convert rect to a tuple for easy comparison
        rect_tuple = tuple(rect)

        # Check if the translation already exists for this block on the given page
        existing_translation = next(
            (
                item
                for item in self.translations["pages"][page_num]["translations"]
                if tuple(item["rect"]) == rect_tuple and item["original"] == original
            ),
            None,
        )

        if existing_translation:
            # If a translation already exists, delete the existing record
            self.translations["pages"][page_num]["translations"].remove(existing_translation)
            self.save_progress()

    def save_translation(
        self,
        page_num,
        block_index,
        translation,
        original,
        rect,
        font_size,
        color,
        align,
        new_rect=None,
    ):
        # Convert rect to a tuple for easy comparison
        rect_tuple = tuple(rect)

        # Check if the translation already exists for this block on the given page
        existing_translation = next(
            (
                item
                for item in self.translations["pages"][page_num]["translations"]
                if tuple(item["rect"]) == rect_tuple and item["original"] == original
            ),
            None,
        )

        if existing_translation:
            # If a translation already exists, update the existing record
            existing_translation["translation"] = translation
            existing_translation["original"] = original
            existing_translation["font_size"] = font_size
            existing_translation["color"] = color
            existing_translation["new_rect"] = new_rect if new_rect else rect
            existing_translation["align"] = align
        else:
            # If no translation exists, append a new record
            self.translations["pages"][page_num]["translations"].append(
                {
                    "original": original,
                    "translation": translation,
                    "rect": rect,
                    "new_rect": new_rect if new_rect else rect,
                    "font_size": font_size,
                    "color": color,
                    "align": align,
                }
            )

        self.save_progress()

    def _add_textbox(
        self,
        page: pymupdf.Page,
        rect: pymupdf.Rect,
        text,
        font_name,
        font_file,
        initial_font_size=60,
        min_font_size=5,
        color=(0, 0, 0),
        align: int = pymupdf.TEXT_ALIGN_LEFT,
    ):
        font_size = initial_font_size
        while font_size >= min_font_size:
            result = page.insert_textbox(
                rect,
                text,
                fontsize=font_size,
                fontname=font_name,
                fontfile=font_file,
                color=color,
                align=align,
            )
            if result >= 0:  # 成功插入文本
                return font_size
            font_size -= 0.5  # 减小字体大小并重试

        # 如果达到最小字体大小仍然无法插入，则使用最小字体大小插入
        # 但是要不断扩大 rect 的宽度以使得能够正常插入
        delta = rect.x1 - rect.x0
        inserted = False
        while not inserted:
            delta += 1
            rect = pymupdf.Rect(rect.x0, rect.y0, rect.x0 + delta, rect.y1 + delta)
            insert_result = page.insert_textbox(
                rect,
                text,
                fontsize=min_font_size,
                fontname=font_name,
                fontfile=font_file,
                color=color,
                align=align,
            )
            inserted = insert_result >= 0
        return min_font_size

    def generate_translated_pdf(self):
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            page_data = self.translations["pages"][page_num]
            for translation in page_data["translations"]:
                block_rect = pymupdf.Rect(*translation["rect"])

                # 使用 add_redact_annot 方法添加涂黑注释
                page.add_redact_annot(block_rect)

                # 应用涂黑注释来删除原始文本
                page.apply_redactions(images=0, graphics=0, text=0)

            for translation in page_data["translations"]:
                rect = translation.get("new_rect") or translation["rect"]
                block_rect = pymupdf.Rect(*rect)

                # 插入翻译后的文本框
                self._add_textbox(
                    page=page,
                    rect=block_rect,
                    text=translation["translation"],
                    font_name=self.font_name,
                    font_file=self.font_file,
                    initial_font_size=translation["font_size"],
                    color=translation.get("color", (0, 0, 0)),
                    align=translation.get("align", pymupdf.TEXT_ALIGN_LEFT),
                )
        self.doc.save(self.translated_pdf_path, garbage=4, deflate=True, clean=True)
        return f"Translated PDF saved to {self.translated_pdf_path}"

    def preview_page(self, page_num, scale=2.0):
        # Create a temporary PDF with just the requested page
        temp_doc = pymupdf.open()
        temp_doc.insert_pdf(self.doc, from_page=page_num, to_page=page_num)
        temp_page = temp_doc[0]

        # Apply translations to the temporary page
        page_data = self.translations["pages"][page_num]
        for translation in page_data["translations"]:
            block_rect = pymupdf.Rect(*translation["rect"])
            temp_page.add_redact_annot(block_rect)
            temp_page.apply_redactions(images=0, graphics=0, text=0)

        for translation in page_data["translations"]:
            rect = translation.get("new_rect") or translation["rect"]
            block_rect = pymupdf.Rect(*rect)
            self._add_textbox(
                page=temp_page,
                rect=block_rect,
                text=translation["translation"],
                font_name=self.font_name,
                font_file=self.font_file,
                initial_font_size=translation["font_size"],
                color=translation.get("color", (0, 0, 0)),
                align=translation.get("align", pymupdf.TEXT_ALIGN_LEFT),
            )

        # Render the page to an image with increased resolution
        mat = pymupdf.Matrix(scale, scale)  # Increase scale for higher resolution
        pix = temp_page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Save the image to a byte stream
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG", dpi=(300, 300))  # Set DPI for better quality
        img_byte_arr = img_byte_arr.getvalue()

        # Close the temporary document
        temp_doc.close()

        return img_byte_arr


translator = None


def get_pdf_folder():
    if os.environ.get("PDF_VISUALIZE_TRANSLATE_DEBUG", "0") == "1":
        return Path(__file__).parent / "pdf"
    else:
        return Path(__file__).parent.parent / "pdf"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/get_config", methods=["GET"])
def get_config():
    config_path = "config.json"
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf8") as f:
            config = json.load(f)
        return jsonify(config)
    else:
        return jsonify({"error": "Config file not found"}), 404


@app.route("/api/save_config", methods=["POST"])
def save_config():
    data = request.get_json()
    with open("config.json", "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return jsonify({"status": "success"})


@app.route("/api/init_translator", methods=["POST"])
def init_translator():
    global translator
    data = request.get_json()
    pdf_path = data["pdf_path"]
    output_json_path = data["output_json_path"]
    translated_pdf_path = data["translated_pdf_path"]
    font_name = data["font_name"]
    font_file = data["font_file"]
    target_language = data["target_language"]
    model_selection = data["model_selection"]
    try:
        translator = PDFTranslator(
            pdf_path,
            output_json_path,
            translated_pdf_path,
            font_name,
            font_file,
            target_language,
            model_selection,
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/get_page_info", methods=["POST"])
def get_page_info():
    data = request.get_json()
    page_num = int(data["page_num"])
    return jsonify(translator.get_page_info(page_num))


@app.route("/api/translate_block", methods=["POST"])
def translate_block():
    data = request.get_json()
    text = data["text"]
    model_selection = data["model_selection"]
    extra_requirements = data.get("extra_requirements", "")
    translation = translator.translate_block(text, model_selection, extra_requirements)
    return jsonify({"translation": translation})


@app.route("/api/delete_block", methods=["POST"])
def delete_block():
    data = request.get_json()
    page_num = int(data["page_num"])
    rect = data["rect"]
    original = data["original"]
    translator.delete_block(page_num, rect, original)
    return jsonify({"status": "success"})


@app.route("/api/save_translation", methods=["POST"])
def save_translation():
    data = request.get_json()
    print(data)
    page_num = int(data["page_num"])
    block_index = int(data["block_index"])
    translation = data["translation"]
    original = data["original"]
    rect = data["rect"]
    new_rect = data.get("new_rect")  # 使用get方法以防止newRect不存在
    font_size = float(data["font_size"])
    color = data["color"]
    align = int(data.get("align", pymupdf.TEXT_ALIGN_LEFT))
    translator.save_translation(
        page_num,
        block_index,
        translation,
        original,
        rect,
        font_size,
        color,
        align,
        new_rect,
    )
    return jsonify({"status": "success"})


@app.route("/api/finish_translation", methods=["POST"])
def finish_translation():
    result = translator.generate_translated_pdf()
    return jsonify({"status": "success", "message": result})


@app.route("/api/preview", methods=["POST"])
def preview_page():
    data = request.get_json()
    page_num = int(data["page_num"])

    img_byte_arr = translator.preview_page(page_num)

    return send_file(
        io.BytesIO(img_byte_arr),
        mimetype="image/png",
        as_attachment=True,
        download_name=f"preview_page_{page_num}.png",
    )


@app.route("/pdf/<path:filename>")
def serve_pdf(filename):
    print(filename)
    pdf_folder = get_pdf_folder()
    print(pdf_folder)
    try:
        return send_from_directory(pdf_folder, filename, mimetype="application/pdf")
    except FileNotFoundError:
        abort(404)


if __name__ == "__main__":
    webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(debug=True, port=port)
