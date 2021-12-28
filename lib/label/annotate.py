import os
import glob
import json
import xmltodict
import cv2
import pandas as pd
import sys
sys.path.insert(0, "./")

from lib.label.table_reconstruct import TableReconstructor


def get_bbx_and_text(file_xml):
    tables = []
    cells = []
    texts = []
    try:
        with open(file_xml, 'r') as f:
            data = f.read()
            obj = xmltodict.parse(data)
            json_data = json.loads(json.dumps(obj))

            for item in json_data["annotation"]["object"]:
                if item["name"] == "cell":
                    xmin = int(float(item["bndbox"]["xmin"]))
                    ymin = int(float(item["bndbox"]["ymin"]))
                    xmax = int(float(item["bndbox"]["xmax"]))
                    ymax = int(float(item["bndbox"]["ymax"]))
                    cells.append([xmin, ymin, xmax, ymax])
                if item["name"] == "text":
                    dictionary = {}
                    dictionary["text"] = item["attributes"]["attribute"]["value"]
                    xmin = int(float(item["bndbox"]["xmin"]))
                    ymin = int(float(item["bndbox"]["ymin"]))
                    xmax = int(float(item["bndbox"]["xmax"]))
                    ymax = int(float(item["bndbox"]["ymax"]))
                    dictionary["bndbox"] = [xmin, ymin, xmax, ymax]

                    texts.append(dictionary)
                if item["name"] == "table":
                    xmin = int(float(item["bndbox"]["xmin"]))
                    ymin = int(float(item["bndbox"]["ymin"]))
                    xmax = int(float(item["bndbox"]["xmax"]))
                    ymax = int(float(item["bndbox"]["ymax"]))
                    tables.append([xmin, ymin, xmax, ymax])
    except:
        return tables, cells, texts

    return tables, cells, texts


def visualize_image(table_reconstruct, file_image):
    image = cv2.imread(file_image)
    for rows in table_reconstruct:
        for cell in rows:
            cell = list(map(int, map(int, cell.split(","))))
            cv2.rectangle(image, (cell[0], cell[1]), (cell[2], cell[3]), color=(0, 0, 255), thickness=2)
            cv2.imshow("image", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


def asign_text_to_cell(table_reconstruct, texts):
    text_reconstruct = []
    cell_reconstruct = []
    
    for rows in table_reconstruct:
        item = []
        for cell in rows:
            status_text = True
            text_cell = ""
            cell = list(map(int, map(int, cell.split(","))))
            if cell[0] == -1:
                continue
            for text_item in texts:
                text_bbx = text_item["bndbox"]
                text_content = text_item["text"]
                if (cell[0] < text_bbx[0] + 5) and (cell[1] < text_bbx[1] + 5)\
                    and (cell[2] > text_bbx[2]) and (cell[3] > text_bbx[3]):
                    if status_text:
                        text_cell = text_content
                        status_text = False
                    else:
                        text_cell += r"\n"
                        text_cell += text_content
                        status_text = False
            
            item.append(text_cell)

        if len(item) > 0:
            text_reconstruct.append(tuple(item))
            cell_reconstruct.append(tuple(cell))

    return text_reconstruct, cell_reconstruct


def create_dataframe(text_reconstruct):
    df = pd.DataFrame(text_reconstruct)
    df.columns = df.iloc[0]
    df = df[1:]

    return df


def fix_reconstruct(df):
    
    headers = ["TÊN XÉT NGHIỆM", "KẾT QUẢ", r"KHOẢNG THAM CHIẾU,\nĐƠN VỊ", r"QUY TRÌNH/\nPPXN", r"MÁY XN/\nUSER TH"]
    filter_strs = ["TÊN XÉT", "KẾT QUẢ", "KHOẢNG THAM", "QUY TRÌNH", "MÁY XN"]
    list_df = [df.filter(regex=filter_str).values.flatten().tolist() for filter_str in filter_strs]
    df = pd.DataFrame(list(zip(*list_df)),columns=headers)
    
    return df


def get_merge_cell(cells, texts, table_reconstruct):
    cell_max = 0
    current_cell = None
    for cell in cells:
        if cell[2] - cell[0] > cell_max:
            cell_max = cell[2] - cell[0]
            current_cell = ",".join(list(map(str, cell)))

    for text in texts:
        try:
            if "Tế bào máu ngoại vi bằng" in text["text"]:
                table_reconstruct.insert(1, [current_cell])
            if "ĐIỆN GIẢI ĐỒ" in text["text"]:
                table_reconstruct.insert(14, [current_cell])
        except:
            continue

    return table_reconstruct


def annotate_image(path_folder):
    for file_xml in glob.glob(path_folder):
        if os.path.isfile(file_xml.replace("xml", "jpg")):
            file_image = file_xml.replace("xml", "jpg")
        else:
            file_image = file_xml.replace("xml", "tif")
        print(file_image)
        
        tables, cells, texts = get_bbx_and_text(file_xml)
        if len(cells) > 0:
            table_reconstruct = TableReconstructor(cells=cells).process()
            table_reconstruct = get_merge_cell(cells, texts, table_reconstruct)
            # visualize_image(table_reconstruct, file_image)
            # import pdb; pdb.set_trace()
            
            text_reconstruct, cell_reconstruct = asign_text_to_cell(table_reconstruct, texts)

            df = create_dataframe(text_reconstruct)
            df = fix_reconstruct(df)

            df.to_csv("./datasets/clean_data/" + file_xml.split("/")[-1].replace("xml", "csv"), encoding='utf-8-sig', index=False)
            html_str = df.to_html().replace("\n    ", "").replace("\n  ", "").replace(">  <", "><").replace(">\n<", "><").replace("None", "")
            import shutil
            shutil.copy(file_image, "./datasets/clean_data/" + file_image.split("/")[-1])
            file = open("./datasets/clean_data/" + file_xml.split("/")[-1].replace("xml", "txt"),"w")
            file.write(html_str)
            file.close()

    return None

if __name__ == "__main__":
    path_folder = "./datasets/origin_data/*.xml"
    annotate_image(path_folder)
