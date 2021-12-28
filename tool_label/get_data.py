import glob
import shutil
import os
import glob


def get_data():
    path_zip_folder = "./datasets/zip_folder"
    if not os.path.isdir(path_zip_folder):
        os.mkdir(path_zip_folder)
    
    path_extract_folder = "./datasets/extract_folder"
    if not os.path.isdir(path_extract_folder):
        os.mkdir(path_extract_folder)

    path_clean_origin_data = "./datasets/origin_data"
    if not os.path.isdir(path_clean_origin_data):
        os.mkdir(path_clean_origin_data)
    
    path_clean_data_folder = "./datasets/clean_data"
    if not os.path.isdir(path_clean_data_folder):
        os.mkdir(path_clean_data_folder)

    # unzip data thalas
    for path_zip in glob.glob("./datasets/zip_folder/*.zip"):
        print(path_zip)
        name_fordel = os.path.basename(path_zip).split(".")[0]
        if not os.path.isdir("./datasets/extract_folder/" + str(name_fordel)):
            os.mkdir("./datasets/extract_folder/" + str(name_fordel))
        
        try:
            shutil.unpack_archive(path_zip, "./datasets/extract_folder/" + str(name_fordel))
        except:
            continue
    
    # move image to folder data
    files = []
    for r, d, f in os.walk("./datasets/extract_folder/"):
        for file in f:
            if '.tif' in file or '.jpg' in file:
                files.append(os.path.join(r, file))
    
    number = 0
    for f in files:
        file_path = f
        file_label = f.replace("JPEGImages", "Annotations").replace(".jpg", ".xml").replace(".tif", ".xml")
        if ".tif" in file_path:
            shutil.copy(file_path, "./datasets/origin_data/" + "thalas_" + str(number) + ".tif")
        if ".jpg" in file_path:
            shutil.copy(file_path, "./datasets/origin_data/" + "thalas_" + str(number) + ".jpg")
        
        shutil.copy(file_label, "./datasets/origin_data/" + "thalas_" + str(number) + ".xml")

        number += 1


if __name__ == "__main__":
    get_data()
