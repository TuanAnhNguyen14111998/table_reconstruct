import os
import cv2
import sys
sys.path.insert(0, "./")

from lib.ocr.reader import Reader


if __name__ == "__main__":
    image_path = "./datasets/clean_data/thalas_0.jpg"
    visualize_dir = "./visualize_dir"
    if not os.path.isdir(visualize_dir):
        os.mkdir(visualize_dir)

    reader_ocr = Reader(vis_dir=visualize_dir)
    image = cv2.imread(image_path)
    reader_ocr(image=image)
