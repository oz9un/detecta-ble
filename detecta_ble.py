# Author: Özgün Kültekin
# email: ozgunkultekin@gmail.com
# Tubitak Image Color Diff - Histogram Extraction

import sys
import cv2
import copy
import os
import numpy as np
import argparse


def hex_histogram(img_name):
    # read original image in full color
    img = cv2.imread(img_name)
    
    all_pixel_hex = []
    hex_histogram = {}
    height = len(img[:,0,0])
    width = len(img[0,:,0])

    for h in range(height):
        for w in range(width):
            red_hex = str(hex(img[h,w,0])[2:]) if len(str(hex(img[h,w,0])[2:])) == 2 else '0'+str(hex(img[h,w,0])[2:])
            green_hex =  str(hex(img[h,w,1])[2:]) if len(str(hex(img[h,w,1])[2:])) == 2 else '0'+str(hex(img[h,w,1])[2:])
            blue_hex = str(hex(img[h,w,2])[2:]) if len(str(hex(img[h,w,2])[2:])) == 2 else '0'+str(hex(img[h,w,2])[2:])
            pixel_hex = red_hex + green_hex + blue_hex

            all_pixel_hex.append(pixel_hex)
            
            if pixel_hex in hex_histogram.keys():
                hex_histogram[pixel_hex] = hex_histogram[pixel_hex] + 1
            else:
                hex_histogram[pixel_hex] = 1

    
    return hex_histogram, img.shape, all_pixel_hex


def create_matrix(img):
    _,imgShape,oneDmatrix = hex_histogram(img)
    twoDmatrix = [[0]*imgShape[1] for i in range(imgShape[0])]

    for row in range(len(twoDmatrix)):
        for column in range(len(twoDmatrix[0])):
            twoDmatrix[row][column] = oneDmatrix[column + row*len(twoDmatrix[0])]

    return twoDmatrix


def compare_matrices(matrix1, matrix2, target_folder, threshold):
    # Edited for additional info:
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    info_file = open(target_folder + "/additional_info.txt", "w")

    difference_matrix = [[0]*len(matrix1[0]) for i in range(len(matrix1))]

    for row in range(len(difference_matrix)):
        for column in range(len(difference_matrix[0])):
            if matrix1[row][column] != matrix2[row][column]:
                col1 = row
                col2 = column
                col3 = matrix1[row][column]
                col4 = matrix2[row][column]
                col5 = hex_difference(matrix1[row][column], matrix2[row][column])
                
                info_file.write(str(col1) + " " + str(col2) + " " + str(col3) + " " + str(col4) + " " + str(col5) + "\n")
                
                if col5 > threshold:
                    difference_matrix[row][column] = -1

    info_file.close()
    return difference_matrix


def hex_difference(hex1, hex2):
    rgb1 = tuple(int(hex1[i:i+2], 16) for i in (0,2,4))
    rgb2 = tuple(int(hex2[i:i+2], 16) for i in (0,2,4))

    red_diff = abs((rgb2[0] - rgb1[0]) / rgb1[0]) * 100 if rgb1[0] != 0 else abs((rgb2[0] - rgb1[0]) / 1) * 100
    green_diff = abs((rgb2[1] - rgb1[1]) / rgb1[1]) * 100 if rgb1[1] != 0 else abs((rgb2[1] - rgb1[1]) / 1) * 100
    blue_diff = abs((rgb2[2] - rgb1[2]) / rgb1[2]) * 100 if rgb1[2] != 0 else abs((rgb2[2] - rgb1[2]) / 1) * 100
    total_diff = (red_diff + green_diff + blue_diff) / 3

    return total_diff


def different_boundaries(difference_matrix):
    updated_diff_matrix = copy.deepcopy(difference_matrix)
    for row in range(len(difference_matrix)):
        for column in range(len(difference_matrix[0])):
            if difference_matrix[row][column] == -1 and row*column != 0 and row < len(difference_matrix)-1 and column < len(difference_matrix[0])-1:
                if difference_matrix[row-1][column] * difference_matrix[row+1][column] * difference_matrix[row][column-1] * difference_matrix[row][column+1] == 1:
                    updated_diff_matrix[row][column] = 0


    return updated_diff_matrix


