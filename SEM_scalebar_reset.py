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
import time

MODE = 'streamlit'  # 'streamlit' or 'local'
INPUT_PATH = r"C:\Users\user\Downloads\G5 Scalebar update"
# INPUT_PATH = r"D:\Research data\SSID\202305\20230524 G5 NbAlSc EDX"
OUTPUT_PATH = Path(f'{INPUT_PATH}\Output_files')
SEM_MANUFACTURER = 'Helios'  # 'Helios', 'JEOL', 'Hitachi'
LENGTH_FRACTION = 0.25  # 0.25, 0.5, 0.75, 1.0 Desired length of the scale bar in fraction of the image width
SIZE_OF_ONE_PIXEL = 0.00  # 0.00 is the default value
SHOW_FRAMEON = True  # True or False
SCALEBAR_LOCATION = 'lower right'  # 'lower right', 'lower left', 'upper right', 'upper left'


def main():
    if MODE == 'streamlit':
        streamlit_mode()
    elif MODE == 'local':
        if not OUTPUT_PATH.exists():
            OUTPUT_PATH.mkdir()  # Create an output folder to save all generated data/files
        local_mode()


def streamlit_mode():
    st.title('SEM Image Scalebar Reset')
    st.info('Confirm SEM Manufacturer', icon="ℹ️")
    st.write("Upload an image file and see it displayed below:")
    st.sidebar.title('User Preference')

    show_original_image = st.sidebar.checkbox("Show original image")
    show_reset_image = st.sidebar.checkbox("Show reset image")

    # File upload
    uploaded_file = st.file_uploader("Choose an image file", type=["tif"])  # "jpg", "jpeg", "png", "tif", "tiff"

    sem_manufacturer = st.sidebar.selectbox(
        'SEM Manufacturer',
        ('Helios', 'JEOL', 'Hitachi'))  # 'Zeiss', 'FEI',

    size_of_one_pixel = st.sidebar.number_input('Pixel size of the image (nm/pixel), and 0.00 is the default value',
                                                format='%.3f')
    st.sidebar.markdown('<div style="margin-top: -15px; font-size: small; color: gray;"> '
                        'Known distance (nm) / Distance in pixels</div>', unsafe_allow_html=True)
    # st.sidebar.caption('Known distance (nm) / Distance in pixels')
    if sem_manufacturer == 'Helios':
        st.sidebar.markdown('<div style="margin-top: -15px; font-size: small; color: gray;"> '
                            'X100000: 1.35; X150000: 0.91; X200000: 0.34 </div>', unsafe_allow_html=True)
        # st.sidebar.caption('X100000: 1.35; X150000: 0.91; X200000: 0.34')
    if sem_manufacturer == 'JEOL':
        st.sidebar.markdown('<div style="margin-top: -15px; font-size: small; color: gray;"> '
                            'X10000: 4.65; X20000: 2.325; X50000: 0.92; X100000: 0.465 </div>', unsafe_allow_html=True)
        # st.sidebar.caption('X10000: 4.65; X20000: 2.325; X50000: 0.92; X100000: 0.465')


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

        print(img[black_row_index - 10, :])  # Check the last 10 rows (pixels) of the image
        # Because the bar info is at the bottom of the image,
        # we find the first row of bar info from index = -150 to the end to crop the image
        for index, black_row in enumerate(img[-150:]):
            if black_row[1:5].mean() == 11822 \
                    or black_row[1:50].mean() == 255 \
                    or black_row[1:50].mean() == 46 \
                    or black_row[1:50].mean() == 257 \
                    or black_row[1:50].mean() == 0 \
                    or black_row[1:50].mean() == 1:
                # The real black row index is the index of the black row plus the index of the last 150 rows
                black_row_index = index + img.shape[0] - 150
                print('black row index', black_row_index)
                print(f'black row: {black_row}')
                break

        # Crop the image and extract the text from the image at the bottom info bar
        text = pytesseract.image_to_string(
            img[black_row_index - 100:], config='--psm 6').replace('\n', ' ')   # --psm 11 may be better
        print(f'Text: {text}')

        # Search the magnification from the text
        magnification = 0
        if SIZE_OF_ONE_PIXEL == 0:
            try:
                magnification = search_magnification(sem_manufacturer, text)
            except ValueError:
                st.error('''The magnification is not found. Please check the SEM manufacturer or :red[ENTER] a magnification.''')
                magnification = st.sidebar.number_input('Magnification', format='%f')

        length_fraction = st.sidebar.selectbox(
            'Desired length of the scale bar as a fraction of the subplot\'s width',
            (0.25, 0.5, 0.75, 1))

        hide_frameon = not st.sidebar.checkbox("Hide frame around the scalebar")

        scalebar_location = st.sidebar.selectbox(
            'Scalebar Location',
            ('lower right', 'lower left', 'upper right', 'upper left'))

        # Display the scalebar
        scalebar = ScaleBar(length / magnification / x_pixel, 'mm',
                            length_fraction=length_fraction,
                            location=scalebar_location,
                            color='white',
                            box_color='black',
                            border_pad=0.5,
                            sep=5,
                            frameon=hide_frameon,
                            font_properties={'size': 'small'}) \
            if size_of_one_pixel == 0 \
            else ScaleBar(size_of_one_pixel, 'nm',
                          length_fraction=length_fraction,
                          location=scalebar_location,
                          color='white',
                          box_color='black',
                          border_pad=0.5,
                          sep=5,
                          frameon=hide_frameon,
                          font_properties={'size': 'small'})

        # Display the reset image
        fig, ax = plt.subplots()
        ax.set_axis_off()

        plt.gca().add_artist(scalebar)  # gca() stands for 'get current axis'
        plt.imshow(img[:black_row_index], cmap='gray')
        if show_reset_image:
            st.pyplot(fig)

        # Save the reset image
        fig = io.BytesIO()  # Create a new in-memory file object for the plot
        plt.savefig(fig, format='png', dpi=600, bbox_inches='tight', pad_inches=0)
        btn = st.download_button(
            label="Download image with 600 dpi",
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
        print('='*50)
        print(index, filename)
        print('-'*50)

        if '.tif' in filename:
            original_image = Image.open(INPUT_PATH + '/' + filename)

            # Display the image info
            dpi = original_image.info['dpi'][0]
            x_pixel = original_image.size[0]
            length = x_pixel / dpi * 25.4
            print(f'x pixels: {x_pixel}, dpi: {dpi}, length: {length}')

            img = np.array(original_image)  # Convert to numpy array because pytesseract only accepts numpy array
            print(img.shape)

            black_row_index = img.shape[0]  # Initialize the black row index
            # Because the bar info is at the bottom of the image,
            # we find the first row of bar info from index = -150 to the end to crop the image
            for index, black_row in enumerate(img[-150:]):
                if black_row[1:5].mean() == 11822 \
                        or black_row[1:50].mean() == 255 \
                        or black_row[1:50].mean() == 46 \
                        or black_row[1:50].mean() == 257 \
                        or black_row[1:50].mean() == 0 \
                        or black_row[1:50].mean() == 1:
                    # The real black row index is the index of the black row plus the index of the last 150 rows
                    black_row_index = index + img.shape[0] - 150
                    print(f'black row index: {black_row_index}')
                    print(f'black row: {black_row}')
                    break

            text = pytesseract.image_to_string(img[black_row_index - 100:], config='--psm 6').replace('\n', ' ')
            print(f'Text: {text}')

            # Search the magnification from the text
            magnification = search_magnification(SEM_MANUFACTURER, text)

            scalebar = ScaleBar(length / magnification / x_pixel, 'mm',
                                length_fraction=LENGTH_FRACTION,
                                location=SCALEBAR_LOCATION,
                                color='white',
                                box_color='black',
                                border_pad=0.5,
                                sep=5,
                                frameon=SHOW_FRAMEON,
                                font_properties={'size': 'small'}) \
                if SIZE_OF_ONE_PIXEL == 0 \
                else ScaleBar(SIZE_OF_ONE_PIXEL, 'nm',
                              length_fraction=LENGTH_FRACTION,
                              location=SCALEBAR_LOCATION,
                              color='white',
                              box_color='black',
                              border_pad=0.5,
                              sep=5,
                              frameon=SHOW_FRAMEON,
                              font_properties={'size': 'small'})
            plt.xticks([])
            plt.yticks([])
            plt.gca().add_artist(scalebar)
            plt.imshow(img[:black_row_index], cmap='gray')
            plt.savefig("{}/{}.png".format(OUTPUT_PATH, f'{filename[:-4]}_scalebar'),
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
        magnification_tail = text.find('x') - 1
        for index in range(magnification_tail, 0, -1):  # Find the magnification head
            if not text[index].isdigit() and text[index] != ' ':
                magnification_head = index + 1
                break
        print(f'magnification_head: {magnification_head}, magnification_tail: {magnification_tail}')

        magnification = int(
            text[magnification_head:magnification_tail + 1].replace(' ', ''))  # Extract the magnification

        print(f'magnification: {magnification}')
        return magnification

    elif sem_manufacturer == 'JEOL':
        magnification_head = text.find('X') if text.find('X') != -1 \
            else text.find('x')
        magnification_tail = text.find(' ', magnification_head + 2)
        print(f'magnification_head: {magnification_head}, magnification_tail: {magnification_tail}')

        magnification = int(text[magnification_head + 1:magnification_tail]
                            .replace(' ', '').replace(',', ''))  # Extract the magnification
        print(f'magnification: {magnification}')
        return magnification

    elif sem_manufacturer == 'Hitachi':
        magnification_head = text.find('x')
        magnification_tail = text.find(' ', magnification_head + 2)
        print(f'magnification_head: {magnification_head}, magnification_tail: {magnification_tail}')

        magnification = text[magnification_head + 1:magnification_tail].replace(' ', '')  # Extract the magnification
        if 'k' in magnification:
            magnification = int(float(magnification[:-1]) * 1000)
        else:
            magnification = int(magnification)
        print(f'magnification: {magnification}')
        return magnification


if __name__ == '__main__':
    main()
