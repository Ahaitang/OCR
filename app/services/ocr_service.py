"""
OCR Service - Local PaddleOCR with GPU acceleration
使用已下载的 PP-OCRv5 Server 模型（高精度）
"""
import numpy as np
from PIL import Image
import io
import base64
import re
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

# 设置 GPU 模式
try:
    import paddle
    if paddle.device.cuda.device_count() > 0:
        paddle.device.set_device('gpu:0')
        logger.info(f"GPU 模式已启用: {paddle.device.cuda.get_device_name(0)}")
    else:
        logger.info("GPU 不可用，使用 CPU 模式")
except Exception as e:
    logger.warning(f"Paddle 初始化失败: {e}")

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR not installed")


class OCRService:
    """本地 PaddleOCR 服务 (GPU 加速)"""

    def __init__(self):
        if PADDLEOCR_AVAILABLE:
            try:
                # PP-OCRv5 Server 模型（高精度，已下载）
                self.paddle_ocr = PaddleOCR()
                logger.info("PaddleOCR 初始化成功 (GPU 加速)")
            except Exception as e:
                logger.error(f"PaddleOCR init failed: {e}")
                self.paddle_ocr = None
        else:
            self.paddle_ocr = None

    def parse_image(self, image_data: bytes) -> Dict:
        """解析单张图片"""
        if not self.paddle_ocr:
            return {'success': False, 'error': 'PaddleOCR not available'}

        try:
            image = Image.open(io.BytesIO(image_data))
            img_array = np.array(image)

            # 调用 OCR
            result = self.paddle_ocr.ocr(img_array)

            lines = []
            for page in result:
                if page:
                    for item in page:
                        text = item[1][0]
                        confidence = round(item[1][1], 3)
                        position = item[0]
                        lines.append({
                            'text': text,
                            'confidence': confidence,
                            'position': position
                        })

            if lines:
                full_text = '\n'.join([l['text'] for l in lines])
                avg_confidence = round(np.mean([l['confidence'] for l in lines]), 3)
                return {
                    'success': True,
                    'full_text': full_text,
                    'lines': lines,
                    'avg_confidence': avg_confidence,
                    'structured_data': self.extract_structured_data(full_text),
                    'source': 'paddleocr-local-gpu'
                }
            return {'success': False, 'error': 'No text detected'}

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {'success': False, 'error': str(e)}

    def parse_medical_record(self, images: List[bytes]) -> Dict:
        """解析多张病历图片"""
        results = [self.parse_image(img) for img in images]

        success_results = [r for r in results if r.get('success')]
        failed_pages = [
            {'page': i + 1, 'error': r.get('error')}
            for i, r in enumerate(results) if not r.get('success')
        ]

        combined_text = '\n\n'.join([r['full_text'] for r in success_results])

        # 合并结构化数据
        all_struct_data = {}
        for r in success_results:
            if r.get('structured_data'):
                all_struct_data.update(r['structured_data'])

        return {
            'success': len(success_results) > 0,
            'combined_text': combined_text,
            'page_results': results,
            'failed_pages': failed_pages,
            'structured_data': all_struct_data,
            'total_pages': len(images),
            'success_pages': len(success_results),
            'source': 'paddleocr-local-gpu'
        }

    def extract_structured_data(self, text: str) -> Dict:
        """从文本中提取结构化信息"""
        data = {}
        patterns = {
            'patient_name': r'姓\s*名[:：]\s*(\S+)',
            'patient_age': r'年\s*龄[:：]\s*(\d+)',
            'patient_gender': r'性\s*别[:：]\s*(男|女)',
            'diagnosis': r'(诊断|初步诊断)[:：]\s*(.+?)(\n|$)',
            'record_date': r'(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
            'hospital': r'(医院|医疗机构)[:：]\s*(\S+)',
            'department': r'科\s*室[:：]\s*(\S+)',
            'doctor': r'医\s*生[:：]\s*(\S+)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                data[key] = match.group(1).strip()
        return data


ocr_service = OCRService()


def parse_images(images: List[str], prompt: str = None) -> Dict:
    """解析 base64 图片列表"""
    decoded = []
    for img in images:
        try:
            decoded.append(base64.b64decode(img) if isinstance(img, str) else img)
        except:
            continue

    if not decoded:
        return {'success': False, 'error': 'No valid images'}

    return ocr_service.parse_medical_record(decoded)