def extract_adjacents(boundaries_matrix, row, column):
    start = [row,column]
    currentList = [[row,column]]
    nextList = []

    while currentList != nextList:
        nextList = copy.deepcopy(currentList)
        for pt in currentList:
            if pt[0]>0 and pt[0]<len(boundaries_matrix)-1 and pt[1]>0 and pt[1]<len(boundaries_matrix[0])-1:
                if boundaries_matrix[pt[0]+1][pt[1]] == -1 and [pt[0]+1,pt[1]] not in currentList:
                    currentList.append([pt[0]+1,pt[1]])
                elif boundaries_matrix[pt[0]-1][pt[1]] == -1 and [pt[0]-1,pt[1]] not in currentList:
                    currentList.append([pt[0]-1,pt[1]])
                elif boundaries_matrix[pt[0]][pt[1]+1] == -1 and [pt[0],pt[1]+1] not in currentList:
                    currentList.append([pt[0],pt[1]+1])
                elif boundaries_matrix[pt[0]][pt[1]-1] == -1 and [pt[0],pt[1]-1] not in currentList:
                    currentList.append([pt[0],pt[1]-1])
                elif boundaries_matrix[pt[0]-1][pt[1]+1] == -1 and [pt[0]-1,pt[1]+1] not in currentList:
                    currentList.append([pt[0]-1,pt[1]+1])
                elif boundaries_matrix[pt[0]-1][pt[1]-1] == -1 and [pt[0]-1,pt[1]-1] not in currentList:
                    currentList.append([pt[0]-1,pt[1]-1])
                elif boundaries_matrix[pt[0]+1][pt[1]+1] == -1 and [pt[0]+1,pt[1]+1] not in currentList:
                    currentList.append([pt[0]+1,pt[1]+1])
                elif boundaries_matrix[pt[0]+1][pt[1]-1] == -1 and [pt[0]+1,pt[1]-1] not in currentList:
                    currentList.append([pt[0]+1,pt[1]-1])
                           
    return currentList


def final_boundaries(boundaries_matrix):
    boundaries = []
    all_points = []
    
    for row in range(len(boundaries_matrix)):
        for column in range(len(boundaries_matrix[0])):
            if boundaries_matrix[row][column] == -1 and [row,column] not in all_points:
                if row>0 and row<len(boundaries_matrix)-1 and column>0 and column<len(boundaries_matrix[0])-1:
                    adjacents = extract_adjacents(boundaries_matrix,row,column)
                    boundaries.append(adjacents)
                    for pt in adjacents:
                        all_points.append(pt)
    return boundaries


def draw_boundaries(boundaries_matrix, target_image):
    img = cv2.imread(target_image)
    for row in range(len(boundaries_matrix)):
        for column in range(len(boundaries_matrix[0])):
            if boundaries_matrix[row][column] == -1:
                img[row][column] = [0,0,255]
    
    cv2.imwrite(sys.argv[4], img)


def draw_on_image(boundaries_matrix, target_image):
    img = cv2.imread(target_image)
    for pixel in boundaries_matrix:
        img[pixel[0]][pixel[1]] = [0,0,255]
    
    cv2.imwrite(sys.argv[4], img)


def multi_draw_on_image(final_boundaries, target_image):
    img = cv2.imread(target_image)
    for x in final_boundaries:
        for pixel in x:
            img[pixel[0]][pixel[1]] = [0,0,255]
        
    cv2.imwrite(sys.argv[4], img)


def cropped_vectors(final_boundaries, target_folder):
    ct = 1
    for diff in final_boundaries:
        min_col = min([x[0] for x in diff])
        max_col = max([x[0] for x in diff])
        min_row = min([x[1] for x in diff])
        max_row = max([x[1] for x in diff])
        
        img = np.full((max_col+20, max_row+20, 3), 255, dtype=np.uint8)

        for pix in diff:
            img[pix[0]][pix[1]] = [0,0,255]

        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        if min_col > 20 and min_row > 20:
            new_img = img[min_col-20:max_col+20, min_row-20:max_row+20]
        else:
            new_img = img[min_col:max_col+20, min_row:max_row+20]

        target_path = target_folder + '/' + str(ct) + '.jpg'
        cv2.imwrite(target_path, new_img)
        

        ct += 1


def cropped_images(img1, img2, final_boundaries, target_folder):
    ct = 1
    img1 = cv2.imread(img1)
    img2 = cv2.imread(img2)
    for diff in final_boundaries:
        min_col = min([x[0] for x in diff])
        max_col = max([x[0] for x in diff])
        min_row = min([x[1] for x in diff])
        max_row = max([x[1] for x in diff])

        for pix in diff:
            img1[pix[0]][pix[1]] = [0,0,255]
            img2[pix[0]][pix[1]] = [0,0,255]

        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        if min_col > 20 and min_row > 20:
            new_img1 = img1[min_col-20:max_col+20, min_row-20:max_row+20]
            new_img2 = img2[min_col-20:max_col+20, min_row-20:max_row+20]
        else:
            new_img1 = img1[min_col:max_col+20, min_row:max_row+20]
            new_img2 = img2[min_col:max_col+20, min_row:max_row+20]


        target_path1 = target_folder + '/' + str(ct) + '_1.jpg'
        target_path2 = target_folder + '/' + str(ct) + '_2.jpg'

        cv2.imwrite(target_path1, new_img1)
        cv2.imwrite(target_path2, new_img2)
    
        ct += 1

    
