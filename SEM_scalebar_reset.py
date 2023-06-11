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

MODE = 'streamlit'  # 'streamlit' or 'local'
# INPUT_PATH = r"D:\Research data\SSID\202303\20230313 FIB-SEM b34 SP"
INPUT_PATH = r"D:\Research data\SSID\202305\20230524 G5 NbAlSc EDX"
OUTPUT_PATH = Path(f'{INPUT_PATH}\Output_files')
if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()    # Create an output folder to save all generated data/files


def main():
    if MODE == 'streamlit':
        streamlit_mode()
    elif MODE == 'local':
        local_mode()


def streamlit_mode():
    st.title('SEM Image Scalebar Reset')
    st.write("Upload an image file and see it displayed below:")
    st.sidebar.title('User Preference')

    show_original_image = st.sidebar.checkbox("Show original image")
    show_reset_image = st.sidebar.checkbox("Show reset image")

    # File upload
    uploaded_file = st.file_uploader("Choose an image file", type=["tif"])  # "jpg", "jpeg", "png", "tif", "tiff"

    sem_manufacturer = st.sidebar.selectbox(
        'SEM Manufacturer',
        ('Helios', 'JEOL', 'Hitachi'))  #'Zeiss', 'FEI',

    size_of_one_pixel = st.sidebar.number_input('Pixel size of the image (mm), and 0.000000000 is the default value',
                                                format='%.9f')
    st.sidebar.caption('Known distance/Distance in pixels')

    length_fraction = st.sidebar.selectbox(
        'Desired length of the scale bar as a fraction of the subplot\'s width',
        (0.25, 0.5, 0.75, 1))

    frameon = st.sidebar.checkbox("Show frame around the scalebar")

    if uploaded_file is not None:
        original_image = Image.open(uploaded_file)
        print("--------------------")
        print(original_image)
        print("--------------------")

        # Display the uploaded image
        if show_original_image:
            st.image(original_image, caption="Uploaded Image", output_format='PNG')

        # Display the uploaded image info
        dpi = original_image.info['dpi'][0]
        x_pixel = original_image.size[0]
        length = x_pixel / dpi * 25.4

        print(f'x pixels: {x_pixel}, dpi: {dpi}, length: {length}')

        img = np.array(original_image)  # Convert to numpy array because pytesseract only accepts numpy array
        print(img.shape)

        black_row_index = img.shape[0]  # Initialize the black row index

        print(img[black_row_index-10, :])   # Check the last 10 rows (pixels) of the image

        for index, black_row in enumerate(img):     # Find the first black row or white row to crop the image
            if black_row[1:5].mean() == 11822 \
                    or black_row[1:50].mean() == 255 \
                    or black_row[1:50].mean() == 46 \
                    or black_row[1:50].mean() == 257 \
                    or black_row[1:50].mean() == 0:
                black_row_index = index
                print(black_row)
                print('black row index', black_row_index)
                break

        # Crop the image and extract the text from the image at the bottom info bar
        text = pytesseract.image_to_string(
            img[black_row_index-100:], config='--psm 6').replace('\n', ' ')
        print(f'Text: {text}')

        # Search the magnification from the text
        magnification = search_magnification(sem_manufacturer, text)

        # Display the scalebar
        scalebar = ScaleBar(length/magnification/x_pixel, 'mm',
                            length_fraction=length_fraction,
                            location='lower right',
                            color='white',
                            box_color='black',
                            border_pad=0.5,
                            sep=5,
                            frameon=frameon,
                            font_properties={'size': 'small'}) \
            if size_of_one_pixel == 0 \
            else ScaleBar(size_of_one_pixel, 'mm',
                          length_fraction=length_fraction,
                          location='lower right',
                          color='white',
                          box_color='black',
                          border_pad=0.5,
                          sep=5,
                          frameon=frameon,
                          font_properties={'size': 'small'})

        # Display the reset image
        fig, ax = plt.subplots()
        ax.set_axis_off()
        # ax.axis('off')

        plt.gca().add_artist(scalebar)  # gca() stands for 'get current axis'
        plt.imshow(img[:black_row_index], cmap='gray')
        if show_reset_image:
            st.pyplot(fig)

        # Save the reset image
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


def search_magnification(sem_manufacturer, text):
    """
    Search the magnification from the text
    :param sem_manufacturer: string, the manufacturer of the SEM
    :param text: string, the text extracted from the image
    :return: int, the magnification
    """
    if sem_manufacturer == 'Helios':
        magnification_head = 0
        magnification_tail = text.find('x')-1
        for index in range(magnification_tail, 0, -1):  # Find the magnification head
            if not text[index].isdigit() and text[index] != ' ':
                magnification_head = index+1
                break
        print(magnification_head, magnification_tail)

        magnification = int(text[magnification_head:magnification_tail+1].replace(' ', ''))  # Extract the magnification
        print(magnification)
        return magnification

    elif sem_manufacturer == 'JEOL':
        magnification_head = text.find('X') if text.find('X') != -1 else text.find('x')
        magnification_tail = text.find(' ', magnification_head+2)
        print(magnification_head, magnification_tail)

        magnification = int(text[magnification_head+1:magnification_tail].replace(' ', '').replace(',', ''))  # Extract the magnification
        print(magnification)
        return magnification

    elif sem_manufacturer == 'Hitachi':
        magnification_head = text.find('x')
        magnification_tail = text.find(' ', magnification_head+2)
        print(magnification_head, magnification_tail)

        magnification = text[magnification_head+1:magnification_tail].replace(' ', '')  # Extract the magnification
        if 'k' in magnification:
            magnification = int(float(magnification[:-1]) * 1000)
        else:
            magnification = int(magnification)
        print(magnification)
        return magnification


if __name__ == '__main__':
    main()