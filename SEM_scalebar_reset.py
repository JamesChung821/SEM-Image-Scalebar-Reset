from PIL import Image, ImageEnhance
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
WIDTH_FRACTION = 0.03  # 0.03 is the default value
FONT_SIZE = 'large'  # 'small', 'medium', 'large', 'x-large', 'xx-large'
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
    st.info('Confirm the SEM Manufacturer', icon="ℹ️")
    st.write("Upload an image file and see it displayed below:")
    st.sidebar.title('User Preference')

    show_original_image = st.sidebar.checkbox("Show original image")
    show_reset_image = st.sidebar.checkbox("Show reset image", value=True)

    # File upload
    uploaded_file = st.file_uploader("Choose an image file", type=["tif"])  # "jpg", "jpeg", "png", "tif", "tiff"

    sem_manufacturer = st.sidebar.selectbox(
        'SEM Manufacturer',
        ('Helios', 'JEOL', 'Hitachi'))  # 'Zeiss', 'FEI',

    size_of_one_pixel = st.sidebar.number_input('Pixel size (nm/pixel), 0.00 is the default value',
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

        print(img[black_row_index - 20, :])  # Check the last 10 rows (pixels) of the image
        # Because the bar info is at the bottom of the image,
        # we find the first row of bar info from index = -150 to the end to crop the image
        for index, black_row in enumerate(img[-150:]):
            # if black_row[1:5].mean() == 11822 \
            #         or black_row[1:50].mean() == 255 \
            #         or black_row[1:50].mean() == 46 \
            #         or black_row[1:50].mean() == 257 \
            #         or black_row[1:50].mean() == 0 \
            #         or black_row[1:50].mean() == 1:
            if black_row[1:50].mean() == black_row[1:10].mean() and black_row[1].mean() != 255:
                # The real black row index is the index of the black row plus the index of the last 150 rows
                black_row_index = index + img.shape[0] - 150
                print('black row index', black_row_index)
                print(f'black row: {black_row[1:5]}')
                print(black_row[1:50].mean())
                break

        # Crop the image and extract the text from the image at the bottom info bar
        print('='*50)
        text = pytesseract.image_to_string(
            img[black_row_index + (img.shape[0]-black_row_index)//2 - 2:], config='--psm 6').replace('\n', ' ')   # --psm 11 may be better
        print(f'Text: {text}')
        print('='*50)

        # Search the magnification from the text
        magnification = 0
        if size_of_one_pixel == 0:
            # magnification = 0
            try:
                magnification = search_magnification(sem_manufacturer, text)
            except ValueError:
                magnification = st.sidebar.number_input('Magnification', format='%f')
                if magnification == 0:
                    st.error('''The magnification is not found. Please check the SEM manufacturer or :red[ENTER] a magnification.''')

        # Adjust the brightness and contrast of the image
        print(f'original_image.mode: {original_image.mode}')
        if original_image.mode not in ["RGB", "L"]:
            original_image = original_image.convert("L")
        # sharpness = st.sidebar.slider('Sharpness, 1.00 is the default value', -10.0, 10.0, 1.0)
        # original_image = ImageEnhance.Sharpness(original_image).enhance(sharpness)      # Enhance the sharpness of the image
        # brightness = st.sidebar.slider('Brightness, 1.00 is the default value', 0.0, 3.0, 1.0)
        # original_image = ImageEnhance.Brightness(original_image).enhance(brightness)    # Enhance the brightness of the image
        # contrast = st.sidebar.slider('Contrast, 1.00 is the default value', -10.0, 10.0, 1.0)
        # original_image = ImageEnhance.Contrast(original_image).enhance(contrast)        # Enhance the contrast of the image
        # img = np.array(original_image)

        # Add this to your streamlit_mode function
        auto_adjust = st.sidebar.checkbox("Auto adjust brightness and contrast")

        # Replace your brightness and contrast sliders with conditional ones
        if auto_adjust:
            original_image = auto_adjust_brightness_contrast(original_image)
        else:
            brightness = st.sidebar.slider('Brightness', 0.0, 3.0, 1.0)
            original_image = ImageEnhance.Brightness(original_image).enhance(brightness)
            contrast = st.sidebar.slider('Contrast', 0.0, 3.0, 1.0)
            original_image = ImageEnhance.Contrast(original_image).enhance(contrast)# Convert to numpy array to plot the image
        img = np.array(original_image)

        hide_frameon = not st.sidebar.checkbox("Hide frame around the scalebar")

        length_fraction = st.sidebar.selectbox('Scale bar length fraction', (0.25, 0.5, 0.75, 1))

        scalebar_location = st.sidebar.selectbox(
            'Scalebar Location',
            ('lower right', 'lower left', 'upper right', 'upper left'))

        width_fraction = st.sidebar.number_input('Scalebar width fraction, 0.03 is the default value', value=0.03)
        font_size = st.sidebar.selectbox('Font size', ('small', 'medium', 'large', 'x-large', 'xx-large'), index=3)
        # white and black
        scalebar_color = st.sidebar.selectbox('Scalebar color', ('white', 'black'), index=0)
        box_color = 'black' if scalebar_color == 'white' else 'white'

        # Display the scalebar
        scalebar = ScaleBar(length / magnification / x_pixel, 'mm',
                            length_fraction=length_fraction,
                            width_fraction=width_fraction,
                            location=scalebar_location,
                            color=scalebar_color,
                            box_color=box_color,
                            border_pad=0.5,
                            sep=5,
                            frameon=hide_frameon,
                            font_properties={'size': font_size}) \
            if size_of_one_pixel == 0 \
            else ScaleBar(size_of_one_pixel, 'nm',
                          length_fraction=length_fraction,
                          width_fraction=width_fraction,
                          location=scalebar_location,
                          color=scalebar_color,
                          box_color=box_color,
                          border_pad=0.5,
                          sep=5,
                          frameon=hide_frameon,
                          font_properties={'size': font_size})    # FontProperties: https://matplotlib.org/stable/api/font_manager_api.html#matplotlib.font_manager.FontProperties

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
                # if black_row[1:5].mean() == 11822 \
                #         or black_row[1:50].mean() == 255 \
                #         or black_row[1:50].mean() == 46 \
                #         or black_row[1:50].mean() == 257 \
                #         or black_row[1:50].mean() == 0 \
                #         or black_row[1:50].mean() == 1:
                if black_row[1:50].mean() == black_row[1].mean() and black_row[1].mean() != 255:
                    # The real black row index is the index of the black row plus the index of the last 150 rows
                    black_row_index = index + img.shape[0] - 150
                    print(f'black row index: {black_row_index}')
                    print(f'black row: {black_row[1:50]}')
                    break

            text = pytesseract.image_to_string(img[black_row_index - 100:], config='--psm 6').replace('\n', ' ')
            print(f'Text: {text}')

            # Search the magnification from the text
            magnification = search_magnification(SEM_MANUFACTURER, text)

            scalebar = ScaleBar(length / magnification / x_pixel, 'mm',
                                length_fraction=LENGTH_FRACTION,
                                width_fraction=WIDTH_FRACTION,
                                location=SCALEBAR_LOCATION,
                                color='white',
                                box_color='black',
                                border_pad=0.5,
                                sep=5,
                                frameon=SHOW_FRAMEON,
                                font_properties={'size': FONT_SIZE}) \
                if SIZE_OF_ONE_PIXEL == 0 \
                else ScaleBar(SIZE_OF_ONE_PIXEL, 'nm',
                              length_fraction=LENGTH_FRACTION,
                              width_fraction=WIDTH_FRACTION,
                              location=SCALEBAR_LOCATION,
                              color='white',
                              box_color='black',
                              border_pad=0.5,
                              sep=5,
                              frameon=SHOW_FRAMEON,
                              font_properties={'size': FONT_SIZE})
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
        magnification_tail = text.rfind('x') - 1    # Find the magnification tail from the last 'x'
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


def auto_adjust_brightness_contrast(image):
    """
    Automatically adjust brightness and contrast of an image
    using histogram equalization
    """
    # Convert PIL image to numpy array
    img_array = np.array(image)

    # Check if grayscale or convert to grayscale
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        gray_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray_img = img_array

    # Get statistics of original image
    orig_mean = np.mean(gray_img)
    orig_std = np.std(gray_img)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    adjusted = clahe.apply(gray_img.astype(np.uint8))

    # Calculate effective brightness and contrast
    adjusted_mean = np.mean(adjusted)
    adjusted_std = np.std(adjusted)

    # Approximate brightness and contrast factors
    effective_brightness = adjusted_mean / orig_mean if orig_mean > 0 else 1.0
    effective_contrast = adjusted_std / orig_std if orig_std > 0 else 1.0

    st.sidebar.info(f"Auto adjustment applied with approximate values:"
                    f"\n- Brightness: {effective_brightness:.2f}"
                    f"\n- Contrast: {effective_contrast:.2f}")

    # Histogram equalization is a little too strong, so we'll tone it down a bit
    original_image = ImageEnhance.Brightness(image).enhance(effective_brightness)    # Enhance the brightness of the image
    original_image = ImageEnhance.Contrast(original_image).enhance(effective_contrast)        # Enhance the contrast of the image

    # Convert back to PIL image
    # return Image.fromarray(adjusted)
    return original_image

if __name__ == '__main__':
    main()