def showdiffs(img_1, img_2, final_boundaries, target_folder):
    ct = 1
    for diff in final_boundaries:
        img1 = cv2.imread(img_1)
        img2 = cv2.imread(img_2)

        min_col = min([x[0] for x in diff])
        max_col = max([x[0] for x in diff])
        min_row = min([x[1] for x in diff])
        max_row = max([x[1] for x in diff])

        for pix in diff:
            img1[pix[0]][pix[1]] = [0,0,255]
            img2[pix[0]][pix[1]] = [0,0,255]

        final_image_top = cv2.hconcat([img1, img2])

        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        if min_col > 20 and min_row > 20:
            new_img1 = img1[min_col-20:max_col+20, min_row-20:max_row+20]
            new_img2 = img2[min_col-20:max_col+20, min_row-20:max_row+20]
        else:
            new_img1 = img1[min_col:max_col+20, min_row:max_row+20]
            new_img2 = img2[min_col:max_col+20, min_row:max_row+20]

        final_image_bot = cv2.hconcat([new_img1, new_img2])
        resized_final_image_bot = cv2.resize(final_image_bot,(len(final_image_top[0,:,0]),len(final_image_top[:,0,0])),interpolation=cv2.INTER_LINEAR)
        final_image = cv2.vconcat([final_image_top, resized_final_image_bot])

        arrow_start = (int((min_row+max_row)/2),int((min_col+max_col)/2))
        arrow_end = (int(len(resized_final_image_bot[0,:,0])/4),int(len(resized_final_image_bot[:,0,0])/2)+len(final_image_top[:,0,0]))
        color = (255, 0, 0) 
        thickness = 9
        arrow_start2 = (len(img1[0,:,0])+int((min_row+max_row)/2),int((min_col+max_col)/2))
        arrow_end2 = (int(len(resized_final_image_bot[0,:,0])*3/4),int(len(resized_final_image_bot[:,0,0])/2)+len(final_image_top[:,0,0]))
        

        final_image = cv2.arrowedLine(final_image, arrow_start, arrow_end, color, thickness) 
        final_image = cv2.arrowedLine(final_image, arrow_start2, arrow_end2, color, thickness)  

        target_path = target_folder + '/' + str(ct) + '.jpg'
        cv2.imwrite(target_path, final_image)
    
        ct += 1


def illuminaton(image):
    img = cv2.imread(image)
     
    # convert image to LAB color model:
    lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_img)

    # apply CLAHE to l_channel:
    # clipLimit = Threshold for contrast limiting. 
    # tileGridSize = Size of grid for histogram equalization. Input image will be divided into equally sized rectangular tiles. tileGridSize defines the number of tiles in row and column. 
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l_channel)    

    # merge cl & a_channel & b_channel
    merged_image = cv2.merge((cl, a_channel, b_channel))

    # final RGB image:
    final = cv2.cvtColor(merged_image, cv2.COLOR_LAB2BGR)


if __name__ == '__main__':
    
    # Get user parameters:
    parser = argparse.ArgumentParser()
    parser.add_argument("-img1", "--image_1", required=True, help="Input Image 1")
    parser.add_argument("-img2", "--image_2", required=True, help="Input Image 2")
    parser.add_argument("-o", '--output_folder', required=True, help="Set output folder's name")
    parser.add_argument("-t", '--threshold', default=0, help="Set threshold for deciding on differences.")

    args = vars(parser.parse_args())

    img1 = args["image_1"]
    img2 = args["image_2"]
    output_folder = args["output_folder"]

    matrix1 = create_matrix(img1)    
    matrix2 = create_matrix(img2)

    matrix_comparison = compare_matrices(matrix1, matrix2, output_folder, threshold=int(args["threshold"]))
    boundary_difference = different_boundaries(matrix_comparison)

    boundaries = final_boundaries(boundary_difference)
    cropped_images(img1, img2, boundaries, output_folder)
    showdiffs(img1, img2, boundaries, output_folder)
