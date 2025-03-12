# SEM-Image-Scalebar-Reset
![logo](./Grok-sem-scalebar-reset-crop.jpg)

This program assists in cropping the bottom information bar of the SEM image and adds a new scale bar.

## Usage

[//]: # ([![Streamlit App]&#40;https://static.streamlit.io/badges/streamlit_badge_black_white.svg&#41;]&#40;https://jameschung821-sem-image-scalebar-rese-sem-scalebar-reset-stt8wz.streamlit.app/&#41;)
<a href="https://jameschung821-sem-image-scalebar-rese-sem-scalebar-reset-stt8wz.streamlit.app/" target="_blank">
<img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Streamlit App">
</a>

![alt text](./sem_image_scalebar_reset_entry.png)

### 1. Define the user input
### 2. Upload the SEM image
### 3. Update the pixel size in nm if needed

<p align="center">
  <img src="./pixel_size.png" alt="Size Limit CLI" width="300">
</p>

Known distance in nm / Distance in pixels = Pixel size (nm/pixel)

e.g. 4000 nm (4 um) / 711 pixels = 5.626 nm/pixel, and then set the pixel size to 5.63

### 4. Download the cropped image with a new scale bar

![alt text](./image_crop.png)