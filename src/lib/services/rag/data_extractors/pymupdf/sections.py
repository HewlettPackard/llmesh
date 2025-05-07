#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyMuPdf for Sections Data Extractor

This module allows:
- Extracting data from a PDF document using the PyMuPDF library
- Parsing elements in an unstructured manner
- Finding tables using bounding box coordinates
"""

import os
from typing import Optional
from pydantic import Field
import fitz
from tqdm import tqdm
from src.lib.services.rag.data_extractors.base import BaseDataExtractor
from src.lib.core.file_cache import FileCache
from src.lib.core.log import Logger


logger = Logger().get_logger()


class PyMuPdfForSectionsDataExtractor(BaseDataExtractor):  # pylint: disable=R0903
    """
    Strategy for managing data extraction from PDF sections
    """

    class Config(BaseDataExtractor.Config):
        """
        Configuration for the Data Extractor
        """
        title_size_threshold: Optional[int] = Field(
            12,
            description="Size of title fonts"
        )
        convert_table_to_html: Optional[bool] = Field(
            True,
            description="Convert tables to HTML format"
        )
        table_column_threshold: Optional[int] = Field(
            20,
            description="Pixel to consider a sable table column"
        )
        skip_header_lines: Optional[int] = Field(
            0,
            description="Number of initial lines to skip"
        )
        skip_footer_lines: Optional[int] = Field(
            0,
            description="Number of end lines to skip"
        )
        skip_header_images: Optional[int] = Field(
            0,
            description="Number of initial images to skip"
        )
        skip_footer_images: Optional[int] = Field(
            0,
            description="Number of end images to skip"
        )

    def __init__(self, config):
        self.config = PyMuPdfForSectionsDataExtractor.Config(**config)
        self.result = PyMuPdfForSectionsDataExtractor.Result()
        self.file_cache = FileCache({"cache_to_file": self.config.cache_elements_to_file})

    def parse(self, file_path: str) -> 'BaseDataExtractor.Result':
        """
        Parse a PDF file.

        :param file_path: Path to the PDF file
        :return: Result object containing the extracted elements
        """
        try:
            self.result.status = "success"
            if self.file_cache.is_cached(file_path):
                logger.debug("Load elements from file.")
                self.result.elements = self.file_cache.load(file_path)
            else:
                logger.debug("Parse document.")
                self.result.elements = self._extract_elements(file_path)
                logger.debug("Save elements to file.")
                self.file_cache.save(file_path, self.result.elements)
        except Exception as e:  # pylint: disable=W0718
            self.result.status = "failure"
            self.result.error_message = f"An error occurred while extracting the document: {e}"
            logger.error(self.result.error_message)
        return self.result

    def _extract_elements(self, file_path: str):
        if self.config.document_type == "Pdf":
            elements = self._extract_pdf_elements(file_path)
        else:
            logger.error("Document type not supported")
            elements = None
        return elements

    def _extract_pdf_elements(self, file_path: str):
        elements = []
        pdf_document = fitz.open(file_path)
        document_basename = os.path.basename(file_path)
        if self.config.extract_text:
            text_elements = self._extract_texts(pdf_document, document_basename)
            if self.config.convert_table_to_html:
                elements = self._transform_tables(text_elements)
            else:
                elements = text_elements
        if self.config.extract_image:
            self._extract_images(pdf_document, document_basename)
        return elements

    def _extract_texts(self, pdf_document, document_basename: str):
        extracted_data = []
        for page_num in tqdm(range(len(pdf_document)), desc="Processing pages"):
            page = pdf_document.load_page(page_num)
            text_with_coords = page.get_text("dict")
            lines = self._get_lines(text_with_coords)
            page_data = self._process_lines(lines, page_num, document_basename)
            extracted_data.extend(page_data)
        return extracted_data

    def _get_lines(self, text_with_coords: dict):
        lines = [
            line for block in text_with_coords["blocks"]
            if "lines" in block for line in block["lines"]
        ]
        if self.config.skip_header_lines > 0:
            lines = lines[self.config.skip_header_lines:]
        if self.config.skip_footer_lines > 0:
            lines = lines[:-self.config.skip_footer_lines]  # pylint: disable=E1130
        return lines

    def _process_lines(self, lines: list, page_num: int, document_name: str):
        extracted_data = []
        last_position = {
            'x': None,
            'y': None,
            'element_index': None
        }
        table_info = {
            'mode': False,
            'elements': 0
        }
        for line in lines:
            for span in line["spans"]:
                element = self._create_element(span, page_num, document_name)
                table_info = self._update_table_mode(
                    table_info,
                    element["metadata"]["coordinates"],
                    last_position,
                    extracted_data
                )
                if table_info['mode']:
                    element["metadata"]["type"] = "table"
                extracted_data.append(element)
                last_position['x'] = element["metadata"]["coordinates"]["x0"]
                last_position['y'] = element["metadata"]["coordinates"]["y0"]
                last_position['element_index'] = len(extracted_data) - 1
        return extracted_data

    def _create_element(self, span: dict, page_num: int, document_name: str):
        x0, y0, x1, y1 = span["bbox"]
        text = span["text"]
        size = span["size"]
        metadata = {
            "page_number": page_num + 1,
            "document_name": document_name,
            "type": "header" if size > self.config.title_size_threshold else "text",
            "header": text if size > self.config.title_size_threshold else None,
            "coordinates": {"x0": x0, "y0": y0, "x1": x1, "y1": y1}
        }
        return {
            "text": text,
            "metadata": metadata
        }

    def _update_table_mode(
            self, table_info: dict,
            coordinates: dict,
            last_position: dict,
            extracted_data: list):
        if last_position['y'] is not None:
            if coordinates["y0"] == last_position['y']:
                table_info['elements'] += 1
                if table_info['elements'] == 1:
                    table_info['mode'] = True
                    if last_position['element_index'] is not None:
                        extracted_data[last_position['element_index']]["metadata"]["type"] = "table"
            elif table_info['mode'] and coordinates["x0"] < last_position['x']:
                table_info['mode'] = False
                table_info['elements'] = 0
        return table_info

    def _transform_tables(self, extracted_data: list):
        transformed_data = []
        table_state = self._reset_table_state()
        for item in extracted_data:
            metadata = item["metadata"]
            if metadata["type"] == "table":
                table_state = self._process_table_item(table_state, item)
            else:
                if table_state["current_table"]:
                    transformed_data.append(self._convert_table_to_html(
                        table_state["current_table"], table_state["table_metadata"]))
                    table_state = self._reset_table_state()
                transformed_data.append(item)
        if table_state["current_table"]:
            transformed_data.append(self._convert_table_to_html(
                table_state["current_table"], table_state["table_metadata"]))
        return transformed_data

    def _reset_table_state(self):
        return {
            "current_table": [],
            "current_row": [],
            "last_x": None,
            "last_y": None,
            "table_metadata": None
        }

    def _process_table_item(self, table_state: dict, item: dict):
        coordinates = item["metadata"]["coordinates"]
        x0, y0 = coordinates["x0"], coordinates["y0"]
        text = item["text"]
        if (table_state["last_y"] is None
            or (table_state["last_x"] is not None and x0 < table_state["last_x"])):  # New row
            if table_state["current_row"]:
                table_state["current_table"].append(table_state["current_row"])
            table_state["current_row"] = ['']
            table_state["last_y"] = y0
            table_state["last_x"] = x0
            if table_state["table_metadata"] is None:
                table_state["table_metadata"] = item["metadata"]
        if (table_state["last_x"] is not None
            and abs(table_state["last_x"] - x0) <= self.config.table_column_threshold):  # pylint: disable=C0301
            table_state["current_row"][-1] += ' ' + text  # Merge with previous cell
        else:
            table_state["current_row"].append(text)  # New cell
            table_state["last_y"] = y0
            table_state["last_x"] = x0

        return table_state

    def _convert_table_to_html(self, current_table: list, table_metadata: dict):
        table_html = '<table>\n'
        for row in current_table:
            table_html += '  <tr>\n'
            for cell in row:
                table_html += f'    <td>{cell}</td>\n'
            table_html += '  </tr>\n'
        table_html += '</table>'
        return {"text": table_html, "metadata": table_metadata}

    def _extract_images(self, pdf_document, document_basename: str):
        document_name, _ = os.path.splitext(document_basename)
        logger.debug(f"Extract images from {document_name}")
        self._process_images(pdf_document, document_name)
        self._process_vector_graphics(pdf_document, document_name)

    def _process_images(self, pdf_document, document_name: str):
        global_img_index = 1
        for page_num in tqdm(range(len(pdf_document)), desc="Processing pages"):
            page = pdf_document.load_page(page_num)
            image_list = self._get_image_list(page)
            for img in image_list:
                image_name = (
                    f"Image-{global_img_index}"
                    f"_Page-{page_num + 1}"
                    f"_Doc-{document_name}")
                self._save_image(img, pdf_document, image_name)
                global_img_index += 1

    def _get_image_list(self, page):
        image_list = page.get_images(full=True)
        if self.config.skip_header_images > 0:
            image_list = image_list[self.config.skip_header_images:]
        if self.config.skip_footer_images > 0:
            image_list = image_list[:-self.config.skip_footer_images]  # pylint: disable=E1130
        return image_list

    def _save_image(self, img: dict, pdf_document, image_name: str):
        xref = img[0]
        base_image = pdf_document.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_name += f".{image_ext}"
        image_path = os.path.join(self.config.image_output_folder, image_name)
        with open(image_path, "wb") as img_file:
            img_file.write(image_bytes)

    def _process_vector_graphics(self, pdf_document, document_name: str):
        global_img_index = 1
        for page_num in tqdm(range(len(pdf_document)), desc="Processing pages"):
            drawings = self._extract_drawings_from_page(pdf_document, page_num)
            valid_rectangles = self._find_valid_rectangles(drawings)
            global_img_index = self._save_rectangles_as_png({
                "doc": pdf_document,
                "doc_name": document_name,
                "rects": valid_rectangles,
                "img_index": global_img_index,
                "page_num": page_num
            })

    def _extract_drawings_from_page(self, doc, page_num: int):
        page = doc[page_num]
        paths = page.get_drawings()
        elements = []
        for path in paths:
            if "rect" in path:
                rect = fitz.Rect(path["rect"])
                elements.append(rect)
            elif "l" in path:
                point1, point2 = path["l"]
                elements.extend([point1, point2])
            elif "qu" in path:
                points = path["qu"]
                elements.extend(points)
            elif "m" in path:
                point = path["m"]
                elements.append(point)
            elif "c" in path:
                points = path["c"]
                elements.extend(points)
            else:
                logger.warning("Element not considered")
        return elements

    def _is_within(self, point, rect):
        return rect.contains(fitz.Point(point))

    def _is_contained(self, inner, outer):
        return outer.contains(inner)

    def _find_valid_rectangles(self, elements: list):
        valid_rectangles = []
        for rect in [e for e in elements if isinstance(e, fitz.Rect)]:
            contains_elements = False
            contained_by_other = False
            for elem in elements:
                if elem == rect:
                    continue
                if isinstance(elem, fitz.Rect):
                    if rect.contains(elem):
                        contains_elements = True
                elif self._is_within(elem, rect):
                    contains_elements = True
            for other_rect in [e for e in elements if isinstance(e, fitz.Rect)]:
                if rect != other_rect and self._is_contained(rect, other_rect):
                    contained_by_other = True
                    break
            if contains_elements and not contained_by_other:
                valid_rectangles.append(rect)
        return valid_rectangles

    def _save_rectangles_as_png(self, params: dict):
        output_dir = self.config.image_output_folder
        os.makedirs(output_dir, exist_ok=True)
        for r in params["rects"]:
            spage = fitz.open()
            spage.new_page(width=r.width, height=r.height)
            spage[0].show_pdf_page(spage[0].rect, params["doc"], params["page_num"], clip=r)
            pix = spage[0].get_pixmap(matrix=fitz.Matrix(2, 2))
            draw_name = (
                f"Draw-{params['img_index']}"
                f"_Page-{params['page_num']+1}"
                f"_Doc-{params['doc_name']}")
            png_file_path = os.path.join(output_dir, f"{draw_name}.png")
            pix.save(png_file_path)
            logger.debug(f"PNG image saved to {png_file_path}")
            params["img_index"] += 1
        return params["img_index"]
