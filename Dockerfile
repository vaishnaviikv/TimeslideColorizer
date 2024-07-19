# Stage 1: Build with Python 3.7
FROM python:3.7-slim as builder

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip and attempt to install pynvx with error handling
RUN pip install --upgrade pip && \
    pip install pynvx==1.0.0 || echo "Failed to install pynvx. Check compatibility or availability."

# # Stage 2: Setup with Python 3.10
# FROM python:3.10 as final

# # Set the working directory in the container
# WORKDIR /app

# # Copy everything from the builder stage
# COPY --from=builder /app /app

# # Install necessary system libraries for PyQt6 and ffmpeg, including build tools
# RUN apt-get update && apt-get install -y \
#     libgl1-mesa-glx \
#     libegl1-mesa \
#     libegl1 \
#     libxrandr2 \
#     libxss1 \
#     libxcursor1 \
#     libxcomposite1 \
#     libasound2 \
#     libxi6 \
#     libxtst6 \
#     ffmpeg \
#     qtbase5-dev \
#     qt5-qmake \
#     qtbase5-dev-tools \
#     qttools5-dev-tools \
#     python3-dev \
#     build-essential

# Log Qt version and qmake path
# RUN qmake --version

# Stage 3: Setup with Python 3.9
FROM python:3.9 as final1

# Set the working directory in the container
WORKDIR /app

# Copy everything from the builder stage
COPY --from=builder /app /app

# Install necessary system libraries for Qt and other dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libegl1-mesa \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    ffmpeg \
    libxcb1 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-randr0 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    xcb-proto \
    libxcb-util1 \
    qt5-gtk-platformtheme \
    libqt5x11extras5 \
    qt5dxcb-plugin \
    --no-install-recommends

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || echo "Some packages in requirements.txt failed to install."
RUN pip install PySide6
RUN pip install fastai==1.0.61 --no-deps
RUN pip install opencv-python
RUN pip install ffmpeg-python
RUN pip install yt-dlp
RUN pip install ipython
RUN pip install validators
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu102
RUN pip install PyYAML

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME TimeSlide

# Run timeslide.py when the container launches
CMD ["python", "timeslide.py"]
