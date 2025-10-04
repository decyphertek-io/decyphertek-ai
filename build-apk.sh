#!/bin/bash
# File: /home/adminotaur/Documents/git/flet/decyphertek-ai/mobile-app/custom/build-apk.sh

# Set Android SDK path to match your installation
export ANDROID_HOME="$HOME/Android/Sdk"
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin"
export PATH="$PATH:$ANDROID_HOME/platform-tools"
export JAVA_HOME="/opt/android-studio-for-platform/jbr"
export PATH="$JAVA_HOME/bin:$PATH"

echo "Building Android APK for DecypherTek AI..."

# Ensure we are in the script's directory
cd "$(dirname "$0")"



# Verify Android SDK exists
if [ ! -d "$ANDROID_HOME" ]; then
    echo "ERROR: Android SDK not found at $ANDROID_HOME"
    echo "Please ensure Android SDK is installed and ANDROID_HOME is set correctly"
    exit 1
fi

echo "Using Android SDK: $ANDROID_HOME"
echo "Using Java: $JAVA_HOME"

# Clean any previous build artifacts
rm -rf mobile/build

# Force update Flutter to absolute latest version
echo "Force updating Flutter to latest version..."
flutter upgrade --force

# Use the latest Flet version (same as desktop)
echo "Installing latest Flet version..."
poetry run pip install --upgrade flet

# Create a credential-free mobile directory
mkdir -p credential_free_mobile
cp simple_mobile.py credential_free_mobile/main.py

# Remove any existing credential files from build
rm -f credential_free_mobile/*.json
rm -f credential_free_mobile/*.env
rm -f credential_free_mobile/*.key

# Build APK with credential-free app
poetry run flet build apk credential_free_mobile

echo "Build process finished. You can find the APK in the build/apk/ directory."