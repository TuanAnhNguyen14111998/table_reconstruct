import os 
import cv2

from lib.utils.visualize_utils import draw_ocr_box_txt

from .reg.vietocr.vietocr_infer import VietOCR
from .det.db_paddle.infer import PaddleTextDetector

class Reader:
    def __init__(self, 
                det_name='DB', 
                det_config_path='config/ocr/ocr_det_db.yml',
                det_use_gpu=False, 
                reg_name='seq2seq', 
                reg_config_path='config/ocr/ocr_reg_seq2seq.yml',
                reg_use_gpu=False,
                vis_dir=None):

        if det_name == "DB":
            self.detect_model = PaddleTextDetector(config_path=det_config_path, use_gpu=det_use_gpu) 
        else:
            raise NotImplementedError("Model {} not implemented".format(det_name))

        if reg_name == 'seq2seq':
            self.recognize_model = VietOCR(config_path=reg_config_path, use_gpu=reg_use_gpu)
        else:
            raise NotImplementedError("Model {} not implemented".format(reg_name))
        self.vis_dir = vis_dir
        
    def __call__(self, image):
        """
        Args:
            image (np.ndarray): BGR image

        Returns:
            list: ocr result - list of (polygon box, text, prob),
                    with polygon box format [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        """
        text_boxes = self.detect_model(image)
        text_result = self.recognize_model.recognize(
            image=image,
            free_list=text_boxes,                                   
        )

        if self.vis_dir is not None:
            if not os.path.exists(self.vis_dir):
                    os.mkdir(self.vis_dir)
            boxes, txts = [], []
            for item in text_result:
                box, label, prob = item 
                boxes.append(box)
                txts.append(label)
            img_visual = draw_ocr_box_txt(image, boxes, txts, font_path='test/fonts/latin.ttf')
            cv2.imwrite(os.path.join(self.vis_dir, "vis_ocr.jpg"), img_visual)

        return text_result