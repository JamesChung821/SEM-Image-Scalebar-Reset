from PIL import Image
import cv2
import pytesseract
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
from matplotlib_scalebar.scalebar import ScaleBar
# package source: https://github.com/ppinard/matplotlib-scalebar
from pathlib import Path
import streamlit as st
# https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
import io

# INPUT_PATH = r"D:\Research data\SSID\202303\20230313 FIB-SEM b34 SP"
INPUT_PATH = r"D:\Research data\SSID\202305\20230524 G5 NbAlSc EDX"
OUTPUT_PATH = Path(f'{INPUT_PATH}\Output_files')
if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()    # Create an output folder to save all generated data/files


def main():
    streamlit_mode()
    # local_mode()

# original_image = Image.open(INPUT_PATH + r"\20230313_b34-07_MoTiCu_SP_800C30M_100000x_1.tif")
# # original_image = Image.open(INPUT_PATH + r"\20230524_b36-02_NbAlSc_SiO2Si_Pristine_200000x_1.tif")
# dpi = original_image.info['dpi'][0]
# x_pixel = original_image.size[0]
# length = x_pixel / dpi * 25.4
# print(x_pixel, dpi, length)
#
# img = np.array(original_image)  # Convert to numpy array
# print(img.shape)
#
# black_row_index = img.shape[0]  # Initialize the black row index
# for index, black_row in enumerate(img):     # Find the first black row or white row to crop the image
#     if black_row[:5].mean() == 11822 or black_row[:5].mean() == 255:
#         black_row_index = index
#         print(black_row_index)
#         break
#
# text = pytesseract.image_to_string(img)
# print(text)
#
# magnification_head = 0
# magnification_tail = text.find('x')-1
# for index in range(magnification_tail, 0, -1):  # Find the magnification head
#     if not text[index].isdigit() and text[index] != ' ':
#         magnification_head = index+1
#         break
#
# magnification = int(text[magnification_head:magnification_tail].replace(' ', ''))   # Extract the magnification
# print(magnification)
#
# fig, ax = plt.subplots()
# ax.set_axis_off()
# # plt.xticks([])
# # plt.yticks([])
# ax.imshow(img[:black_row_index], cmap='gray')
# scalebar = ScaleBar(length/magnification/x_pixel, 'mm',
#                     length_fraction=0.25,
#                     location='lower right',
#                     color='white',
#                     box_color='black',
#                     border_pad=0.5,
#                     sep=5,
#                     font_properties={'size': 'small'})
# ax.add_artist(scalebar)
# plt.savefig("{}/{}.png".format(OUTPUT_PATH, "test"), dpi=600, bbox_inches='tight', pad_inches=0)
# plt.show()


def streamlit_mode():
    st.title('SEM Image Scalebar Reset')
    st.write("Upload an image file and see it displayed below:")
    st.sidebar.title('User Preference')

    show_original_image = st.sidebar.checkbox("Show original image")
    show_reset_image = st.sidebar.checkbox("Show reset image")

    # File upload
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png", "tif"])

    sem_manufacturer = st.sidebar.selectbox(
        'SEM Manufacturer',
        ('Hitachi', 'Helios', 'JEOL'))  #'Zeiss', 'FEI',

    size_of_one_pixel = st.sidebar.number_input('Pixel size of the image (nm), and 0.00 is the default value')

    if uploaded_file is not None:
        original_image = Image.open(uploaded_file)
        print("--------------------")
        print(original_image)
        print("--------------------")

        # Display the uploaded image
        if show_original_image:
            st.image(original_image, caption="Uploaded Image", output_format='PNG')

        dpi = original_image.info['dpi'][0]
        x_pixel = original_image.size[0]
        length = x_pixel / dpi * 25.4
        print(x_pixel, dpi, length)

        img = np.array(original_image)  # Convert to numpy array because pytesseract only accepts numpy array
        print(img.shape)

        black_row_index = img.shape[0]  # Initialize the black row index

        # print(img[200, :, 0])

        for index, black_row in enumerate(img):     # Find the first black row or white row to crop the image
            if black_row[:5].mean() == 11822 or black_row[:50].mean() == 255 or black_row[:50].mean() == 46:
                black_row_index = index
                print(black_row)
                print(black_row_index)
                break

        text = pytesseract.image_to_string(
            img[black_row_index-100:], config='--psm 6').replace('\n', ' ')    # Extract the text from the image at the bottom info bar
        print(f'Text: {text}')

        magnification_head = 0
        magnification_tail = text.find('x')-1
        for index in range(magnification_tail, 0, -1):  # Find the magnification head
            if not text[index].isdigit() and text[index] != ' ':
                magnification_head = index+1
                break
        print(magnification_head, magnification_tail)

        magnification = int(text[magnification_head:magnification_tail+1].replace(' ', ''))  # Extract the magnification
        print(magnification)

        scalebar = ScaleBar(length/magnification/x_pixel, 'mm',
                            length_fraction=0.25,
                            location='lower right',
                            color='white',
                            box_color='black',
                            border_pad=0.5,
                            sep=5,
                            font_properties={'size': 'small'}) \
            if size_of_one_pixel == 0 \
            else ScaleBar(size_of_one_pixel, 'mm',
                          length_fraction=0.25,
                          location='lower right',
                          color='white',
                          box_color='black',
                          border_pad=0.5,
                          sep=5,
                          font_properties={'size': 'small'})

        fig, ax = plt.subplots()
        ax.set_axis_off()
        plt.gca().add_artist(scalebar)
        plt.imshow(img[:black_row_index], cmap='gray')
        if show_reset_image:
            st.pyplot(fig)

        fig = io.BytesIO()  # Create a new in-memory file object for the plot
        plt.savefig(fig, format='png', dpi=600, bbox_inches='tight', pad_inches=0)
        btn = st.download_button(
            label="Download image",
            data=fig,
            file_name=f'{uploaded_file.name[:-4]}_scalebar.png',
            mime="image/png"
        )

    st.button("Re-run")


def local_mode():
    files = Path(INPUT_PATH).glob(f'*.tif')
    for index, file_directory in enumerate(files):
        file = file_directory.resolve()  # Make the path absolute, resolving any symlinks
        filename = file.name
        print(index, filename)

        if '.tif' in filename and index == 0:
            original_image = Image.open(INPUT_PATH + '/' + filename)
            dpi = original_image.info['dpi'][0]
            x_pixel = original_image.size[0]
            length = x_pixel / dpi * 25.4
            print(x_pixel, dpi, length)

            img = np.array(original_image)  # Convert to numpy array
            print(img.shape)

            black_row_index = img.shape[0]  # Initialize the black row index
            for index, black_row in enumerate(img):     # Find the first black row or white row to crop the image
                if black_row[:5].mean() == 11822 or black_row[:5].mean() == 255:
                    black_row_index = index
                    print(black_row_index)
                    break

            text = pytesseract.image_to_string(img)
            print(text)

            magnification_head = 0
            magnification_tail = text.find('x')-1
            for index in range(magnification_tail, 0, -1):  # Find the magnification head
                if not text[index].isdigit() and text[index] != ' ':
                    magnification_head = index+1
                    break

            magnification = int(text[magnification_head:magnification_tail+1])
            print(magnification)

            scalebar = ScaleBar(length/magnification/x_pixel, 'mm',
                                length_fraction=0.25,
                                location='lower right',
                                color='white',
                                box_color='black',
                                border_pad=0.5,
                                sep=5,
                                font_properties={'size': 'small'})
            plt.xticks([])
            plt.yticks([])
            plt.gca().add_artist(scalebar)
            plt.imshow(img[:black_row_index], cmap='gray')
            plt.savefig("{}/{}.png".format(OUTPUT_PATH, f'reset_{filename[:-4]}'),
                        dpi=600, bbox_inches='tight', pad_inches=0)
            plt.show()
            plt.close()


if __name__ == '__main__':
    main()